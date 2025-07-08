from fastapi import FastAPI
from dotenv import load_dotenv
from schema import *
from psdb_client import init_db_client, add_task, get_task_status, get_task
from contextlib import asynccontextmanager

from supabase_client import upload_file_to_supabase


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_dotenv()
    init_db_client()
    yield

app = FastAPI(lifespan=lifespan)


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
