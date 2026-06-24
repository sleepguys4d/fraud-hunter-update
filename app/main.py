import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .config import settings
from .database import Base, engine, SessionLocal
from .seed import seed
from .routers import (dashboard, transactions, rules, killchain,
                      cases, aml, network, threat)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # garante a pasta da BD SQLite
    if settings.database_url.startswith("sqlite"):
        path = settings.database_url.split("///")[-1]
        d = os.path.dirname(path)
        if d:
            os.makedirs(d, exist_ok=True)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed(db)
    finally:
        db.close()
    yield


app = FastAPI(title=settings.app_name, version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)

for r in (dashboard, transactions, rules, killchain, cases, aml, network, threat):
    app.include_router(r.router)


@app.get("/api/health", tags=["meta"])
def health():
    return {"status": "ok", "service": settings.app_name, "auth_disabled": settings.auth_disabled}


_static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
if os.path.isdir(_static_dir):
    app.mount("/", StaticFiles(directory=_static_dir, html=True), name="static")
