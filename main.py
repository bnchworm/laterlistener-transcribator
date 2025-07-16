from dotenv import load_dotenv
from diarization import diarize
from preprocessor import preprocess_audio
from transcription import transcription
from aligner import align_speakers_with_text
from psdb_client import init_db_client, get_waiting_task, set_task_status, set_task_result_url
from urllib.request import urlretrieve
from schema import TaskStatus
import json
import os
from supabase_client import upload_file_to_supabase
import asyncio
import aiofiles.os

PATH_TO_AUDIO_FILES = 'audio_to_process'
PATH_TO_TRANSCRIPTIONS = 'transcriptions'

load_dotenv()
init_db_client()

async def main():
    while True:
        try:
            task = get_waiting_task()
            if task is None:
                await asyncio.sleep(0.5)
                continue

            if await asyncio.create_task(set_task_status(task.id, TaskStatus.running)) == 0:
                continue

            path_to_audio = os.path.join(PATH_TO_AUDIO_FILES, task.file_name)
            await asyncio.create_task(urlretrieve(task.file_url, path_to_audio))
            diarization_result = await asyncio.to_thread(diarize, path_to_audio)
            transcription_result = await asyncio.to_thread(transcription,path_to_audio)
            align_result = await asyncio.to_thread(align_speakers_with_text, transcription_result, diarization_result)

            base_file_name = task.id
            transcription_file_path = os.path.join(PATH_TO_TRANSCRIPTIONS, f'{base_file_name}.json')
            async with aiofiles.open(transcription_file_path, 'w', encoding='utf8') as f:
                await asyncio.create_task(json.dump(align_result, f, ensure_ascii=False))

            # Загружаем результат в Supabase и сохраняем ссылку
            public_url = await asyncio.create_task(upload_file_to_supabase(transcription_file_path, 'transcriptions', f'transcriptions/{base_file_name}.json', 'application/json'))
            await asyncio.create_task(set_task_result_url(task.id, public_url))
            await asyncio.create_task(set_task_status(task.id, TaskStatus.finished))
            
            # Удаляем временные файлы
            try:
                aiofiles.os.remove(path_to_audio)
                aiofiles.os.remove(transcription_file_path)
            except OSError as e:
                print(f"Ошибка при удалении файлов: {e}")
        except RuntimeWarning as e:
            raise RuntimeWarning(f"{str(e)}")

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Воркер остановлен")
    except Exception as e:
        print(f"Критическая ошибка: {e}")
    finally:
        print("Очистка ресурсов завершена")