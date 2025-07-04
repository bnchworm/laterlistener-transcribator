from pydub import AudioSegment
import os
import wave

def preprocess_audio(pfile):
    filename, ext = os.path.splitext(pfile)
    ofile = pfile if ext == '.wav' else f"{filename}.wav"

    audio = AudioSegment.from_file(pfile)
    audio.export(ofile, format="wav", parameters=["-ac", "1", "-ar", "16000"])
    
    with wave.open(ofile, 'rb') as audiofile:
        frame_rate = audiofile.getframerate()
        n_frames = audiofile.getnframes()
        duration = n_frames / float(frame_rate)
        
        return {
            'filename': ofile,
            'frame_rate': frame_rate,
            'n_frames': n_frames,
            'duration': duration
        }

path_to_file = "path"
result = preprocess_audio(path_to_file)
print(result)