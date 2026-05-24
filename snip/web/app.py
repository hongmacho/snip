from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
import os
from snip.repository import SnippetRepository
from snip.models import Snippet

app = FastAPI(title="snip web", version="1.0.0")

# static files 마운트
static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

repo = SnippetRepository()

class SnippetCreate(BaseModel):
    title: str
    language: str = "text"
    tags: str = ""
    description: str = ""
    code: str

class SnippetUpdate(BaseModel):
    title: Optional[str] = None
    language: Optional[str] = None
    tags: Optional[str] = None
    description: Optional[str] = None
    code: Optional[str] = None

@app.get("/")
def index():
    return FileResponse(os.path.join(static_dir, "index.html"))

@app.get("/api/snippets")
def list_snippets(language: Optional[str] = None, tag: Optional[str] = None):
    snippets = repo.get_all(language=language, tag=tag)
    return [s.__dict__ for s in snippets]

@app.post("/api/snippets", status_code=201)
def create_snippet(data: SnippetCreate):
    snippet = Snippet(title=data.title, language=data.language, tags=data.tags,
                      description=data.description, code=data.code)
    created = repo.create(snippet)
    return created.__dict__

@app.get("/api/snippets/search")
def search_snippets(q: str = Query(..., min_length=1)):
    snippets = repo.search(q)
    return [s.__dict__ for s in snippets]

@app.get("/api/snippets/{snippet_id}")
def get_snippet(snippet_id: int):
    snippet = repo.get_by_id(snippet_id)
    if not snippet:
        raise HTTPException(status_code=404, detail="Snippet not found")
    return snippet.__dict__

@app.put("/api/snippets/{snippet_id}")
def update_snippet(snippet_id: int, data: SnippetUpdate):
    updates = {k: v for k, v in data.dict().items() if v is not None}
    snippet = repo.update(snippet_id, **updates)
    if not snippet:
        raise HTTPException(status_code=404, detail="Snippet not found")
    return snippet.__dict__

@app.delete("/api/snippets/{snippet_id}")
def delete_snippet(snippet_id: int):
    deleted = repo.delete(snippet_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Snippet not found")
    return {"ok": True}

@app.get("/api/stats")
def get_stats():
    return repo.get_stats()
