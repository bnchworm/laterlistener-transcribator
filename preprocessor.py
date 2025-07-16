from pydub import AudioSegment
import os

def preprocess_audio(pfile):
    filename, ext = os.path.splitext(pfile)
    ofile = pfile if ext == '.wav' else f"{filename}.wav"
    if ext != ".wav":
        AudioSegment.from_file(pfile).export(ofile, format="wav")

path_to_file = "path"
preprocess_audio(path_to_file)