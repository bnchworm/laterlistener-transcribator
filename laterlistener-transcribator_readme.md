# Модуль обработки аудио

## Цель
Модуль предназначен для обработки загруженных аудиофайлов, их расшифровки и диаризации с возвращением структурированного текста, размеченного по спикерам.

## Возможная структура модуля

```
laterlistener-transcribator/
├── main.py               # Точка входа
├── preprocessor.py       # Подготовка аудио
├── transcription.py      # Whisper
├── diarization.py        # pyannote
├── aligner.py            # Сопоставление текста и спикеров
├── schema.py             # Pydantic-схемы
├── utils.py              # Вспомогательные функции
```

---

## Список задач

### 1. `preprocessor.py`: Подготовка аудио
- Поддержка форматов: `mp3`, `m4a`, `wav`, `ogg`, `webm`.
- Конвертация в WAV 16kHz mono.
- Валидация по длине и размеру.

```python
def preprocess_audio(input_path: str) -> str:
    """
    Конвертирует файл в .wav 16kHz mono.
    Возвращает путь к подготовленному файлу.
    """
```

---

### 2. `transcription.py`: Транскрипция (Whisper)
- Вывод с сегментами, таймкодами и текстом.

```python
def transcribe(audio_path: str, model_size: str = "medium") -> List[Dict]:
    """
    Возвращает список сегментов:
    [{"start": 0.0, "end": 3.5, "text": "..."}]
    """
```

---

### 3. `diarization.py`: Диаризация (pyannote)
- Получение временных интервалов с указанием спикеров.

```python
def diarize(audio_path: str) -> List[Dict]:
    """
    Возвращает список сегментов:
    [{"start": 0.0, "end": 2.5, "speaker": "SPEAKER_00"}]
    """
```

---

### 4. `aligner.py`: Сопоставление спикеров
- Сопоставление текста и интервалов спикеров по таймкодам.
- Объединение сегментов одного спикера.

```python
def assign_speakers(transcript: List[Dict], diarization: List[Dict]) -> List[Dict]:
    """
    Возвращает список сегментов:
    [{"start": ..., "end": ..., "speaker": ..., "text": ...}]
    """
```

---

### 5. `main.py`: Точка входа
- Композиция всех шагов: `preprocess → transcribe → diarize → align`.

```python
def process_audio(input_path: str) -> List[Dict]:
    """
    Возвращает расшифровку с привязкой к спикерам.
    """
```

---

### 6. `schema.py`: Схемы данных (Pydantic)
- `TranscriptSegment`
- `SpeakerSegment`
- `ProcessedTranscript`

---

### 7. `utils.py`: Вспомогательные функции
- Логгирование
- Проверка форматов
- Идентификация и хэширование файлов

---

## Пример финального вывода

```json
[
  {
    "start": 0.0,
    "end": 5.3,
    "speaker": "SPEAKER_01",
    "text": "Привет, как у тебя дела?"
  },
  {
    "start": 5.4,
    "end": 10.2,
    "speaker": "SPEAKER_02",
    "text": "Все отлично, спасибо! А ты как?"
  }
]
```

## Возможное API
### `POST /transcribe`

Запуск задачи транскрибации.

### Запрос:
| Поле       | Тип       | Описание                         |
|------------|------------|----------------------------------|
| `audio`    | file       | Аудиофайл (.mp3, .m4a, .wav и др) |
| `language` | string     | (опционально) язык речи (`"ru"`, `"en"`, `"auto"`) |
| `model`    | string     | (опционально) размер модели Whisper: `tiny`, `base`, `medium`, `large` |
| `callback_url` | string | (опционально) URL для webhook-уведомления по завершении |

### Пример cURL:
```bash
curl -X POST https://transcriber.laterlistener.ai/transcribe -F "audio=@recording.mp3" -F "language=ru" -F "callback_url=https://yourdomain.com/webhook"
```

### Ответ:
```json
{
  "task_id": "a3e90d51-d2b5-4c1b-9b1e-01eae12f23d2",
  "status": "queued"
}
```

---

## `GET /status/{task_id}`

Проверка статуса задачи.

### Ответ:
```json
{
  "task_id": "a3e90d51-d2b5-4c1b-9b1e-01eae12f23d2",
  "status": "in_progress",  // or "completed", "failed"
  "progress": 0.73
}
```

---

## `GET /result/{task_id}`

Получение результата транскрипции.

### Ответ:
```json
{
  "task_id": "a3e90d51-d2b5-4c1b-9b1e-01eae12f23d2",
  "language": "ru",
  "segments": [
    {
      "start": 0.0,
      "end": 4.1,
      "speaker": "SPEAKER_01",
      "text": "Привет, как у тебя дела?"
    },
    {
      "start": 4.2,
      "end": 7.8,
      "speaker": "SPEAKER_02",
      "text": "Всё отлично, спасибо."
    }
  ]
}
```

## Возможные ошибки

| Код | Ошибка                  | Описание                                      |
|-----|--------------------------|-----------------------------------------------|
| 400 | `InvalidFileFormat`     | Файл не поддерживается                        |
| 413 | `FileTooLarge`          | Превышен лимит размера                        |
| 422 | `ValidationError`       | Некорректные параметры                        |
| 500 | `ProcessingError`       | Ошибка внутри модуля                          |

---

## Внедрение очереди задач в модуль транскрибации

## Что нужно

1. Redis или RabbitMQ — брокер сообщений
2. Celery — менеджер очередей
3. Воркер — исполняет задачи транскрибации
4. (Опционально) Мониторинг (например, Flower)

## Архитектура

```
Client → FastAPI API
           |
           |  (Celery task)
           ↓
     [ Redis / RabbitMQ ]  ← очередь задач
           ↓
        Celery worker
           ↓
   Транскрибация, диаризация
           ↓
     Хранение результата
           ↓
        Webhook / API
```