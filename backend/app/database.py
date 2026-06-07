import os
from pathlib import Path
from urllib.parse import quote

from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import DeclarativeBase, sessionmaker

ENV_FILE = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(ENV_FILE)

DEFAULT_DATABASE_URL = "mysql+pymysql://root:password@localhost:3306/cartium_clone"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
SQLITE_FALLBACK_PATH = PROJECT_ROOT / ".local" / "cartium_fallback.db"


def normalize_database_url(raw_url: str) -> str:
    database_url = raw_url.strip()
    if database_url.startswith("mysql://"):
        return database_url.replace("mysql://", "mysql+pymysql://", 1)
    return database_url


def build_database_url() -> str:
    for env_key in ("DATABASE_URL", "MYSQL_PUBLIC_URL", "MYSQL_URL"):
        raw_value = os.getenv(env_key)
        if raw_value:
            return normalize_database_url(raw_value)

    host = os.getenv("DB_HOST") or os.getenv("MYSQLHOST")
    port = os.getenv("DB_PORT") or os.getenv("MYSQLPORT") or "3306"
    user = os.getenv("DB_USER") or os.getenv("MYSQLUSER")
    password = os.getenv("DB_PASSWORD") or os.getenv("MYSQLPASSWORD") or ""
    database = os.getenv("DB_NAME") or os.getenv("MYSQLDATABASE")

    if host and user and database:
        return (
            "mysql+pymysql://"
            f"{quote(user, safe='')}:{quote(password, safe='')}"
            f"@{host}:{port}/{quote(database, safe='')}"
        )

    return DEFAULT_DATABASE_URL


def sqlite_fallback_enabled() -> bool:
    value = os.getenv("ALLOW_SQLITE_FALLBACK", "true").strip().lower()
    environment = os.getenv("APP_ENV", "development").strip().lower()
    return environment != "production" and value not in {"0", "false", "no", "off"}


def make_engine(database_url: str):
    if database_url.startswith("sqlite"):
        return create_engine(database_url, connect_args={"check_same_thread": False})
    return create_engine(database_url, pool_pre_ping=True, pool_recycle=1800, connect_args={"connect_timeout": 10})


def create_resilient_engine():
    primary_url = build_database_url()
    primary_engine = make_engine(primary_url)
    if not sqlite_fallback_enabled():
        return primary_url, primary_engine

    try:
        with primary_engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return primary_url, primary_engine
    except OperationalError:
        SQLITE_FALLBACK_PATH.parent.mkdir(parents=True, exist_ok=True)
        fallback_url = f"sqlite:///{SQLITE_FALLBACK_PATH.as_posix()}"
        return fallback_url, make_engine(fallback_url)


DATABASE_URL, engine = create_resilient_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



def initialize_database() -> None:
    from . import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    inspector = inspect(engine)
    if "cart_items" not in inspector.get_table_names():
        return

    column_names = {column["name"] for column in inspector.get_columns("cart_items")}
    with engine.begin() as connection:
        if "cart_id" not in column_names:
            if DATABASE_URL.startswith("sqlite"):
                connection.execute(text("ALTER TABLE cart_items ADD COLUMN cart_id INTEGER"))
            else:
                connection.execute(text("ALTER TABLE cart_items ADD COLUMN cart_id INTEGER NULL"))

        if DATABASE_URL.startswith("sqlite"):
            connection.execute(
                text(
                    """
                    INSERT INTO carts (user_id, name, is_active)
                    SELECT DISTINCT ci.user_id, 'Main cart', 1
                    FROM cart_items ci
                    WHERE ci.user_id IS NOT NULL
                    AND NOT EXISTS (
                        SELECT 1 FROM carts c WHERE c.user_id = ci.user_id
                    )
                    """
                )
            )
            connection.execute(
                text(
                    """
                    UPDATE cart_items
                    SET cart_id = (
                        SELECT c.id FROM carts c
                        WHERE c.user_id = cart_items.user_id
                        ORDER BY c.is_active DESC, c.id ASC
                        LIMIT 1
                    )
                    WHERE cart_id IS NULL
                    """
                )
            )
        else:
            connection.execute(
                text(
                    """
                    INSERT INTO carts (user_id, name, is_active)
                    SELECT DISTINCT ci.user_id, 'Main cart', 1
                    FROM cart_items ci
                    WHERE ci.user_id IS NOT NULL
                    AND NOT EXISTS (
                        SELECT 1 FROM carts c WHERE c.user_id = ci.user_id
                    )
                    """
                )
            )
            connection.execute(
                text(
                    """
                    UPDATE cart_items ci
                    JOIN carts c ON c.user_id = ci.user_id AND c.is_active = 1
                    SET ci.cart_id = c.id
                    WHERE ci.cart_id IS NULL
                    """
                )
            )
