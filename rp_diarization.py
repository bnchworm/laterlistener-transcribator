from dotenv import load_dotenv
import os
import subprocess
import pathlib
import torch
import io
import tempfile

def process_audio_bytes(audio_bytes):
    """
    Process audio bytes through speaker diarization pipeline.
    
    Args:
        audio_bytes (bytes): Raw audio file bytes
        
    Returns:
        str: Speaker diarization output in RTTM format
    """
    # Load environment variables
    load_dotenv('.rp.env')
    hf_token = os.getenv("HF_TOKEN")
    
    # if not hf_token:
    #     raise ValueError("HF_TOKEN environment variable not set")
    
    # Check if CUDA is available
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")
    
    # Instantiate the pipeline
    from pyannote.audio import Pipeline
    pipeline = Pipeline.from_pretrained(
        "pyannote/speaker-diarization-3.1",
        use_auth_token=hf_token)
    
    # Move pipeline to GPU if available
    pipeline.to(torch.device(device))
    
    # Create temporary files for processing
    temp_input = None
    wav_file = None
    
    try:
        # Save input bytes to a temporary file
        temp_input = tempfile.NamedTemporaryFile(delete=False, suffix='.tmp')
        temp_input.write(audio_bytes)
        temp_input.close()
        
        # Create a temporary WAV file
        wav_fd, wav_path = tempfile.mkstemp(suffix='.wav')
        os.close(wav_fd)
        
        # Convert to WAV format using ffmpeg with -y flag to prevent prompts
        subprocess.run([
            'ffmpeg', '-y', '-i', temp_input.name, '-acodec', 'pcm_s16le', 
            '-ar', '16000', '-ac', '1', wav_path
        ], check=True)
        print(f"Converted audio to WAV format")
        
        # Run the pipeline on the audio file
        diarization = pipeline(wav_path)
        
        # Get the diarization output as string
        output_string = io.StringIO()
        diarization.write_rttm(output_string)
        result = output_string.getvalue()
        
        return result
    
    except subprocess.CalledProcessError as e:
        print(f"Error converting audio: {e}")
        raise RuntimeError(f"Failed to process audio: {e}")
    
    finally:
        # Clean up temporary files
        for temp_file in [temp_input.name if temp_input else None, wav_path if 'wav_path' in locals() else None]:
            if temp_file and os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                    print(f"Removed temporary file: {temp_file}")
                except OSError as e:
                    print(f"Error removing temporary file {temp_file}: {e}")





# Example usage:
if __name__ == "__main__":
    # Example of how to use the function
    import sys
    
    if len(sys.argv) > 1:
        # Use file provided as command line argument
        input_file = sys.argv[1]
        print(f"Processing file: {input_file}")
        with open(input_file, "rb") as f:
            audio_bytes = f.read()
    else:
        # Use default file if no argument provided
        default_file = "rec.m4a"
        print(f"No input file specified, using default: {default_file}")
        try:
            with open(default_file, "rb") as f:
                audio_bytes = f.read()
        except FileNotFoundError:
            print(f"Default file {default_file} not found. Please provide an audio file path.")
            sys.exit(1)
    
    result = process_audio_bytes(audio_bytes)
    
    # Save the result to a file
    output_file = "audio.rttm"
    with open(output_file, "w") as rttm:
        rttm.write(result)
    print(f"Results written to {output_file}")