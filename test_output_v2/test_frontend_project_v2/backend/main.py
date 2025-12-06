from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="test_frontend_project_v2 API")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://frontend:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "test_frontend_project_v2_backend"}

# Database connection example (uncomment and configure as needed)
# from sqlalchemy import create_engine
# DATABASE_URL = "postgresql://test_frontend_project_v2_user:*Pn%ARXudl22Dj$f@database:5432/test_frontend_project_v2_db"
# engine = create_engine(DATABASE_URL)
