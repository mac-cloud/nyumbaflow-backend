from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .database import Base, engine
from .routers import auth, users, properties, units, tenants, leases, payments

# Auto-create tables on startup (simple deployments).
# For production migrations, use Alembic instead.
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="NyumbaFlow API",
    description="Property & rent management backend",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.allowed_origins.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(properties.router)
app.include_router(units.router)
app.include_router(tenants.router)
app.include_router(leases.router)
app.include_router(payments.router)


@app.get("/")
def root():
    return {"name": "NyumbaFlow API", "status": "ok"}


@app.get("/health")
def health():
    return {"status": "healthy"}
