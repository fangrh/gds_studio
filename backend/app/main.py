from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db import run_migrations
from app.gds.router import router as gds_router
from app.issues.router import issue_router, comment_router
from app.wiki.router import router as wiki_router
from app.agent.router import router as agent_router
from app.projects.router import router as projects_router
from app.sync.router import router as sync_router

app = FastAPI(title="GDS Collab Platform", version="0.2.0")


@app.on_event("startup")
def startup():
    run_migrations()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(gds_router)
app.include_router(issue_router)
app.include_router(comment_router)
app.include_router(wiki_router)
app.include_router(agent_router)
app.include_router(projects_router)
app.include_router(sync_router)


@app.get("/api/health")
async def health():
    return {"status": "ok"}
