# File Sharing System

A modular local file-sharing system built with **FastAPI, PostgreSQL, SQLAlchemy, Jinja2, Pydantic, and Argon2**.

## Architecture

```text
                         File Sharing System
                                  |
                +-----------------+-----------------+
                |                 |                 |
           Permissions      Resumable Upload      Status
                |                 |                 |
                +-----------------+-----------------+
                                  |
                         Performance Analysis
```

### Components

- **Permissions** — Every file is either **public** or **private**. Public files can be downloaded by anyone, but modification still requires permission. Private files require access permission to download or modify. Only the owner can change visibility, delete the file, or manage permissions.
- **Resumable Upload** — Large files are uploaded in chunks. If the client disconnects, it asks the server for committed progress and continues from the last confirmed chunk. Incomplete files remain `.part` files until finalization.
- **Status** — Shows upload progress, file availability, failures, storage usage, and useful system state to users/admins.
- **Performance Analysis** — Measures throughput for disk I/O, recovery time for resume upload.

## Technology Stack

- FastAPI + Uvicorn
- Python 3.11+
- PostgreSQL
- SQLAlchemy 2.x ORM + `asyncpg`
- Pydantic + `pydantic-settings`
- Jinja2 server-side rendering
- `pwdlib` with Argon2
- Alembic for database migrations
- Docker container

## Database

Use SQLAlchemy's modern typed ORM:

```python
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str]
    password_hash: Mapped[str]
```

Use an asynchronous PostgreSQL engine:

```python
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

engine = create_async_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
```

Use SQLAlchemy 2.x queries:

```python
from sqlalchemy import select

stmt = select(User).where(User.username == username)
user = (await session.scalars(stmt)).one_or_none()
```

NO need to use **Alembic** for schema migrations. Create tables automatically during application startup.

Pydantic handles application input validation, while PostgreSQL should still enforce fundamental integrity such as primary keys, foreign keys, uniqueness, and non-null constraints.

## Configuration

Use `pydantic-settings`:

```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str
    secret_key: secretStr
    upload_dir: str = "storage/uploads"
    max_upload_bytes: int = 2 * 1024 * 1024 * 1024

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
```

Never commit `.env` or secrets to Git.

## Authentication

Never store plaintext passwords. Use Argon2 through `pwdlib`:

```python
from pwdlib import PasswordHash

password_hash = PasswordHash.recommended()
hashed = password_hash.hash(password)
valid = password_hash.verify(password, hashed)
```

Use secure session cookies for the server-rendered application and CSRF protection for state-changing browser requests.

## Server-Side Rendering

Jinja2 is used only by frontend routes:

```python
@router.get("/files", response_class=HTMLResponse)
async def files_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="files.html",
        context={},
    )
```

Keep frontend and API endpoints separate. Frontend routes return HTML; API routes return structured data.

- `api/` — API endpoints only
- `frontend/` — Jinja2/HTML endpoints only
- `schemas/` — Pydantic validation
- `models/` — SQLAlchemy ORM models
- `repositories/` — database access
- `services/` — business logic
- `utils/` — reusable utilities
- `templates/` — Jinja2 pages
- `static/` — CSS/JS/images
- `storage/` — uploaded files; never expose directly as static files

## Resumable Upload

```text
Browser                    FastAPI
  |                          |
  | POST /api/uploads       |
  |------------------------->|
  |      upload_id           |
  |<-------------------------|
  |                          |
  | PATCH /.../chunks        |
  |------ chunk 0 ---------->|
  |------ chunk 1 ---------->|
  |------ chunk 2 ---------->|
  X connection lost          |
  |                          |
  | GET /.../status          |
  |------------------------->|
  |  committed progress      |
  |<-------------------------|
  |                          |
  | PATCH /.../chunks        |
  |------ remaining -------->|
  |                          |
  |       completed           |
  |<-------------------------|
```

Use `File.slice()` in the browser and HTTP chunk requests. The server is the source of truth for progress. Use `.part` files and atomically finalize only after the complete upload has been verified.

Additional safeguards:

- Maximum file/chunk size
- Per-user upload limits
- Chunk offset/index validation
- Duplicate/out-of-order chunk handling
- File checksum verification
- Cleanup of abandoned uploads
- Atomic finalization

## Validation and Errors

Everything from the client is untrusted. Validate form fields, query/path parameters, JSON, filenames, file metadata, upload IDs, chunk offsets, and permissions with Pydantic where applicable.

Example:

```python
from typing import Literal
from pydantic import BaseModel

class FileVisibilityUpdate(BaseModel):
    visibility: Literal["public", "private"]
```

Never trust client-provided filenames or paths. Prevent path traversal.

Use intentional responses such as:

```text
400  malformed request
401  not authenticated
403  not authorized
404  resource not found / inaccessible
409  state conflict
413  request/file too large
422  validation failure
429  rate limit exceeded
500  unexpected server error
503  temporary service/storage failure
```

Frontend failures should render an appropriate HTML response. API failures should return structured error data. Never expose stack traces, SQL errors, filesystem paths, or secrets.

## Minimal API Surface

```text
Authentication
POST   /api/auth/register
POST   /api/auth/login
POST   /api/auth/logout

Files
GET    /api/files
GET    /api/files/{file_id}
GET    /api/files/{file_id}/download
PATCH  /api/files/{file_id}
DELETE /api/files/{file_id}

Permissions
POST   /api/files/{file_id}/access-requests
POST   /api/files/{file_id}/permissions
DELETE /api/files/{file_id}/permissions/{user_id}

Resumable uploads
POST   /api/uploads
GET    /api/uploads/{upload_id}/status
PATCH  /api/uploads/{upload_id}/chunks
DELETE /api/uploads/{upload_id}

Frontend
GET    /login
GET    /register
GET    /files
GET    /files/{file_id}
GET    /upload
```

Keep the endpoint set small; add an endpoint only when it represents a real operation.

## Core Data Model

```text
User
 ├── owns → File
 ├── requests → AccessRequest
 └── receives → Permission

File
 ├── belongs to → User
 ├── has → Permission
 └── may have → UploadSession

Permission
 ├── belongs to → User
 └── belongs to → File

AccessRequest
 ├── requested by → User
 └── requested for → File

UploadSession
 ├── belongs to → User
 └── creates → File
```

Useful file metadata:

```text
id
owner_id
original_filename
storage_name
size
content_type
checksum
visibility
created_at
updated_at
```

Use a generated storage identifier rather than the original filename as the physical storage path.

## Important Rules

### Access control

```text
Request
  ↓
Authenticate
  ↓
Load file
  ↓
Check authorization
  ↓
Perform operation
```

Only the owner can make a file public/private or delete it.

### Storage

Keep file bytes on the filesystem and metadata/permissions in PostgreSQL:

```text
PostgreSQL                 Filesystem
-----------                ----------
owner                      actual bytes
filename                   generated storage ID
size                       .part files
permissions
checksum
status
```

Do not expose the upload directory as a public static directory.

### Atomic completion

```text
abc123.part
     |
     | upload + verification complete
     v
atomic rename
     |
     v
abc123
```

### Abandoned uploads

Expired upload sessions and `.part` files must be cleaned up periodically.

### Concurrency

Define behavior for simultaneous modification/deletion requests and prevent inconsistent database/filesystem state.

## Scope

This is intentionally a **single-node local file-sharing system**.

It demonstrates:

- Authentication
- Public/private files
- Access requests
- Modification permissions
- Resumable uploads
- Failure/recovery handling
- Status visualization
- Async PostgreSQL access
- Performance measurement

True high availability and distributed fault tolerance are outside the scope. Multiple FastAPI processes on one PC can demonstrate load-balancing concepts, but they do not protect against failure of the physical machine.

## Development Principles

1. Keep API and frontend endpoints separate.
2. Keep business logic out of route handlers.
3. Keep reusable utilities in `utils/`.
4. Validate all client input with Pydantic/application schemas.
5. Keep database integrity constraints as a second line of defense.
6. Use SQLAlchemy 2.x async ORM APIs.
7. Never trust client-provided identifiers or filenames.
8. Authorize every protected file operation.
9. Never expose incomplete uploads.
10. Never store plaintext passwords.
11. Never expose uploaded storage as a public static directory.
12. Keep secrets and user files outside version control.
13. Prefer a small number of well-defined endpoints.
