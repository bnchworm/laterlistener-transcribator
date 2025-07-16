from pydub import AudioSegment
import os

def preprocess_audio(pfile):
    filename, ext = os.path.splitext(pfile)
    ofile = pfile if ext == '.wav' else f"{filename}.wav"
    if ext != ".wav":
        AudioSegment.from_file(pfile).export(ofile, format="wav")
        os.remove(pfile)
    return ofile
