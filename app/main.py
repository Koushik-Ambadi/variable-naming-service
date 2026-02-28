from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager

from app.api import routes
from app.core.database import init_db


# ✅ Lifespan handler (modern FastAPI way)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database once at startup
    init_db()
    yield
    # (Optional) add shutdown logic here later if needed


app = FastAPI(
    title="Variable Naming Service",
    lifespan=lifespan
)

# Serve static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")


# Landing pages
@app.get("/")
def read_index():
    return FileResponse("app/static/index.html")

@app.get("/admin")
def read_admin():
    return FileResponse("app/static/admin.html")

@app.get("/index")
def read_index_alias():
    return FileResponse("app/static/index.html")

@app.get("/maab")
def read_maab():
    return FileResponse("app/static/maab.html")


# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ⚠ tighten this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes
app.include_router(routes.router)