# app/utils/json_utils.py

import json
import re
from typing import Any, Dict, List
import logging

logger = logging.getLogger(__name__)

def safe_parse_json(content: Any) -> Dict[str, Any]:
    """
    Safely parse JSON content, whether it's a string or already a dict.
    """
    if isinstance(content, dict):
        return content
    if isinstance(content, str):
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse content as JSON. Error: {str(e)}")
            logger.error(f"Content: {content}")
            # Attempt to extract key information if JSON parsing fails
            return extract_info_from_text(content)
    logger.error(f"Unexpected content type: {type(content)}")
    return {}

def extract_info_from_text(text: str) -> Dict[str, Any]:
    """
    Attempt to extract key information from text if JSON parsing fails.
    """
    result = {}

    # Define patterns for different types of fields
    patterns = {
        'string': r'"(\w+)":\s*"([^"]*)"',
        'boolean': r'"(\w+)":\s*(true|false)',
        'number': r'"(\w+)":\s*(-?\d+(?:\.\d+)?)',
        'list': r'"(\w+)":\s*(\[.*?\])',
        'nested_dict': r'"(\w+)":\s*(\{.*?\})'
    }

    # Extract information based on patterns
    for pattern_type, pattern in patterns.items():
        matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)
        for match in matches:
            key, value = match
            if pattern_type == 'boolean':
                result[key] = value.lower() == 'true'
            elif pattern_type == 'number':
                result[key] = float(value) if '.' in value else int(value)
            elif pattern_type in ['list', 'nested_dict']:
                try:
                    result[key] = json.loads(value)
                except json.JSONDecodeError:
                    result[key] = value  # Store as string if parsing fails
            else:
                result[key] = value

    return result

def extract_specific_info(parsed_data: Dict[str, Any], node_type: str) -> Dict[str, Any]:
    """
    Extract specific information based on the node type.
    """
    if node_type == "analyzer":
        return {
            "is_query_relevant": parsed_data.get("is_query_relevant", False),
            "analyzed_query": parsed_data.get("analyzed_query", ""),
            "selected_tables": parsed_data.get("selected_tables", []),
            "explanation": parsed_data.get("explanation", "")
        }
    elif node_type == "sql_generator":
        return {
            "sql_query": parsed_data.get("sql_query", ""),
            "explanation": parsed_data.get("explanation", "")
        }
    elif node_type == "sql_validator":
        return {
            "is_sql_valid": parsed_data.get("is_sql_valid", False),
            "issues": parsed_data.get("issues", []),
            "suggested_fix": parsed_data.get("suggested_fix", "")
        }
    elif node_type == "result_evaluator":
        return {
            "is_result_relevant": parsed_data.get("is_result_relevant", False),
            "explanation": parsed_data.get("explanation", ""),
            "requires_visualization": parsed_data.get("requires_visualization", False),
            "summary": parsed_data.get("summary", "")
        }
    else:
        return parsed_data  # Return all data if node type is not recognized

# Example usage in a node's processing function:
def process_node_output(content: Any, node_type: str) -> Dict[str, Any]:
    parsed_data = safe_parse_json(content)
    return extract_specific_info(parsed_data, node_type)




########################
# Helper function to convert the string json format to json
import json
import re


def convert_to_json(content):
    # Strip leading/trailing whitespace
    content = content.strip()

    # Check if the content is already valid JSON
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass  # Not valid JSON, continue with conversion

    # Remove ```json and ``` if present
    content = re.sub(r'^```json\s*|\s*```$', '', content, flags=re.MULTILINE)

    # Remove any remaining ``` at the start or end
    content = re.sub(r'^```\s*|\s*```$', '', content, flags=re.MULTILINE)

    # Attempt to parse the cleaned content as JSON
    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
        print(f"Problematic content:\n{content}")

        # If parsing fails, attempt to create a dict from key-value pairs
        result = {}
        for line in content.split('\n'):
            match = re.match(r'^\s*"?([^"]+)"?\s*:\s*(.+)$', line)
            if match:
                key, value = match.groups()
                key = key.strip('"')
                value = value.strip().strip(',').strip('"')
                if value.lower() == 'true':
                    value = True
                elif value.lower() == 'false':
                    value = False
                elif value.replace('.', '').isdigit():
                    value = float(value) if '.' in value else int(value)
                result[key] = value

        if result:
            return result
        else:
            raise ValueError("Unable to parse content into JSON or key-value pairs")


# Example usage:
# json_data = convert_to_json(your_model_output)

########################