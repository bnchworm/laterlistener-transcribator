from dotenv import load_dotenv
from diarization import diarize
from transcription import transcription
from aligner import align_speakers_with_text
from psdb_client import init_db_client, get_waiting_task, set_task_status
from urllib.request import urlretrieve
from schema import TaskStatus
import time
import json


PATH_TO_AUDIO_FILES = 'audio_to_process'
PATH_TO_TRANSCRIPTIONS = 'transcriptions'

load_dotenv()
init_db_client()

while True:
    task = get_waiting_task()
    if task is None:
        time.sleep(0.5)
        continue

    if set_task_status(task.id, TaskStatus.run) == 0:
        continue

    path_to_audio = f'{PATH_TO_AUDIO_FILES}/{task.file_name}'
    urlretrieve(task.file_url, path_to_audio)
    diarization_result = diarize(path_to_audio)
    transcription_result = transcription(path_to_audio)
    align_result = align_speakers_with_text(transcription_result, diarization_result)

    base_file_name = task.file_name[0:task.file_name.rfind('.')]
    with open(f'{PATH_TO_TRANSCRIPTIONS}/{base_file_name}.json', 'w', encoding='utf8') as f:
        json.dump(align_result, f, ensure_ascii=False)
