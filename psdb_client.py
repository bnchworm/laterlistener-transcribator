import psycopg2
from psycopg2.extras import RealDictCursor
from schema import *
import os

TASKS_TABLE = 'task'
connection = None


def init_db_client():
    global connection
    try:
        connection = psycopg2.connect(
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT"),
            dbname=os.getenv("DB_DBNAME"),
            cursor_factory=RealDictCursor
        )

        cursor = connection.cursor()
    except Exception as e:
        print(f"Failed to connect: {e}")


def add_task(query: TranscribeQuery):
    with connection.cursor() as cursor:
        cursor.execute(f'INSERT INTO task(id, file_url, file_name, status) VALUES (uuid_generate_v4(), \'{query.file_url}\', \'{query.file_name}\', \'WAIT\') RETURNING id;')
        connection.commit()
        return cursor.fetchone()


def get_task_status(task_id: str):
    with connection.cursor() as cursor:
        cursor.execute(f'SELECT status FROM task WHERE id = \'{task_id}\';')
        return cursor.fetchone()


def get_waiting_task():
    with connection.cursor() as cursor:
        cursor.execute(f'SELECT * FROM task WHERE status = \'WAIT\'')
        query_result = cursor.fetchone()
        if query_result:
            return Task(**query_result)

        return query_result


def set_task_status(task_id: str, status: TaskStatus):
    with connection.cursor() as cursor:
        cursor.execute(f'UPDATE task SET status = \'{status.value}\' WHERE id = \'{task_id}\'')
        connection.commit()
        return cursor.rowcount
