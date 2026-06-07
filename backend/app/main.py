from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.config import settings
from .database import initialize_database
from .routers import account, admin, ai, auth, cart, catalog, health, orders, reviews, seller


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name, debug=settings.debug)
    @app.on_event("startup")
    def on_startup():
        initialize_database()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health.router)
    app.include_router(catalog.router)
    app.include_router(auth.router)
    app.include_router(account.router)
    app.include_router(cart.router)
    app.include_router(orders.router)
    app.include_router(orders.legacy_router)
    app.include_router(reviews.router)
    app.include_router(ai.router)
    app.include_router(ai.legacy_router)
    app.include_router(seller.router)
    app.include_router(admin.router)
    return app


app = create_app()
