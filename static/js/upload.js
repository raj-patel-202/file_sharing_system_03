document.addEventListener("DOMContentLoaded", async () => {
    const uploadForm = document.getElementById("upload-form");
    const fileInput = document.getElementById("file-input");
    const filenameInput = document.getElementById("filename-input");
    const statusDiv = document.getElementById("upload-status");
    const speedDiv = document.getElementById("upload-speed");
    const progressContainer = document.getElementById("progress-bar-container");
    const progressBar = document.getElementById("progress-bar");
    
    const startBtn = document.getElementById("start-btn");
    const resumeBtn = document.getElementById("resume-btn");
    const pauseBtn = document.getElementById("pause-btn");

    const urlParams = new URLSearchParams(window.location.search);
    const targetFileId = urlParams.get('target_file');
    const resumeSessionId = urlParams.get('resume_session');
    
    let resumeSessionData = null;
    let currentSessionId = null;
    let isPaused = false;

    if (resumeSessionId) {
        try {
            const res = await fetch(`/api/uploads/${resumeSessionId}/status`);
            if (res.ok) {
                resumeSessionData = await res.json();
                statusDiv.textContent = `Ready to resume upload for ${resumeSessionData.original_filename} (${Math.round(resumeSessionData.committed_size/1024)}KB / ${Math.round(resumeSessionData.total_size/1024)}KB)`;
                document.getElementById("visibility-input").value = resumeSessionData.visibility;
            }
        } catch(e) {}
    }

    async function uploadChunks(file, sessionId, offset) {
        const chunkSize = 1024 * 1024; // 1MB chunks
        let startTime = Date.now();
        let uploadedBytesSinceStart = 0;

        try {
            while (offset < file.size) {
                if (isPaused) {
                    statusDiv.textContent = `Upload paused at ${Math.round((offset/file.size)*100)}%`;
                    speedDiv.textContent = "";
                    return;
                }

                const chunk = file.slice(offset, offset + chunkSize);
                const formData = new FormData();
                formData.append("offset", offset);
                formData.append("chunk", chunk);

                const chunkRes = await fetch(`/api/uploads/${sessionId}/chunks`, {
                    method: "PATCH",
                    body: formData
                });

                if (!chunkRes.ok) {
                    throw new Error(`Failed at offset ${offset}`);
                }

                const resData = await chunkRes.json();
                
                if (resData.status === "complete") {
                    progressBar.style.width = "100%";
                    statusDiv.textContent = "Upload complete!";
                    speedDiv.textContent = "";
                    pauseBtn.style.display = "none";
                    setTimeout(() => { window.location.href = "/files"; }, 2000);
                    return;
                }

                uploadedBytesSinceStart += chunk.size;
                const elapsedSec = (Date.now() - startTime) / 1000;
                if (elapsedSec > 0.5) {
                    const speedBps = uploadedBytesSinceStart / elapsedSec;
                    const speedMBps = (speedBps / 1024 / 1024).toFixed(2);
                    speedDiv.textContent = `Speed: ${speedMBps} MB/s`;
                }

                offset = resData.committed_size;
                const progress = (offset / file.size) * 100;
                progressBar.style.width = `${progress}%`;
                statusDiv.textContent = `Uploading... ${Math.round(progress)}%`;
            }
        } catch (err) {
            statusDiv.innerHTML = `<span class="error">Error: ${err.message}</span>`;
            pauseBtn.style.display = "none";
            resumeBtn.style.display = "inline-block";
        }
    }

    if (pauseBtn) {
        pauseBtn.addEventListener("click", () => {
            isPaused = true;
            pauseBtn.style.display = "none";
            resumeBtn.style.display = "inline-block";
        });
    }

    if (resumeBtn) {
        resumeBtn.addEventListener("click", async () => {
            isPaused = false;
            resumeBtn.style.display = "none";
            pauseBtn.style.display = "inline-block";
            
            statusDiv.textContent = "Resuming upload...";
            try {
                const res = await fetch(`/api/uploads/${currentSessionId}/status`);
                if (res.ok) {
                    const statusData = await res.json();
                    uploadChunks(fileInput.files[0], currentSessionId, statusData.committed_size);
                } else {
                    throw new Error("Could not fetch session status");
                }
            } catch (err) {
                statusDiv.innerHTML = `<span class="error">Error: ${err.message}</span>`;
            }
        });
    }

    if (uploadForm) {
        uploadForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const file = fileInput.files[0];
            if (!file) return;
            
            let customName = filenameInput.value.trim() || file.name;

            // Append extension if custom name is provided but doesn't have it
            if (filenameInput.value.trim()) {
                const originalExtMatch = file.name.match(/\.[0-9a-z]+$/i);
                if (originalExtMatch) {
                    const ext = originalExtMatch[0];
                    if (!customName.endsWith(ext)) {
                        customName += ext;
                    }
                }
            }

            let offset = 0;

            if (resumeSessionData) {
                if (file.size !== resumeSessionData.total_size || file.name !== resumeSessionData.original_filename) {
                    if (!confirm("The selected file does not match the original upload. Resume progress will be lost and a new upload will start. Continue?")) {
                        return;
                    }
                    // Cancel old session
                    await fetch(`/api/uploads/${resumeSessionId}`, { method: "DELETE" });
                    resumeSessionData = null;
                }
            }

            startBtn.style.display = "none";
            pauseBtn.style.display = "inline-block";
            statusDiv.textContent = "Initializing upload...";
            speedDiv.textContent = "";
            progressContainer.style.display = "block";
            progressBar.style.width = "0%";
            isPaused = false;

            try {
                if (resumeSessionData) {
                    currentSessionId = resumeSessionData.id;
                    offset = resumeSessionData.committed_size;
                } else {
                    // Init session
                    const initRes = await fetch("/api/uploads", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({
                            original_filename: customName,
                            total_size: file.size,
                            visibility: document.getElementById("visibility-input").value,
                            target_file_id: targetFileId ? parseInt(targetFileId) : null
                        })
                    });

                    if (!initRes.ok) {
                        throw new Error("Failed to init upload");
                    }

                    const sessionData = await initRes.json();
                    currentSessionId = sessionData.id;
                }
                
                uploadChunks(file, currentSessionId, offset);

            } catch (err) {
                statusDiv.innerHTML = `<span class="error">Error: ${err.message}</span>`;
                pauseBtn.style.display = "none";
                startBtn.style.display = "inline-block";
            }
        });
    }
});
