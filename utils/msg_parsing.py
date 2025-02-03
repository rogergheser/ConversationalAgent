import logging
import json
import re
from typing import Union

def clean_json_string(json_str: str) -> str:
        """
        Cleans the input string to make it more JSON-compliant and extracts the JSON portion.
        """
        # Strip leading/trailing whitespace and artifacts
        json_str = json_str.strip()
        
        json_str = json_str.split('```')[1].rsplit('```')[0]
        if json_str.startswith('json'):
            json_str = json_str[4:]
        
        return json_str

def parse_json(json_str: str, with_list:bool = False, replace_quotes = True) -> Union[dict, list, None]:
    """
    Parses a JSON string into a Python dictionary or list, with robust handling for edge cases,
    including cleaning and extracting JSON from additional text.
    
    Args:
        json_str (str): A JSON-formatted string or text containing JSON.
        with_list (bool): If True, the input is treated as a list of JSON objects.
        replace_quotes (bool): If True, single quotes are replaced with double quotes.
    
    Returns:
        Union[dict, list, None]: Parsed JSON object (dict or list) or None if parsing fails.
    
    Raises:
        ValueError: If the input cannot be parsed into valid JSON after cleanup.
    """
    if json_str.startswith('```') and json_str.endswith('```'):
        json_str = json_str[3:-3]
        if json_str.startswith('json'):
            json_str = json_str[4:]
    
    if  not with_list and json_str[0] == '[' and json_str[-1] == ']':
        json_str = json_str[1:-1]
    
    if replace_quotes:
        json_str = json_str.replace('\'', '\"')
    
    try:
        # Attempt to parse directly
        return json.loads(json_str)
    except json.JSONDecodeError:
        try:
            # Try cleaning the string and parsing again
            cleaned_json = clean_json_string(json_str)
            return json.loads(cleaned_json)
        except json.JSONDecodeError as e:
            try:
                # Try cleaning the string and parsing again
                cleaned_json = cleaned_json.split('{', 1)[1].rsplit('}', 1)[0]
                logging.error(f"Cleaned JSON: {cleaned_json}")
                return json.loads('{'+cleaned_json+'}')
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON string after cleanup: {e}\n{cleaned_json}") from e
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
    ret = parse_json(input_string)
    action, argument = ret['action'], ret['argument']
    
    return action, argument
