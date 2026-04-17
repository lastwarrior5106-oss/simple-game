import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.routers import auth_route, user_route, team_route, ai_route
from src.database import init_db
from mcp.server.fastmcp import FastMCP
from mcp_server.tools import register_user_tools, register_team_tools
from seed import seed_database
from src.middlewares import RequestLoggerMiddleware, GlobalExceptionHandlerMiddleware

app = FastAPI(title="Simple Game API")

app.add_middleware(RequestLoggerMiddleware)
app.add_middleware(GlobalExceptionHandlerMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5176",
        "http://127.0.0.1:5176",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

mcp = FastMCP(name="simple-game-mcp")
register_user_tools(mcp)
register_team_tools(mcp)
app.mount("/mcp", mcp.sse_app())

app.include_router(auth_route.router, prefix=auth_route.prefix)
app.include_router(user_route.router, prefix=user_route.prefix)
app.include_router(team_route.router, prefix=team_route.prefix)
app.include_router(ai_route.router, prefix=ai_route.prefix)


@app.on_event("startup")
async def on_startup():
    await init_db()

    if os.getenv("SEED_DB", "false").lower() == "true":
        await seed_database()


@app.get("/")
async def home():
    return {"status": "ok", "message": "Row Match API"}