from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from pathlib import Path

from app.config import PROJECT_NAME, DEBUG
from app.database import init_db
from app.routers.teams import router as teams_router
from app.routers.players import router as players_router
from app.routers.chat import router as chat_router

TEMPLATES_DIR = Path("app/templates")


def render_template(name: str) -> str:
    return (TEMPLATES_DIR / name).read_text(encoding="utf-8")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(title=PROJECT_NAME, debug=DEBUG, lifespan=lifespan)

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(teams_router)
app.include_router(players_router)
app.include_router(chat_router)


@app.get("/", response_class=HTMLResponse)
async def index():
    return render_template("index.html")


@app.get("/teams", response_class=HTMLResponse)
async def teams_page():
    return render_template("teams/list.html")


@app.get("/teams/{team_id}", response_class=HTMLResponse)
async def team_detail_page(team_id: int):
    html = render_template("teams/detail.html")
    from fastapi.responses import HTMLResponse as HR
    return HR(content=html, media_type="text/html")


@app.get("/players", response_class=HTMLResponse)
async def players_page():
    return render_template("players/list.html")


@app.get("/players/{player_id}", response_class=HTMLResponse)
async def player_detail_page(player_id: int):
    html = render_template("players/detail.html")
    from fastapi.responses import HTMLResponse as HR
    return HR(content=html, media_type="text/html")

@app.get("/chat", response_class=HTMLResponse)
async def chat_page():
    return render_template("chat/index.html")
