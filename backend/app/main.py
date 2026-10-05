import os

import psycopg
from fastapi import FastAPI, HTTPException

app = FastAPI(title="Proyecto Pulsador", version="0.1.0")


def checkDatabaseConnection() -> dict[str, str]:
    try:
        with psycopg.connect(os.environ["DATABASE_URL"]) as connection:
            connection.execute("SELECT 1")
    except (KeyError, psycopg.Error) as exc:
        raise HTTPException(status_code=503, detail="Database is unavailable") from exc

    return {"status": "ok", "database": "connected"}


@app.get("/api/testdb")
def testEndpoint() -> dict[str, str]:
    return checkDatabaseConnection()

