import json
import re
from typing import Union

def clean_json_string(json_str: str) -> str:
        """
        Cleans the input string to make it more JSON-compliant and extracts the JSON portion.
        """
        # Strip leading/trailing whitespace and artifacts
        json_str = json_str.strip()
        
        # Extract JSON portion using regex
        json_pattern = r'({.*?}|\[.*?\])'  # Matches JSON objects ({}) or arrays ([])
        match = re.search(json_pattern, json_str, re.DOTALL)
        
        if match:
            return match.group(0)  # Return the matched JSON portion
        
        # If no valid JSON is found, return the string as-is (will fail during parsing)
        return json_str

def parse_json(json_str: str) -> Union[dict, list, None]:
    """
    Parses a JSON string into a Python dictionary or list, with robust handling for edge cases,
    including cleaning and extracting JSON from additional text.
    
    Args:
        json_str (str): A JSON-formatted string or text containing JSON.
    
    Returns:
        Union[dict, list, None]: Parsed JSON object (dict or list) or None if parsing fails.
    
    Raises:
        ValueError: If the input cannot be parsed into valid JSON after cleanup.
    """
    try:
        # Attempt to parse directly
        return json.loads(json_str)
    except json.JSONDecodeError:
        try:
            # Try cleaning the string and parsing again
            cleaned_json = clean_json_string(json_str)
            return json.loads(cleaned_json)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON string after cleanup: {e}") from e
    except TypeError as e:
        raise ValueError(f"Input must be a string: {e}") from e
    
def extract_action_and_arguments(input_string: str):
    """
    Extracts the action and arguments from the input string.
    
    Args:
        input_string (str): A string in the format 'action(arg1, arg2, ...)'.
    
    Returns:
        tuple: A tuple containing the action and a list of arguments.
    
    Raises:
        ValueError: If the input string does not match the expected format.
    """
    # Remove any ' or " characters from the input string
    input_string = input_string.replace("'", "").replace("\"", "")
    
    # Define the regex pattern for extracting action and arguments
    pattern = r'(\w+)\((.*?)\)'
    match = re.match(pattern, input_string)
    
    if match:
        action = match.group(1)  # Extract the action
        arguments = match.group(2).split(',')  # Extract the arguments and split by comma
        arguments = [arg.strip() for arg in arguments]  # Remove any leading/trailing whitespace
        return action, arguments
    else:
        raise ValueError("Input string does not match the expected format 'action(arg1, arg2, ...)'.")
