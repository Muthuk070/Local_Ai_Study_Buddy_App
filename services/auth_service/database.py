import os
from dotenv import load_dotenv
import aiomysql
from fastapi import HTTPException
import logging
from contextlib import asynccontextmanager
load_dotenv()

DB_CONFIG = {
    "host": os.getenv("HOST"),
    "port": int(os.getenv("PORT") or 3306),
    "user": os.getenv("USER"),
    "password": os.getenv("PASSWORD"),
    # aiomysql accepts either “db” or “database”; make sure it’s not None/empty
    "db": os.getenv("DB") or os.getenv("DATABASE"),
}

if not DB_CONFIG["db"]:
    raise RuntimeError("database name not configured – set DB (or DATABASE) in .env")

@asynccontextmanager
async def get_connection_ctx():
    conn = None
    cursor = None
    dict_cursor = None
    try:
        conn = await aiomysql.connect(**DB_CONFIG)
        # ensure the database is selected (defensive in case env var was blank)
        await conn.select_db(DB_CONFIG["db"])

        cursor = await conn.cursor()
        dict_cursor = await conn.cursor(aiomysql.DictCursor)

        try:
            yield conn, cursor, dict_cursor
        finally:
            if cursor:
                await cursor.close()
            if dict_cursor:
                await dict_cursor.close()
            if conn:
                conn.close()

    except aiomysql.MySQLError as e:
        logging.error(f"MySQL error: {e}")
        raise HTTPException(status_code=500, detail="Database connection error...")


async def get_connection():
    # FastAPI dependency (async generator) that uses the async context manager
    async with get_connection_ctx() as resources:
        yield resources