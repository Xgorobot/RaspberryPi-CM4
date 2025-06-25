import os
import json
import re

# Note: Path handling for language files might need adjustment
# based on where these functions are called from in the new structure.
# For now, assuming 'language' directory is accessible relative to CWD or
# that CWD is set appropriately before calling these.

# Default base path assumes this script is in dog_app/common, and language dir is at dog_app/language
DEFAULT_LANGUAGE_BASE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "language"))


def load_language(base_path=None):
    """
    Loads the language dictionary from .la file based on language.ini.
    :param base_path: The base directory where 'language' folder is located.
                     If None, uses DEFAULT_LANGUAGE_BASE_PATH.
    """
    if base_path is None:
        base_path = DEFAULT_LANGUAGE_BASE_PATH

    language_ini_path = os.path.join(base_path, "language.ini") # language.ini is directly in base_path (e.g. dog_app/language/language.ini)
    # print(f"Attempting to read language.ini from: {language_ini_path}")
    try:
        with open(language_ini_path, 'r') as f:
            lang_setting = f.read().strip()
        # print(f"Language setting from ini: {lang_setting}")
    except FileNotFoundError:
        print(f"Error: language.ini not found at {language_ini_path}")
        # Fallback to a default language or handle error
        # For now, let's assume 'en' if not found, or raise error
        # To match original behavior, it might just fail if file is not found.
        # Let's stick to original expectation of failure.
        raise

    language_pack_path = os.path.join(base_path, lang_setting + ".la") # .la file is also directly in base_path
    # print(f"Attempting to read language pack from: {language_pack_path}")
    try:
        with open(language_pack_path, 'r') as f:
            language_json = f.read()
    except FileNotFoundError:
        print(f"Error: Language pack {lang_setting}.la not found at {language_pack_path}")
        raise

    # Remove control characters which might invalidate JSON
    cleaned_json = re.sub(r'[\x00-\x1f\x7f]', '', language_json)
    language_dict = json.loads(cleaned_json)
    return language_dict

def get_language_setting(base_path=None):
    """
    Reads the language setting (e.g., 'cn' or 'en') from language.ini.
    :param base_path: The base directory where 'language' folder is located.
                     If None, uses DEFAULT_LANGUAGE_BASE_PATH.
    """
    if base_path is None:
        base_path = DEFAULT_LANGUAGE_BASE_PATH

    language_ini_path = os.path.join(base_path, "language.ini")
    # print(f"Attempting to read language.ini from: {language_ini_path}")
    try:
        with open(language_ini_path,'r') as f:
            language_setting = f.read().strip()
        # print(f"Language setting: {language_setting}")
        return language_setting
    except FileNotFoundError:
        print(f"Error: language.ini not found at {language_ini_path}")
        # Fallback or error handling
        # For now, let's assume 'en' as a default or raise
        raise

if __name__ == '__main__':
    # Example usage:
    # This test will now use DEFAULT_LANGUAGE_BASE_PATH which is dog_app/language/
    # It assumes this script is run from a context where ../language relative to it makes sense.
    # For instance, if run from dog_app/common/

    print(f"Testing language utils. Default language base path: {DEFAULT_LANGUAGE_BASE_PATH}")

    # Create dummy files for testing in the default location
    if not os.path.exists(DEFAULT_LANGUAGE_BASE_PATH):
        os.makedirs(DEFAULT_LANGUAGE_BASE_PATH)
        print(f"Created directory: {DEFAULT_LANGUAGE_BASE_PATH}")

    dummy_ini_path = os.path.join(DEFAULT_LANGUAGE_BASE_PATH, "language.ini")
    dummy_en_la_path = os.path.join(DEFAULT_LANGUAGE_BASE_PATH, "en.la")
    dummy_cn_la_path = os.path.join(DEFAULT_LANGUAGE_BASE_PATH, "cn.la")

    with open(dummy_ini_path, "w") as f:
        f.write("en")
    with open(dummy_en_la_path, "w") as f:
        json.dump({"MAIN": {"GREETING": "Hello"}}, f)
    with open(dummy_cn_la_path, "w") as f:
        json.dump({"MAIN": {"GREETING": "你好"}}, f)
    print(f"Created dummy language files in {DEFAULT_LANGUAGE_BASE_PATH}")

    current_setting = get_language_setting() # Uses default path
    print(f"Current language setting: {current_setting}")
    lang_dict_en = load_language() # Uses default path
    print(f"English dictionary: {lang_dict_en}")

    # Test with Chinese
    with open(dummy_ini_path, "w") as f:
        f.write("cn")
    current_setting_cn = get_language_setting()
    print(f"Current language setting (after change): {current_setting_cn}")
    lang_dict_cn = load_language()
    print(f"Chinese dictionary: {lang_dict_cn}")

    # Clean up dummy files
    print(f"Cleaning up dummy files...")
    os.remove(dummy_en_la_path)
    os.remove(dummy_cn_la_path)
    os.remove(dummy_ini_path)
    # Only remove directory if it was created by this script and is empty
    # This is simplistic; robust cleanup might check if it was pre-existing & empty.
    try:
        if not os.listdir(DEFAULT_LANGUAGE_BASE_PATH): # Check if empty
            os.rmdir(DEFAULT_LANGUAGE_BASE_PATH)
            print(f"Removed directory: {DEFAULT_LANGUAGE_BASE_PATH}")
        else:
            print(f"Directory {DEFAULT_LANGUAGE_BASE_PATH} not empty, not removing.")
    except OSError as e:
        print(f"Error removing directory {DEFAULT_LANGUAGE_BASE_PATH}: {e}")

    print("Test complete.")
