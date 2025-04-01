## Building and running the application locally

To run locally, we use `app.db` as a simple local database to test. 
Some files to verify to ensure correct connection,
- The property of database configuration `SQLALCHEMY_DATABASE_URL` in `backend\app\core\config.py` is pointing to `"sqlite:///./app.db"` not PostgreSQL. 

### Start Backend at localhost:8000 (NO DOCKER)
Open terminal 

```
cd backend
pip install -r requirements.txt # Or if you use VSCode, you can use command palette in VSCode Python: Create Environment to create a virtual environment and install dependencies. 
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head
# Optional: initialize some data
python -m app.initDB
# Start the python app locally
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Building and running the application with DOCKER

When you're ready, start your application by running:
`docker compose up --build`

The build of docker containers is based on `docker-compose.yml`, hence, this will create 2 containers for 2 services of our AUTH-SERVICE

- auth-db: PostgreSQL database for auth-service
- auth-service: FastAPI for auth-service

### Data Initialization for Sample Data
Use `docker compose exec` if the container is already running
```
# app.initDB is a script to generate some sample data quickly
docker compose exec auth-service python -m app.initDB
```

### Clean up
- Delete the existing containers, volumes and networks `docker compose down -v `
- Stop services but keep database/data `docker compose down`
- Reset environment completely and rebuild images and containers `docker compose down -v && docker compose up --build`