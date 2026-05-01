from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Text, Float, DateTime, ForeignKey,
    JSON, and_, Enum as SAEnum,
)
from sqlalchemy.orm import relationship, foreign
from app.db import Base


def utcnow():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(100), unique=True, nullable=False)
    display_name = Column(String(200))


# --- GDS Source Tracking ---

class GdsScript(Base):
    __tablename__ = "gds_scripts"

    id = Column(Integer, primary_key=True)
    path = Column(String(500), unique=True, nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, default="")
    params_json = Column(JSON, default=dict)
    last_modified = Column(DateTime, default=utcnow)
    git_commit = Column(String(40))

    builds = relationship("GdsBuild", back_populates="script", order_by="GdsBuild.created_at.desc()")


class GdsBuild(Base):
    __tablename__ = "gds_builds"

    id = Column(Integer, primary_key=True)
    script_id = Column(Integer, ForeignKey("gds_scripts.id"), nullable=False)
    gds_path = Column(String(500), nullable=False)
    status = Column(String(20), default="pending")  # pending, success, failed
    build_log = Column(Text, default="")
    git_commit = Column(String(40))
    created_at = Column(DateTime, default=utcnow)

    script = relationship("GdsScript", back_populates="builds")
    cells = relationship("GdsCell", back_populates="build")


class GdsCell(Base):
    __tablename__ = "gds_cells"

    id = Column(Integer, primary_key=True)
    build_id = Column(Integer, ForeignKey("gds_builds.id"), nullable=False)
    name = Column(String(200), nullable=False)
    cell_type = Column(String(50), default="cell")
    bbox = Column(String(100))  # "x1,y1,x2,y2"
    layer_count = Column(Integer, default=0)
    element_count = Column(Integer, default=0)

    build = relationship("GdsBuild", back_populates="cells")
    elements = relationship("GdsElement", back_populates="cell")


class GdsElement(Base):
    __tablename__ = "gds_elements"

    id = Column(Integer, primary_key=True)
    cell_id = Column(Integer, ForeignKey("gds_cells.id"), nullable=False)
    element_type = Column(String(50), nullable=False)  # polygon, path, text, reference
    layer = Column(String(20), nullable=False)  # "M1", "D1", etc.
    bbox = Column(String(100))
    path_data = Column(Text, default="")  # serialized geometry
    properties = Column(JSON, default=dict)
    source_line = Column(Integer)  # line in the Python script that created this

    cell = relationship("GdsCell", back_populates="elements")


# --- Collaboration ---

class Issue(Base):
    __tablename__ = "issues"

    id = Column(Integer, primary_key=True)
    title = Column(String(500), nullable=False)
    body = Column(Text, default="")
    status = Column(String(20), default="open")  # open, in_progress, resolved, closed
    author_type = Column(String(20), nullable=False, default="user")
    author_id = Column(Integer, default=1)
    priority = Column(String(10), default="normal")
    tags = Column(JSON, default=list)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)
    resolved_by = Column(String(50))
    resolved_at = Column(DateTime)
    script_path = Column(String(500))

    linked_elements = relationship("IssueElement", back_populates="issue")
    comments = relationship(
        "Comment",
        primaryjoin="and_(foreign(Comment.target_id) == Issue.id, Comment.target_type == 'issue')",
        order_by="Comment.created_at",
        viewonly=True,
    )


class IssueElement(Base):
    __tablename__ = "issue_elements"

    id = Column(Integer, primary_key=True)
    issue_id = Column(Integer, ForeignKey("issues.id"), nullable=False)
    gds_build_id = Column(Integer, ForeignKey("gds_builds.id"))
    cell_name = Column(String(200))
    element_id = Column(Integer)
    layer = Column(String(20))
    bbox = Column(String(100))
    source_script_line = Column(Integer)
    deep_link_url = Column(String(1000))

    issue = relationship("Issue", back_populates="linked_elements")
    build = relationship("GdsBuild")


class WikiPage(Base):
    __tablename__ = "wiki_pages"

    id = Column(Integer, primary_key=True)
    title = Column(String(500), nullable=False)
    slug = Column(String(200), unique=True, nullable=False)
    body = Column(Text, default="")
    category = Column(String(100), default="general")
    tags = Column(JSON, default=list)
    version = Column(Integer, default=1)
    last_editor_type = Column(String(20), default="user")
    last_editor_id = Column(Integer, default=1)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)


class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True)
    target_type = Column(String(20), nullable=False)  # "issue" or "wiki"
    target_id = Column(Integer, nullable=False)
    author_type = Column(String(20), nullable=False, default="user")  # "user" or "agent"
    author_id = Column(Integer, default=1)
    body = Column(Text, nullable=False)
    agent_model = Column(String(100))  # e.g. "claude-sonnet-4.6"
    agent_skill_version = Column(String(50))
    created_at = Column(DateTime, default=utcnow)
    edited_at = Column(DateTime)

    issue = relationship(
        "Issue",
        primaryjoin="and_(Comment.target_id == foreign(Issue.id), Comment.target_type == 'issue')",
        viewonly=True,
    )


# --- Agent Tracking ---

class AgentSession(Base):
    __tablename__ = "agent_sessions"

    id = Column(Integer, primary_key=True)
    agent_type = Column(String(50), nullable=False)  # "claude-code", "copilot", etc.
    model = Column(String(100), nullable=False)
    skill_version = Column(String(50))
    started_at = Column(DateTime, default=utcnow)
    ended_at = Column(DateTime)
    issues_processed = Column(Integer, default=0)
    builds_triggered = Column(Integer, default=0)
    status = Column(String(20), default="active")  # active, completed, failed
