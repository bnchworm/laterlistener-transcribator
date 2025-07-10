import base64
import json
import os
from typing import Optional


def file_to_base64_json(
    input_file_path: str,
    prompt: str,
    output_file_path: Optional[str] = None
) -> str:
    """
    Convert a file to base64 and save it as a JSON file in the specified format.
    
    Args:
        input_file_path: Path to the input file to be converted to base64
        prompt: Text prompt to include in the JSON
        output_file_path: Path where the JSON file will be saved. If None, a default name will be generated
                         based on the input file name.
    
    Returns:
        Path to the saved JSON file
    
    Raises:
        FileNotFoundError: If the input file doesn't exist
        IOError: If there's an error reading the input file or writing the output file
    """
    # Check if input file exists
    if not os.path.exists(input_file_path):
        raise FileNotFoundError(f"Input file not found: {input_file_path}")
    
    # Generate default output path if not provided
    if output_file_path is None:
        base_name = os.path.splitext(os.path.basename(input_file_path))[0]
        output_file_path = f"{base_name}_base64.json"
    
    try:
        # Read the input file as binary
        with open(input_file_path, 'rb') as file:
            file_content = file.read()
        
        # Convert to base64
        base64_content = base64.b64encode(file_content).decode('utf-8')
        
        # Create the JSON structure
        json_data = {
            "input": {
                "prompt": prompt,
                "file": base64_content
            }
        }
        
        # Write the JSON to the output file
        with open(output_file_path, 'w') as json_file:
            json.dump(json_data, json_file, indent=4)
        
        return output_file_path
    
    except Exception as e:
        raise IOError(f"Error processing file: {str(e)}")


# Example usage:
file_to_base64_json("rec.m4a", "Hey there!")
# print(f"JSON saved to: {output_path}")