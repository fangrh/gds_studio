"""SQLAlchemy database connection and session management."""
import hashlib
import os
import uuid

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase

DB_PATH = os.environ.get("GDS_COLLAB_DB", "gds_collab.db")

engine = create_engine(
    f"sqlite:///{DB_PATH}",
    connect_args={"check_same_thread": False},
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def run_migrations():
    """Add projects table and project_id FK to existing tables."""
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name='projects'")
        )
        if result.fetchone():
            return

        conn.execute(text("""
            CREATE TABLE projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(200) NOT NULL UNIQUE,
                description TEXT DEFAULT '',
                token_hash VARCHAR(64) NOT NULL UNIQUE,
                last_sync_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """))

        default_token = str(uuid.uuid4())
        default_hash = hashlib.sha256(default_token.encode()).hexdigest()
        conn.execute(text(
            "INSERT INTO projects (name, description, token_hash) "
            "VALUES ('main', 'Default project', :hash)"
        ), {"hash": default_hash})

        for table in ["issues", "wiki_pages", "gds_scripts", "gds_builds"]:
            try:
                conn.execute(text(
                    f"ALTER TABLE {table} ADD COLUMN project_id INTEGER DEFAULT 1"
                ))
            except Exception:
                pass

        # Drop old global unique index on wiki_pages.slug, replace with composite
        try:
            conn.execute(text("DROP INDEX IF EXISTS ix_wiki_pages_slug"))
        except Exception:
            pass
        try:
            conn.execute(text(
                "CREATE UNIQUE INDEX IF NOT EXISTS uq_wiki_slug_project "
                "ON wiki_pages (slug, project_id)"
            ))
        except Exception:
            pass

        # Drop old unique index on gds_scripts.path (now per-project)
        try:
            conn.execute(text("DROP INDEX IF EXISTS ix_gds_scripts_path"))
        except Exception:
            pass

        conn.commit()

        print(f"Migration complete. Default project token: {default_token}")
        print("Save this token — it won't be shown again.")
