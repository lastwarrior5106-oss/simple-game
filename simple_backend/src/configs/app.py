from dotenv import load_dotenv
from os import environ as env

load_dotenv()

class AppConfig:
    POSTGRES_USER = env.get("POSTGRES_USER")
    POSTGRES_PASSWORD = env.get("POSTGRES_PASSWORD")
    POSTGRES_SERVER = env.get("POSTGRES_SERVER", "127.0.0.1")
    POSTGRES_PORT = env.get("POSTGRES_PORT", "5432")
    POSTGRES_DB = env.get("POSTGRES_DB", "row_match")

    DATABASE_URL = (
        f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}"
        f"@{POSTGRES_SERVER}:{POSTGRES_PORT}/{POSTGRES_DB}"
    )

    SECRET_KEY = env.get("SECRET_KEY", "secret")
    HASHING_ALGORITHM = env.get("HASHING_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES = int(env.get("ACCESS_TOKEN_EXPIRE_MINUTES", 60))