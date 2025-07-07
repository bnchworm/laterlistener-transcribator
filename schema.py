from pydantic import BaseModel
import enum


class TaskStatus(enum.Enum):
    wait = 'WAIT'
    running = 'RUNNING'
    finished = 'FINISHED'


class TranscribeQuery(BaseModel):
    file_url: str
    file_name: str


class Task(BaseModel):
    id: str
    file_url: str
    file_name: str
    status: TaskStatus
