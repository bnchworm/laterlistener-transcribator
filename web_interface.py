from fastapi import FastAPI, Response, HTTPException, Depends
from dotenv import load_dotenv
from schema import *
from psdb_client import init_db_client, add_task, get_task_status, get_task
from contextlib import asynccontextmanager

from supabase_client import upload_file_to_supabase

import os
from supabase import create_client, Client

from auth.hash import verify_password
from auth.security import create_access_token, access_token_required

@asynccontextmanager
async def lifespan(app: FastAPI):
    load_dotenv()
    init_db_client()
    yield
load_dotenv()
app = FastAPI(lifespan=lifespan)
supabase: Client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
JWT_ACCESS_COOKIE_NAME = os.getenv("JWT_ACCESS_COOKIE_NAME", "access_token")

@app.post('/transcribe')
async def start_transcribe(query: TranscribeQuery):
    return add_task(query)


@app.get('/status/{task_id}')
async def get_transcribe_status(task_id: str):
    return get_task_status(task_id)


@app.get('/result/{task_id}')
async def get_transcribe_result(task_id: str):
    task = get_task(task_id)
    if not task:
        return {"error": "Task not found"}
    if task.status != TaskStatus.finished:
        return {"error": "Task not finished"}
    return {"result_url": task.result_url}

@app.post("/login")
def login(creds: UserLogin, response: Response):
    result = (
        supabase
        .table("user")
        .select("id, password")
        .eq("username", creds.username)
        .limit(1)
        .execute()
    )

    if not result.data:
        raise HTTPException(status_code=401, detail="User not found")

    user = result.data[0]
    if not verify_password(creds.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid password")

    token = create_access_token(uid=str(user["id"]))
    response.set_cookie(key=JWT_ACCESS_COOKIE_NAME, value=token)
    return {"access_token": token}

@app.get("/protected")
def protected(user_id: str = Depends(access_token_required)):
    return {"message": f"Hello, user {user_id}!"}