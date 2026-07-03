from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.core.config import settings
from app.db.database import async_engine, motor_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ──────────────────────────────────────────────────────────
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    # Load ML model once; stored on app.state so all requests share the same instance
    try:
        from app.ml.predictor import ModelPredictor
        app.state.predictor = ModelPredictor()
    except FileNotFoundError:
        # Model not yet trained — /api/ml/estimate-price will return 503 until trained
        app.state.predictor = None

    yield

    # ── Shutdown ─────────────────────────────────────────────────────────
    await async_engine.dispose()
    motor_client.close()


def create_app() -> FastAPI:
    _app = FastAPI(
        title="RentWise API",
        description="Smart Real Estate Platform — API Documentation",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    _app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    _app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

    # Register all domain routers
    from app.routers.auth_router import router as auth_router
    from app.routers.user_router import router as user_router
    from app.routers.property_router import router as property_router
    from app.routers.booking_router import router as booking_router
    from app.routers.application_router import router as application_router
    from app.routers.lease_router import router as lease_router
    from app.routers.payment_router import router as payment_router
    from app.routers.review_router import router as review_router
    from app.routers.maintenance_router import router as maintenance_router
    from app.routers.notification_router import router as notification_router
    from app.routers.admin_router import router as admin_router
    from app.routers.ml_router import router as ml_router
    from app.routers.file_router import router as file_router
    from app.routers.saved_property_router import router as saved_property_router
    from app.routers.settings_router import router as settings_router
    from app.routers.export_router import router as export_router

    _app.include_router(auth_router,         prefix="/api/auth",          tags=["Auth"])
    _app.include_router(user_router,         prefix="/api/users",         tags=["Users"])
    _app.include_router(property_router,     prefix="/api/properties",    tags=["Properties"])
    _app.include_router(booking_router,      prefix="/api/bookings",      tags=["Bookings"])
    _app.include_router(application_router,  prefix="/api/applications",  tags=["Applications"])
    _app.include_router(lease_router,        prefix="/api/leases",        tags=["Leases"])
    _app.include_router(payment_router,      prefix="/api/payments",      tags=["Payments"])
    _app.include_router(review_router,       prefix="/api/reviews",       tags=["Reviews"])
    _app.include_router(maintenance_router,  prefix="/api/maintenance",   tags=["Maintenance"])
    _app.include_router(notification_router, prefix="/api/notifications", tags=["Notifications"])
    _app.include_router(admin_router,        prefix="/api/admin",         tags=["Admin"])
    _app.include_router(ml_router,           prefix="/api/ml",            tags=["ML"])
    _app.include_router(file_router,         prefix="/api/files",         tags=["Files"])
    _app.include_router(saved_property_router, prefix="/api/saved-properties", tags=["Saved Properties"])
    _app.include_router(settings_router,     prefix="/api/settings",      tags=["Settings"])
    _app.include_router(export_router,        prefix="/api/admin",         tags=["Export"])

    return _app


fastapi_app = create_app()

# Wrap with Socket.IO after fastapi_app is fully constructed (avoids circular import)
from app.websockets.socket_manager import create_socket_app  # noqa: E402
app = create_socket_app(fastapi_app)
