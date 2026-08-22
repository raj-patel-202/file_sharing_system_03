// SYS.SHARE // Retro Terminal JS

document.addEventListener("DOMContentLoaded", async () => {

    // --- Active Navbar Tab ---
    function setActiveNavTab() {
        const path = window.location.pathname;
        document.querySelectorAll("nav a").forEach(link => {
            const href = link.getAttribute("href");
            if (href && (path === href || (href === "/files" && path === "/"))) {
                link.classList.add("active");
            } else if (href && href !== "#" && href !== "/" && path.startsWith(href)) {
                link.classList.add("active");
            } else {
                link.classList.remove("active");
            }
        });
    }

    setActiveNavTab();

    function formatFileSize(bytes) {
        if (bytes < 1024) return `${bytes} B`;
        if (bytes < 1048576) return `${(bytes / 1024).toFixed(1)} KB`;
        if (bytes < 1073741824) return `${(bytes / 1048576).toFixed(1)} MB`;
        return `${(bytes / 1073741824).toFixed(2)} GB`;
    }

    function formatFileName(filename) {
        if (!filename) return "";
        const lastDotIndex = filename.lastIndexOf('.');
        if (lastDotIndex === -1 || lastDotIndex === 0) {
            return filename.length > 20 ? filename.substring(0, 20) + "..." : filename;
        }
        const name = filename.substring(0, lastDotIndex);
        const ext = filename.substring(lastDotIndex);
        if (name.length > 20) {
            return name.substring(0, 20) + "..." + ext;
        }
        return filename;
    }

    function getStatusBadges(access_status, visibility) {
        const badges = [];

        if (access_status === 'owner') {
            badges.push('<span class="status-badge status-owner">OWNER</span>');
        } else if (access_status === 'granted_modify') {
            // No need to show what permission is allowed if both are allowed (requested by user)
        } else if (access_status === 'granted_read' || access_status === 'granted_read_pending_modify') {
            // No need to show what permission is allowed (requested by user)
        } else if (access_status === 'none' && visibility !== 'public') {
            badges.push('<span class="status-badge status-none">NO ACCESS</span>');
        }

        // Visibility badge
        if (visibility === 'public') {
            badges.push('<span class="status-badge status-public">PUBLIC</span>');
        } else {
            badges.push('<span class="status-badge status-private">PRIVATE</span>');
        }

        return badges.join(' ');
    }

    // --- Fetch and display user info ---
    const userInfo = document.getElementById("user-info");
    if (userInfo) {
        try {
            const res = await fetch("/api/auth/me");
            if (res.ok) {
                const user = await res.json();
                userInfo.innerHTML = `<span>[ ${user.username} ]</span>`;
            }
        } catch(e) {}
    }

    // --- Logout ---
    const logoutBtn = document.getElementById("logout-btn");
    if (logoutBtn) {
        logoutBtn.addEventListener("click", async (e) => {
            e.preventDefault();
            await fetch("/api/auth/logout", { method: "POST" });
            window.location.href = "/login";
        });
    }

    // --- Login Form ---
    const loginForm = document.getElementById("login-form");
    if (loginForm) {
        loginForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const username = document.getElementById("username").value;
            const password = document.getElementById("password").value;
            const errorMsg = document.getElementById("error-msg");
            
            try {
                const res = await fetch("/api/auth/login", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ username, password })
                });
                
                if (res.ok) {
                    window.location.href = "/files";
                } else {
                    const data = await res.json();
                    errorMsg.style.display = "block";
                    errorMsg.textContent = `ERR: ${data.detail || "Authentication failed"}`;
                }
            } catch (err) {
                errorMsg.style.display = "block";
                errorMsg.textContent = "ERR: Connection to server failed";
            }
        });
    }

    // --- Register Form ---
    const registerForm = document.getElementById("register-form");
    if (registerForm) {
        registerForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const username = document.getElementById("username").value;
            const password = document.getElementById("password").value;
            const errorMsg = document.getElementById("error-msg");
            
            try {
                const res = await fetch("/api/auth/register", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ username, password })
                });
                
                if (res.ok) {
                    errorMsg.className = "success-msg";
                    errorMsg.style.display = "block";
                    errorMsg.textContent = "Account created. Redirecting to login...";
                    setTimeout(() => { window.location.href = "/login"; }, 2000);
                } else {
                    const data = await res.json();
                    errorMsg.style.display = "block";
                    errorMsg.textContent = `ERR: ${data.detail || "Registration failed"}`;
                }
            } catch (err) {
                errorMsg.style.display = "block";
                errorMsg.textContent = "ERR: Connection to server failed";
            }
        });
    }

    // --- File drop zone ---
    const dropZone = document.getElementById("file-drop-zone");
    const fileInput = document.getElementById("file-input");
    if (dropZone && fileInput) {
        dropZone.addEventListener("click", () => fileInput.click());

        dropZone.addEventListener("dragover", (e) => {
            e.preventDefault();
            dropZone.classList.add("dragover");
        });

        dropZone.addEventListener("dragleave", () => {
            dropZone.classList.remove("dragover");
        });

        dropZone.addEventListener("drop", (e) => {
            e.preventDefault();
            dropZone.classList.remove("dragover");
            if (e.dataTransfer.files.length > 0) {
                fileInput.files = e.dataTransfer.files;
                updateDropZoneText(e.dataTransfer.files[0]);
            }
        });

        fileInput.addEventListener("change", () => {
            if (fileInput.files.length > 0) {
                updateDropZoneText(fileInput.files[0]);
            }
        });

        function updateDropZoneText(file) {
            const dropText = document.getElementById("file-drop-text");
            dropText.textContent = `${file.name} (${formatFileSize(file.size)})`;
            dropZone.classList.add("file-selected");
        }
    }

    // --- Load files ---
    const fileList = document.getElementById("file-list");
    if (fileList) {
        loadFiles();
    }
    
    if (document.getElementById("requests-list")) {
        loadRequests();
    }

    async function loadFiles() {
        try {
            const res = await fetch("/api/files");
            if (res.ok) {
                const files = await res.json();
                fileList.innerHTML = "";
                
                const filter = fileList.getAttribute("data-filter") || "all";
                
                // Fetch incomplete sessions for owner view
                if (filter === "owner") {
                    try {
                        const sessRes = await fetch("/api/uploads/sessions");
                        if (sessRes.ok) {
                            const sessions = await sessRes.json();
                            sessions.forEach(s => {
                                const progress = Math.round((s.committed_size / s.total_size) * 100);
                                const div = document.createElement("div");
                                div.className = "file-item incomplete-upload";
                                div.innerHTML = `
                                    <div class="file-info">
                                        <div class="file-name">[INCOMPLETE] ${formatFileName(s.original_filename)}</div>
                                        <div class="file-meta">
                                            <span><span class="meta-label">SIZE:</span> ${formatFileSize(s.total_size)}</span>
                                            <span><span class="meta-label">PROGRESS:</span> ${progress}%</span>
                                        </div>
                                        <span class="status-badge status-pending">INCOMPLETE UPLOAD</span>
                                    </div>
                                    <div class="file-actions">
                                        <a href="/upload?resume_session=${s.id}" class="action-modify">[RESUME]</a>
                                        <button class="action-delete" onclick="cancelSession('${s.id}')">[DELETE]</button>
                                    </div>
                                `;
                                fileList.appendChild(div);
                            });
                        }
                    } catch(e) {}
                }

                const displayFiles = filter === "owner" ? files.filter(f => f.access_status === "owner") : files;

                // Stats bar (centered)
                const statsBar = document.getElementById("files-stats");
                if (statsBar) {
                    const totalFiles = displayFiles.length;
                    const totalSize = displayFiles.reduce((sum, f) => sum + f.size, 0);
                    const publicCount = displayFiles.filter(f => f.visibility === 'public').length;
                    const privateCount = displayFiles.filter(f => f.visibility === 'private').length;

                    statsBar.style.display = "flex";
                    statsBar.innerHTML = `
                        <div class="stat-item">
                            <span class="stat-value">${totalFiles}</span>
                            <span class="stat-label">FILES</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-value">${formatFileSize(totalSize)}</span>
                            <span class="stat-label">TOTAL</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-value">${publicCount}</span>
                            <span class="stat-label">PUBLIC</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-value">${privateCount}</span>
                            <span class="stat-label">PRIVATE</span>
                        </div>
                    `;
                }

                if (displayFiles.length === 0 && fileList.innerHTML === "") {
                    fileList.innerHTML = `
                        <div class="empty-state">
                            No files found. ${filter === "owner" ? '<a href="/upload">[UPLOAD YOUR FIRST FILE]</a>' : ''}
                        </div>
                    `;
                    return;
                }

                displayFiles.forEach(f => {
                    const div = document.createElement("div");
                    div.className = "file-item";
                    
                    let actions = "";
                    if (f.access_status === "owner") {
                        actions = `
                            <select class="vis-select" onchange="updateVisibility(${f.id}, this.value)">
                                <option value="private" ${f.visibility==='private'?'selected':''}>Private</option>
                                <option value="public" ${f.visibility==='public'?'selected':''}>Public</option>
                            </select>
                            <a href="/upload?target_file=${f.id}" class="action-modify">[MODIFY]</a>
                            <a href="/api/files/${f.id}/download" class="action-download">[DOWNLOAD]</a>
                            <button class="action-delete" onclick="deleteFile(${f.id})">[DELETE]</button>
                        `;
                    } else if (f.access_status === "granted_modify") {
                        actions = `
                            <a href="/upload?target_file=${f.id}" class="action-modify">[MODIFY]</a>
                            <a href="/api/files/${f.id}/download" class="action-download">[DOWNLOAD]</a>
                        `;
                    } else if (f.access_status === "granted_read") {
                        actions = `
                            <a href="/api/files/${f.id}/download" class="action-download">[DOWNLOAD]</a>
                            <button class="action-request" onclick="requestAccess(${f.id})">[REQUEST MODIFY]</button>
                        `;
                    } else if (f.access_status === "granted_read_pending_modify") {
                        actions = `
                            <a href="/api/files/${f.id}/download" class="action-download">[DOWNLOAD]</a>
                            <span class="action-request" style="cursor: default;">[MODIFY REQUESTED]</span>
                        `;
                    } else if (f.access_status === "pending") {
                        actions = `<span class="action-request" style="cursor: default;">[ACCESS PENDING]</span>`;
                    } else {
                        actions = `<button class="action-request" onclick="requestAccess(${f.id})">[REQUEST ACCESS]</button>`;
                    }

                    const dateStr = new Date(f.created_at).toLocaleString();
                    let modifyInfo = "";
                    if (f.last_modified_by_username) {
                        const updateStr = new Date(f.updated_at).toLocaleString();
                        modifyInfo = `<div class="file-modify-info">Modified by ${f.last_modified_by_username} — ${updateStr}</div>`;
                    }

                    const badgesHtml = getStatusBadges(f.access_status, f.visibility);

                    div.innerHTML = `
                        <div class="file-info">
                            <div class="file-name">${formatFileName(f.original_filename)}</div>
                            <div class="file-meta">
                                <span><span class="meta-label">BY:</span> ${f.owner_username}</span>
                                <span><span class="meta-label">SIZE:</span> ${formatFileSize(f.size)}</span>
                                <span><span class="meta-label">DATE:</span> ${dateStr}</span>
                            </div>
                            <div style="display: flex; gap: 6px; flex-wrap: wrap; margin-top: 4px;">
                                ${badgesHtml}
                            </div>
                            ${modifyInfo}
                        </div>
                        <div class="file-actions">${actions}</div>
                    `;
                    fileList.appendChild(div);
                });
            } else {
                if (res.status === 401) window.location.href = "/login";
                fileList.innerHTML = '<div class="empty-state">Failed to load files.</div>';
            }
        } catch (e) {
            fileList.innerHTML = '<div class="empty-state">Connection error.</div>';
        }
    }

    // --- Global actions ---
    window.updateVisibility = async (id, visibility) => {
        await fetch(`/api/files/${id}`, {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ visibility })
        });
        loadFiles();
    };

    window.cancelSession = async (id) => {
        if(confirm("Cancel this upload?")) {
            await fetch(`/api/uploads/${id}`, { method: "DELETE" });
            loadFiles();
        }
    };

    window.deleteFile = async (id) => {
        if(confirm("Delete file permanently?")) {
            await fetch(`/api/files/${id}`, { method: "DELETE" });
            loadFiles();
        }
    };

    window.requestAccess = async (id) => {
        await fetch(`/api/files/${id}/access-requests`, { method: "POST" });
        loadFiles();
    };

    window.approveRequest = async (id, level) => {
        await fetch(`/api/access-requests/${id}/approve?level=${level}`, { method: "POST" });
        loadRequests();
    };

    window.rejectRequest = async (id) => {
        await fetch(`/api/access-requests/${id}/reject`, { method: "DELETE" });
        loadRequests();
    };

    async function loadRequests() {
        const reqList = document.getElementById("requests-list");
        if (!reqList) return;

        try {
            const res = await fetch("/api/access-requests");
            if (res.ok) {
                const reqs = await res.json();
                reqList.innerHTML = "";
                if (reqs.length > 0) {
                    reqs.forEach(r => {
                        const div = document.createElement("div");
                        div.className = "request-item";
                        div.innerHTML = `
                            <div class="request-info">
                                <span class="request-user">${r.username}</span> requests access to <span class="request-file">${r.filename}</span>
                            </div>
                            <div class="request-actions">
                                <button class="btn-approve" onclick="approveRequest(${r.id}, 'read')">[DOWNLOAD]</button>
                                <button class="btn-modify-approve" onclick="approveRequest(${r.id}, 'modify')">[MODIFY]</button>
                                <button class="btn-danger" onclick="rejectRequest(${r.id})">[REJECT]</button>
                            </div>
                        `;
                        reqList.appendChild(div);
                    });
                } else {
                    reqList.innerHTML = '<div class="empty-state">No pending requests.</div>';
                }
            }
        } catch (e) {
            console.error(e);
        }
    }
});
