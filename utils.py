import os
import logging
import hashlib
import wave
from typing import Optional

SUPPORTED_AUDIO_FORMATS = (".mp3", ".m4a", ".wav", ".ogg", ".webm")


LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True) 


def get_logger(name: str = "general") -> logging.Logger:
    logger = logging.getLogger(f"transcriber.{name}")
    if logger.handlers:
        return logger 

    logger.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s] - %(message)s"
    )


    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

 
    log_file = os.path.join(LOG_DIR, f"{name}.log")
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    logger.propagate = False
    return logger

def is_supported_audio_file(file_path: str) -> bool:
    return file_path.lower().endswith(SUPPORTED_AUDIO_FORMATS)


def get_file_size_mb(file_path: str) -> float:
    size_bytes = os.path.getsize(file_path)
    return round(size_bytes / (1024 * 1024), 2)


def get_audio_duration_wav(file_path: str) -> Optional[float]:
    try:
        with wave.open(file_path, "rb") as wf:
            frames = wf.getnframes()
            rate = wf.getframerate()
            duration = frames / float(rate)
            return round(duration, 2)
    except Exception as e:
        logger = get_logger("utils")
        logger.error(f"Ошибка при получении длительности файла: {e}")
        return None


def get_file_hash(file_path: str) -> str:
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def safe_remove(file_path: str):
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            get_logger("utils").info(f"Удалён временный файл: {file_path}")
    except Exception as e:
        get_logger("utils").warning(f"Не удалось удалить файл: {file_path} — {e}")
