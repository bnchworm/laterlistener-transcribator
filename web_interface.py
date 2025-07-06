from fastapi import FastAPI
from dotenv import load_dotenv
from schema import *
from psdb_client import init_db_client, add_task, get_task_status


app = FastAPI()


@app.on_event("startup")
def startup_event():
    load_dotenv()
    init_db_client()


@app.post('/transcribe')
async def start_transcribe(query: TranscribeQuery):
    return add_task(query)


@app.get('/status/{task_id}')
async def get_transcribe_status(task_id: str):
    return get_task_status(task_id)
