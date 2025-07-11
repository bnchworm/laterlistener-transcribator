from dotenv import load_dotenv
from diarization import diarize
from transcription import transcription
from aligner import align_speakers_with_text
from psdb_client import init_db_client, get_waiting_task, set_task_status, set_task_result_url
from urllib.request import urlretrieve
from schema import TaskStatus
import time
import json
import os
from supabase_client import upload_file_to_supabase


PATH_TO_AUDIO_FILES = 'audio_to_process'
PATH_TO_TRANSCRIPTIONS = 'transcriptions'

load_dotenv()
init_db_client()

while True:
    task = get_waiting_task()
    if task is None:
        time.sleep(0.5)
        continue

    if set_task_status(task.id, TaskStatus.running) == 0:
        continue

    path_to_audio = os.path.join(PATH_TO_AUDIO_FILES, task.file_name)
    urlretrieve(task.file_url, path_to_audio)
    diarization_result = diarize(path_to_audio)
    transcription_result = transcription(path_to_audio)
    align_result = align_speakers_with_text(transcription_result, diarization_result)

    base_file_name = task.id
    transcription_file_path = os.path.join(PATH_TO_TRANSCRIPTIONS, f'{base_file_name}.json')
    with open(transcription_file_path, 'w', encoding='utf8') as f:
        json.dump(align_result, f, ensure_ascii=False)

    # Загружаем результат в Supabase и сохраняем ссылку
    public_url = upload_file_to_supabase(transcription_file_path, 'transcriptions', f'transcriptions/{base_file_name}.json', 'application/json')
    set_task_result_url(task.id, public_url)
    set_task_status(task.id, TaskStatus.finished)
    
    # Удаляем временные файлы
    try:
        os.remove(path_to_audio)
        os.remove(transcription_file_path)
    except OSError as e:
        print(f"Ошибка при удалении файлов: {e}")
