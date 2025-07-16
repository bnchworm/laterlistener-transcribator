from pydantic import BaseModel
import enum


class TaskStatus(enum.Enum):
    wait = 'WAIT'
    running = 'RUNNING'
    finished = 'FINISHED'


class TranscribeQuery(BaseModel):
    file_url: str
    file_name: str
    telegram_id: int


class Task(BaseModel):
    id: str
    file_url: str
    file_name: str
    status: TaskStatus
    result_url: str | None = None
    telegram_id: int

class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class OneTimeTokenQuery(BaseModel):
    telegram_id: int
