import zipfile
import os
import re

local = os.getcwd()
version_id = "1.12.2"
# Libraries path
root_directory = f'{local}\\instances\\{version_id}\\libraries\\'
# Extract the natives path
output_directory = f'{local}\\instances\\{version_id}\\libraries\\natives'

# Check natives folder is exists!
os.makedirs(output_directory, exist_ok=True)

# Regular expression to match the native jar files(???working time.....)
pattern = re.compile(r'^.*-natives-(windows|linux|macos)\.jar$')

def extract_natives_from_jar(jar_path, output_directory, platform):
    try:
        with zipfile.ZipFile(jar_path, 'r') as jar_file:
            for member in jar_file.namelist():
                # Extract only the .dll files...
                if member.startswith(f'{platform}/') and member.lower().endswith('.dll'):
                    # Extract the filename from the full path
                    filename = os.path.basename(member)
                    output_path = os.path.join(output_directory, filename)
                    with jar_file.open(member) as source_file:
                        with open(output_path, 'wb') as target_file:
                            target_file.write(source_file.read())
        print(f'Extracted natives from {jar_path} to {output_directory}')
    except PermissionError as e:
        print(f'Permission error with {jar_path}: {e}')
    except Exception as e:
        print(f'Error processing {jar_path}: {e}')

def process_directory(directory, output_directory):
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.jar'):
                jar_path = os.path.join(root, file)
                match = pattern.search(file)
                if match:
                    platform = match.group(1)
                    extract_natives_from_jar(jar_path, output_directory, platform)

# Start processing from the root folder
process_directory(root_directory, output_directory)