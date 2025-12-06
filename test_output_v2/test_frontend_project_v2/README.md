# test_frontend_project_v2

Generated development environment with fastapi backend and postgres database.

## Prerequisites

- Docker and Docker Compose installed
- Python 3.11+ (for local development without Docker)

## Quick Start with Docker

1. Make sure you're in the project root directory
2. Copy the environment file:
   ```bash
   cp .env.example .env
   ```
   (Or use the provided `.env` file)

3. Start all services:
   ```bash
   docker compose up
   ```

4. The backend API will be available at:
   - http://localhost:8000

5. Test the health endpoint:
   ```bash
   curl http://localhost:8000/health
   ```

## Running Without Docker

### Backend (FastAPI)

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the development server:
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

### Database (PostgreSQL)

For local development, you'll need PostgreSQL installed:

1. Create the database:
   ```bash
   createdb test_frontend_project_v2_db
   ```

2. Update your backend code to use the local database connection string:
   ```
   postgresql://test_frontend_project_v2_user:*Pn%ARXudl22Dj$f@localhost:5432/test_frontend_project_v2_db
   ```

## Project Structure

```
test_frontend_project_v2/
├── backend/              # Backend application code
│   ├── main.py          # FastAPI application
│   ├── requirements.txt # Python dependencies
│   └── Dockerfile       # Backend Docker image
├── database/            # Database initialization scripts (if any)
├── docker-compose.yml   # Docker Compose configuration
├── .env                 # Environment variables (do not commit!)
└── README.md            # This file
```

## Environment Variables

The `.env` file contains configuration for all services. Key variables:

- `PROJECT_NAME`: Project name
- `BACKEND_PORT`: Backend service port (default: 8000)
- `DATABASE_PORT`: Database port (default: 5432)
- `DATABASE_NAME`: Database name
- `DATABASE_USER`: Database user
- `DATABASE_PASSWORD`: Database password (change in production!)

**Important:** Never commit the `.env` file to version control. It contains sensitive information.

## API Endpoints

### Health Check

- **GET** `/health`
  - Returns: `{"status": "healthy", "service": "test_frontend_project_v2_backend"}`

## Development Workflow

1. Make changes to your code
2. If using Docker, rebuild and restart:
   ```bash
   docker compose up --build
   ```
3. If running locally, the development server will auto-reload on file changes

## Troubleshooting

### Port Already in Use

If you get a port conflict error, you can change the ports in the `.env` file and restart the services.

### Database Connection Issues

- Ensure the database service is running: `docker compose ps`
- Check the database logs: `docker compose logs database`
- Verify environment variables in `.env` match the docker-compose.yml configuration

### Backend Not Starting

- Check backend logs: `docker compose logs backend`
- Verify Python dependencies are installed correctly
- Ensure the backend port is not already in use

## Stopping Services

To stop all services:
```bash
docker compose down
```

To stop and remove volumes (this will delete database data):
```bash
docker compose down -v
```
