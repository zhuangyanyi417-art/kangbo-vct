import os
from dotenv import load_dotenv

load_dotenv()

RIOT_API_KEY = os.getenv("RIOT_API_KEY", "")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///../data/haojiao.db")
PROJECT_NAME = "无畏契约电竞平台"
DEBUG = True
HOST = "0.0.0.0"
PORT = 8000
