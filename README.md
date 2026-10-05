# Proyecto SAP

Entorno de desarrollo contenerizado para Vue 3 + Vite, FastAPI y PostgreSQL.

## Iniciar

En VS Code, abre la paleta de comandos y ejecuta **Dev Containers: Reopen in Container**. Docker Desktop debe estar instalado y en ejecución. El contenedor instala las dependencias de npm y levanta los tres servicios.

- Frontend: http://localhost:5175
- API: http://localhost:8003
- Documentación interactiva: http://localhost:8003/docs
- PostgreSQL: localhost:5435

Desde la raíz del proyecto, puedes iniciar todo el stack con Docker Compose:

```sh
docker compose -f .devcontainer/docker-compose.yml up --build -d
```

Para iniciar un servicio específico, ejecuta:

```sh
# Base de datos
docker compose -f .devcontainer/docker-compose.yml up --build -d db

# Backend (también inicia la base de datos)
docker compose -f .devcontainer/docker-compose.yml up --build -d backend

# Frontend (también inicia el backend y la base de datos)
docker compose -f .devcontainer/docker-compose.yml up --build -d frontend
```

Compose inicia automáticamente las dependencias del servicio seleccionado. Para detener los servicios, ejecuta `docker compose -f .devcontainer/docker-compose.yml down`. Los datos de PostgreSQL persisten en un volumen nombrado; `down -v` los elimina.

## Estructura

- `frontend/`: aplicación Vue y configuración de Vite. El proxy `/api` llega al servicio `backend`.
- `backend/`: API FastAPI; `/api/testdb` valida la conexión con PostgreSQL.
- `.devcontainer/`: definición de los servicios Docker Compose y del dev container.

Las credenciales del Compose son solo para desarrollo local. Se debe cambiar esos valores antes de cualquier despliegue y no guardes secretos reales en el repositorio.
