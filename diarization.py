from typing import Dict, List
from pyannote.audio import Pipeline, Audio
import os


def diarize(audio_path: str) -> List[Dict]:
    audio = Audio(sample_rate=16000)
    diarization_token = os.getenv('DIARIZATION_TOKEN')
    
    waveform, sample_rate = audio(audio_path)
    pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization-3.1", 
                                        use_auth_token=diarization_token)
    diarization = pipeline({
        "waveform": waveform,
        "sample_rate": sample_rate
    })

    return [
        {"start": segment.start, "end": segment.end, "speaker": speaker}
        for segment, _, speaker in diarization.itertracks(yield_label=True)
    ]