# Workspace Instructions

- The frontend is a Vue 3 application built with Vite in `frontend/`.
- The API is a FastAPI application in `backend/`; keep routes under `/api`.
- PostgreSQL is the `db` service in `.devcontainer/docker-compose.yml`. Use the `DATABASE_URL` environment variable from the backend rather than hardcoding connection details in application code.
- Run and debug the stack through the Docker Compose dev container defined in `.devcontainer/devcontainer.json`.
- Keep development-only credentials out of production deployments and never commit a real `.env` file.
