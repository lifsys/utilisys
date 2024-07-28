"""
Provides utility functions for processing text, files, and data.
"""
from email import policy
from email.parser import BytesParser
from typing import Optional
from intelisys import get_completion_api
import phonenumbers
import logging
import re
import os
import json
import pandas as pd
import redis.asyncio as redis
from fuzzywuzzy import fuzz
import requests
from bs4 import BeautifulSoup
import urllib3
from onepasswordconnectsdk import new_client_from_environment
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from sqlalchemy import create_engine

def get_api(item: str, key_name: str, vault: str = "API") -> str:
    """
    Retrieve an API key from a 1Password vault.

    Args:
        item (str): The name of the item in the 1Password vault.
        key_name (str): The name of the key within the item.
        vault (str, optional): The name of the vault. Defaults to "API".

    Returns:
        str: The value of the requested key.

    Raises:
        Exception: If there's an error connecting to 1Password or retrieving the key.
    """
    try:
        client = new_client_from_environment()
        item = client.get_item(item, vault)
        for field in item.fields:
            if field.label == key_name:
                return field.value
        raise ValueError(f"Key '{key_name}' not found in item '{item}'")
    except Exception as e:
        raise Exception(f"1Password Connect Error: {e}")

def standardize_phone_number(phone: str, default_country: str = "US") -> str:
    """
    Standardize a phone number by parsing it and formatting it in international format.

    This function attempts to parse the given phone number and format it
    according to the international standard. If parsing fails, it returns
    the original input.

    Args:
        phone (str): The phone number to be standardized.
        default_country (str, optional): The default country code to use for parsing. 
                                         Defaults to "US".

    Returns:
        str: The standardized phone number in international format, 
             or the original phone number if parsing fails.

    Example:
        >>> standardize_phone_number("(123) 456-7890")
        '+1 123-456-7890'
    """
    try:
        # Parse phone number with a default country code
        phone_number = phonenumbers.parse(phone, default_country)
        # Format phone number in international format
        return phonenumbers.format_number(
            phone_number, phonenumbers.PhoneNumberFormat.INTERNATIONAL
        )
    except phonenumbers.NumberParseException:
        # Return the original phone number if parsing fails
        return phone


def flatten_dict(d, parent_key="", sep="_"):
    """
    Recursively flattens a nested dictionary into a single-level dictionary.

    Args:
        d (dict): The dictionary to be flattened.
        parent_key (str, optional): The parent key to be prepended to the flattened keys. Defaults to "".
        sep (str, optional): The separator to be used between the parent key and the child key. Defaults to "_".

    Returns:
        dict: The flattened dictionary.
    """
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        elif isinstance(v, list):
            items.append((new_key, ", ".join(map(str, v))))
        else:
            items.append((new_key, v))
    return dict(items)

def load_contract_requirements() -> dict:
    try:
        engine = create_engine(get_api("lifsysdb", "lifsysdb"))
        df = pd.read_sql_table("contract_requirements", engine)
        return df
    except (FileNotFoundError, json.JSONDecodeError) as e:
        raise Exception(f"Failed to load contract requirements: {e}")

def get_requirements(matched_position):
    """
    Retrieves the requirements for a given position from a contract DataFrame.

    Args:
        matched_position (str): The position to retrieve requirements for.
        contract_df (pandas.DataFrame): The DataFrame containing the contract dictionary.

    Returns:
        dict or str: A dictionary containing the position and its formatted requirements,
                     or an error message if the position is not found.
    """
    contract_df = load_contract_requirements()
    if matched_position not in contract_df['lcat'].values:
        return f"No requirements found for {matched_position}"

    requirements = contract_df.loc[contract_df['lcat'] == matched_position].iloc[0]
    formatted_requirements = {}

    for field in [
        "degreeRequirements",
        "yearsOfExperience",
        "certifications",
        "experience",
        "skills",
    ]:
        if field in requirements and not pd.isna(requirements[field]):
            formatted_requirements[field] = requirements[field]
        else:
            formatted_requirements[field] = "Not specified"

    return {"position": matched_position, "requirements": formatted_requirements}

def find_closest_match(position_applied, positions_list):
    """
    Find the closest match to position_applied in positions_list
    using Levenshtein distance.
    """
    best_match = None
    highest_ratio = 0

    for position in positions_list:
        ratio = fuzz.ratio(position_applied.lower(), position.lower())
        if ratio > highest_ratio:
            highest_ratio = ratio
            best_match = position

    return best_match

def create_work_experience_dict(detailexp):
    work_dict = {}

    for work in detailexp["work"]:
        company = work["company"]
        work_dict[company] = {
            "duration_months": work["dates_of_employment"]["duration_months"],
            "experience": work["experience"],
            "accomplishments": work["accomplishments"],
        }

    return work_dict

def parse_eml_file(file_path):
    """Open the .eml file in binary mode"""
    with open(file_path, "rb") as file:
        # Parse the .eml file content
        msg = BytesParser(policy=policy.default).parse(file)

    # Get the email text
    email_text = msg.get_body(preferencelist=("plain", "html")).get_content()
    return email_text

def read_all_eml_files(directory_path):
    """Iterate through all .eml files in the specified directory"""
    for filename in os.listdir(directory_path):
        if filename.endswith(".eml"):
            file_path = os.path.join(directory_path, filename)
            output_text = parse_eml_file(file_path)
            print(f"Contents of {filename}:\n{output_text}\n")

def extract_text_version_link(email_content):
    """
    Extracts the link to the TEXT version from the given email content.

    Args:
        email_content (str): The content of the email.

    Returns:
        str or None: The link to the TEXT version if found, None otherwise.
    """
    # Regular expression to find the TEXT version link
    text_link_pattern = r"Link to the TEXT version:\s*(http://\S+)"
    match = re.search(text_link_pattern, email_content)

    if match:
        return match.group(1)
    else:
        return None

def fetch_and_parse_html(url):
    """
    Fetch HTML content from a given URL and parse it using BeautifulSoup.

    Args:
    url (str): The URL to fetch the HTML content from.

    Returns:
    BeautifulSoup: Parsed HTML content, or None if the request failed.
    """
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    # Create a session
    session = requests.Session()

    # Set up headers to mimic a real browser more closely
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.3 Safari/605.1.15",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0",
    }
    session.headers.update(headers)

    try:
        # Send a GET request to the URL, with SSL verification
        response = session.get(url, verify=True)

        # Handle potential redirects
        if response.history:
            logger.info("Request was redirected")
            for resp in response.history:
                logger.info(f"Redirect from {resp.url} to {response.url}")

        # Check if the request was successful
        response.raise_for_status()

        # Parse the HTML content using BeautifulSoup
        soup = BeautifulSoup(response.content, "html.parser")
        return soup

    except requests.exceptions.SSLError:
        logger.warning("SSL verification failed. Attempting without verification (not recommended for production).")
        try:
            # If SSL verification fails, try without verification (use cautiously)
            response = session.get(url, verify=False)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, "html.parser")
            return soup
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed even without SSL verification: {e}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {e}")

    return None

def delete_file(file_path: str) -> Optional[bool]:
    """
    Delete a file if it exists.

    Args:
    file_path (str): The path to the file to be deleted.

    Returns:
    Optional[bool]: True if the file was deleted successfully, False if the file doesn't exist,
                    None if an error occurred during deletion.
    """
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"File '{file_path}' deleted successfully.")
            return True
        else:
            logger.warning(f"File '{file_path}' does not exist.")
            return False
    except PermissionError:
        logger.error(f"Permission denied: Unable to delete file '{file_path}'.")
    except IsADirectoryError:
        logger.error(f"'{file_path}' is a directory, not a file.")
    except Exception as e:
        logger.error(
            f"An error occurred while trying to delete '{file_path}': {str(e)}"
        )

    return None

def find_text(text, left_delimiter, right_delimiter=None, max_chars=None):
    """
    Search for text between delimiters and capture the text between the left and right delimiters.

    :param text: The text to search in
    :param left_delimiter: The left delimiter to search for
    :param right_delimiter: The right delimiter to search for (optional)
    :param max_chars: Maximum number of characters to capture between delimiters (optional)
    :return: The captured text, or None if the delimiters are not found
    """
    # Escape special regex characters in the delimiters
    escaped_left_delimiter = re.escape(left_delimiter)
    escaped_right_delimiter = re.escape(right_delimiter) if right_delimiter else ""

    # Create the pattern
    if right_delimiter:
        if max_chars is not None:
            pattern = f"{escaped_left_delimiter}(.{{0,{max_chars}}}?)(?={escaped_right_delimiter})"
        else:
            pattern = f"{escaped_left_delimiter}(.*?)(?={escaped_right_delimiter})"
    else:
        if max_chars is not None:
            pattern = f"{escaped_left_delimiter}(.{{0,{max_chars}}})"
        else:
            pattern = f"{escaped_left_delimiter}(.*)"

    # Search for the pattern
    match = re.search(pattern, text, re.DOTALL)

    if match:
        return match.group(1).strip()
    else:
        return None

def read_excel_to_dataframe(file_path: str) -> pd.DataFrame:
    """
    Reads an Excel file and returns its contents as a pandas DataFrame.

    Parameters:
    file_path (str): The path to the Excel file.

    Returns:
    pd.DataFrame: The contents of the Excel file as a DataFrame.

    Raises:
    FileNotFoundError: If the specified file_path does not exist.
    Exception: If any other error occurs during the reading process.
    """
    try:
        # Read the Excel file without specifying a sheet name
        df = pd.read_excel(file_path)
        return df
    except FileNotFoundError:
        print(f"Error: The file {file_path} was not found.")
        return None
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return None

def save_json_to_file(data, detailexp, validateresume, path_to_save):
    """
    Save JSON data, detail experience, and resume review to files.

    Args:
        data (dict): The JSON data to be saved.
        detailexp (str): The detail experience to be saved.
        validateresume (str): The resume review to be saved.
        path_to_save (str): The path where the files will be saved.

    Returns:
        str: The file path of the saved JSON file.

    Raises:
        OSError: If there is an error creating the directory or writing the files.
    """
    # Ensure the directory exists
    os.makedirs(path_to_save, exist_ok=True)

    # Convert data to JSON string
    json_str = json.dumps(data, indent=4)

    # Extract relevant information for filename
    candidate_name = data["Candidate"]["Name"]
    position_applied = data["Candidate"]["Applied for"]
    match_score = data["Key Metrics"]["Match Score"]

    # JSON Summary
    filename = (
        f"{candidate_name}_{position_applied}_{match_score.replace(' ', '_')}.json"
    )
    file_path = os.path.join(path_to_save, filename)
    with open(file_path, "w") as file:
        file.write(json_str)

    # Detail Experience
    detailexpFile = f"Detail-{candidate_name}_{position_applied}_{match_score.replace(' ', '_')}.txt"
    file_path = os.path.join(path_to_save, detailexpFile)
    with open(file_path, "w") as file:
        file.write(detailexp)

    # Validate Resume Review
    validateFile = f"Validate-{candidate_name}_{position_applied}_{match_score.replace(' ', '_')}.txt"
    resume_file_path = os.path.join(path_to_save, validateFile)
    with open(resume_file_path, "w") as file:
        file.write(validateresume)

    return file_path

def fix_json(json_string, speed="fast"):
    prompt = f"You are a JSON formatter, fixing any issues with JSON formats. Review the following JSON: {json_string}. Return only the fixed JSON with no additional content. Do not add Here is the fixed JSON or any other text."
    return get_completion_api(prompt, f"groq-{speed}", "simple")

def convert_to_dict(json_output):
    """
    Convert a JSON output to a dictionary.

    Args:
        json_output (str): The JSON output to be converted.

    Returns:
        dict: The converted dictionary.

    """
    # Convert the JSON output to a string
    cleaned_input_str = str(json_output)

    # Replace "}{" with "}, {"
    cleaned_input_str = cleaned_input_str.replace("}{", "}, {")

    cleaned_input_str = cleaned_input_str.replace("'", "'")

    # Remove leading and trailing square brackets "[" and "]"
    cleaned_input_str = cleaned_input_str.strip("[]")

    # Load the cleaned JSON string into a dictionary
    output_dict = json.loads(cleaned_input_str)

    return output_dict

def plaintext_output(data):
    plain_text_output = "\n".join(data)
    return plain_text_output

def clean_text(text):
    # Remove backslashes and other escape characters
    text = text.replace("\\", "")
    # If there are other specific patterns to clean, use re.sub()
    # Example: Remove annotations or other specific objects
    text = re.sub(r"\\(.*?)\\", "", text)
    return text


def get_name_from_string(s):
    # Define the regular expression pattern to match the Name line
    pattern = r"Name:\s*(.+)"

    # Use re.search to find a match in the string
    match = re.search(pattern, s)

    # If a match is found, return the matching group (the name)
    if match:
        return match.group(1)
    else:
        return "Name not found"

def collect_information_from_text(input_text):
    """
    Parses an input text containing questions marked with bullets, prompts the user for answers,
    and saves the responses in a dictionary.

    Parameters:
    - input_text (str): A long string of text with questions marked by '-' and separated by newlines.

    Returns:
    - dict: A dictionary with questions as keys and user responses as values.
    """
    # Split the input text into lines
    lines = input_text.split("\n")

    # Dictionary to hold the questions and user responses
    info = {}

    # Process each line
    for line in lines:
        # Check if the line starts with a bullet
        if line.startswith("-"):
            # Extract the question (remove the bullet and leading/trailing spaces)
            question = line[1:].strip()
            print(question + ":")  # Display the question
            user_input = input()  # Get user input
            info[question] = (
                user_input  # Save the question and answer in the dictionary
            )

    return info

def collect_data_from_user(example_text):
    prompts = example_text.split("\n- ")
    data_collected = {}

    for prompt in prompts:
        if prompt.strip():
            key = prompt.split("\n")[0]
            user_input = input(f"Please enter {key}: ")
            data_collected[key] = user_input

    return data_collected

def process_content(content):
    """
    Processes the given content into a nested dictionary structure using generated placeholder values.

    Parameters:
    - content (str): The plaintext content to be processed.

    Returns:
    - dict: A nested dictionary structure representing the processed content with placeholder values.
    """
    lines = content.split("\n")
    processed_content = {}
    current_root = None

    # Generate the values_dict with placeholder values based on the content
    values_dict = generate_values_dict_from_content(content)

    for line in lines:
        if line.strip() and line[0].isdigit() and ". " in line:
            current_root = line.split(". ", 1)[1]
            processed_content[current_root] = {}
        elif "-" in line and current_root is not None:
            key = line.strip().lstrip("-").strip()
            value = values_dict.get(key, "Not provided")
            processed_content[current_root][key] = value

    final_content = update_content(processed_content)

    return final_content

def generate_values_dict_from_content(content):
    """
    Generates a dictionary of keys with placeholder values based on the provided content.

    Parameters:
    - content (str): The plaintext content to be processed.

    Returns:
    - dict: A dictionary with keys derived from the content and placeholder values.
    """
    lines = content.split("\n")
    values_dict = {}

    for line in lines:
        if "-" in line:
            key = line.strip().lstrip("-").strip()
            # Assign a placeholder value or generate a default value for each key
            values_dict[key] = f"Placeholder for {key}"

    return values_dict

def update_content(info_dict):
    for category, level2_items in info_dict.items():
        print(f"\nCategory: {category}")
        items_to_remove = []
        for item, value in level2_items.items():
            user_input = input(f"Enter value for '{item}': ")
            if user_input.upper() == "TBD":
                items_to_remove.append(item)
            else:
                info_dict[category][item] = user_input

        # Remove items with 'TBD' from the dictionary
        for item in items_to_remove:
            del info_dict[category][item]
    return info_dict

async def write_to_redis(key, value):
    r = redis.Redis(host="192.168.1.12", port=6379, decode_responses=True)
    await r.set(key, value)
    await r.close()
