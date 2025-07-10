import runpod
import base64
from rp_diarization import process_audio_bytes
import traceback


def handler(event):
    """
    This function processes incoming requests to your Serverless endpoint.
    
    Args:
        event (dict): Contains the input data and request metadata
        
    Returns:
        Any: The result to be returned to the client
    """
    
    # Extract input data
    print(f"Worker Start")
    input = event['input']
    
    # Extract key from input and decode from base64
    input_file = input.get('file')
    if input_file:
        try:
            # Decode base64 to binary
            binary_data = base64.b64decode(input_file)
            rttm = process_audio_bytes(binary_data)

            return {
                "rttm": rttm
            }
            
        except Exception as e:
            return {
                "error": traceback.format_exc()
            }
    else:
        raise Exception("No file provided in the input")

# Start the Serverless function when the script is run
if __name__ == '__main__':
    runpod.serverless.start({'handler': handler })