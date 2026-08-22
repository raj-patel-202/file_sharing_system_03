# File Sharing System

A modular local file-sharing system built with **FastAPI, PostgreSQL, SQLAlchemy, Jinja2, Pydantic, and Argon2**.

## About the System

- **Permissions** — Every file is either **public** or **private**. Public files can be downloaded by anyone, but modification still requires permission. Private files require access permission to download or modify. Only the owner can change visibility, delete the file, or manage permissions.
- **Resumable Upload** — Large files are uploaded in chunks. If the client disconnects, it asks the server for committed progress and continues from the last confirmed chunk.
- **Status Overview** — Shows upload progress, file availability, failures, and storage usage to users and admins.

## Quick Start (Docker)

To get started quickly without installing Python or PostgreSQL manually, you can use Docker. The Docker setup automatically configures the database and the web application for you.

### Prerequisites
- [Docker](https://docs.docker.com/get-docker/) installed on your machine
- [Docker Compose](https://docs.docker.com/compose/install/) (usually comes with Docker Desktop)

### Running the Application

1. **Clone the repository:**
   ```bash
   git clone https://github.com/raj-patel-202/file_sharing_system_03.git
   cd file_sharing_system_03
   ```

2. **Set up the environment variables:**
   Copy the `.env.example` file to `.env`:
   ```bash
   # On Linux/macOS
   cp .env.example .env
   
   # On Windows (Command Prompt)
   copy .env.example .env
   ```
   
   **Tip:** You can generate a secure random string for your `SECRET_KEY` by running the following command in your terminal (if you have Python installed):
   ```bash
   python -c "import secrets; print(secrets.token_hex(32))"
   ```
   Open the newly created `.env` file and replace the `SECRET_KEY` value with your generated string. The `DATABASE_URL` is already configured correctly for Docker.

3. **Start the containers:**
   Run the following command in the root directory of the project:
   ```bash
   docker-compose up -d --build
   ```
   *(Note: This might take a few minutes the first time as it downloads the PostgreSQL and Python images.)*

3. **Access the web application:**
   Once the containers are successfully running, open your web browser and navigate to:
   [http://localhost:8000](http://localhost:8000)

### Stopping the Application

To shut down the application and its database, run:
```bash
docker-compose down
```

*(Note: The database data and uploaded files are saved in local volumes, so your files will still be there the next time you start the application.)*
