import pytest
from sqlalchemy import inspect
from app.db import engine, Base, get_db
from app.models import (
    User, GdsScript, GdsBuild, GdsCell, GdsElement,
    Issue, IssueElement, WikiPage, Comment, AgentSession,
)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def test_all_tables_exist():
    inspector = inspect(engine)
    table_names = inspector.get_table_names()
    expected = [
        "users", "gds_scripts", "gds_builds", "gds_cells", "gds_elements",
        "issues", "issue_elements", "wiki_pages", "comments", "agent_sessions",
    ]
    for table in expected:
        assert table in table_names, f"Missing table: {table}"


def test_create_script_and_build():
    from sqlalchemy.orm import Session
    with Session(engine) as session:
        script = GdsScript(
            path="scripts/ring_resonator.py",
            name="ring_resonator",
            description="Ring resonator design",
        )
        session.add(script)
        session.flush()

        build = GdsBuild(
            script_id=script.id,
            gds_path="gds/ring_resonator.gds",
            status="success",
        )
        session.add(build)
        session.commit()

        assert script.id is not None
        assert build.id is not None
        assert build.script_id == script.id
