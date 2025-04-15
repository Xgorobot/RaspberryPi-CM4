import os
import locale

# Function to set the language based on the system locale
def get_system_language():
    current_locale = locale.getdefaultlocale()
    if current_locale:
        language_code = current_locale[0][:2]
        # Validate and return language if it's supported
        if language_code in ['en', 'cn', 'jp']:
            return language_code
    return 'en'  # Default to English if locale is not set or unsupported

# Function to set the language to a config file
def set_language_in_file(language_code):
    language_directory = 'language'
    language_file_path = os.path.join(language_directory, 'language.ini')

    # Ensure the language directory exists
    os.makedirs(language_directory, exist_ok=True)

    # Write the selected language to the file if different
    if os.path.exists(language_file_path):
        with open(language_file_path, 'r') as configfile:
            current_code_in_file = configfile.read().strip()
    else:
        current_code_in_file = None

    if current_code_in_file != language_code:
        with open(language_file_path, 'w') as configfile:
            configfile.write(language_code)
        print(f"Language '{language_code}' written to {language_file_path}")
    else:
        print(f"Language '{language_code}' already set.")

# Determine the language (either cn, en, or default to en)
language = get_system_language()

# Set the language in the config file
set_language_in_file(language)

# Run the main program with the appropriate language
if language == 'cn':
    print('Language set to Chinese (cn)')
    os.system('sudo python3 main.py')
else:
    print('Language set to English (en)')
    os.system('sudo -E python3 main.py')
