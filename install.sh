#!/usr/bin/env bash

set -e

# get_script_dir from https://stackoverflow.com/questions/59895/how-do-i-get-the-directory-where-a-bash-script-is-located-from-within-the-script
get_script_dir()
{
    local SOURCE_PATH="${BASH_SOURCE[0]}"
    local SYMLINK_DIR
    local SCRIPT_DIR
    # Resolve symlinks recursively
    while [ -L "$SOURCE_PATH" ]; do
        # Get symlink directory
        SYMLINK_DIR="$( cd -P "$( dirname "$SOURCE_PATH" )" >/dev/null 2>&1 && pwd )"
        # Resolve symlink target (relative or absolute)
        SOURCE_PATH="$(readlink "$SOURCE_PATH")"
        # Check if candidate path is relative or absolute
        if [[ $SOURCE_PATH != /* ]]; then
            # Candidate path is relative, resolve to full path
            SOURCE_PATH=$SYMLINK_DIR/$SOURCE_PATH
        fi
    done
    # Get final script directory path from fully resolved source path
    SCRIPT_DIR="$(cd -P "$( dirname "$SOURCE_PATH" )" >/dev/null 2>&1 && pwd)"
    echo "$SCRIPT_DIR"
}

############################################################
# Help                                                     #
############################################################
Help()
{
   # Display Help
   echo "Útil paisagem installer."
   echo
   echo "Syntax: install.sh [-h|p]"
   echo "Options:"
   echo "-h     Print this help."
   echo "-p     Set Python runtime (3.13 or greater)."
   echo
}

# Set variables
PYTHON="python3"

# Input options
while getopts ":hp:" option; do
   case $option in
      h) # display help
         Help
         exit;;
      p) # Set Python runtime
         PYTHON=$OPTARG;;
     \?) # Invalid option
         echo "Error: invalid option."
         echo ""
         Help
         exit;;
   esac
done

# Install Útil paisagem
cd $(get_script_dir)

echo "Creating virtual environment..."
$PYTHON -m venv .env

echo "Activating virtual environment..."
source .env/bin/activate

echo "Installing required Python modules..."
python -m pip install -r requirements.txt

echo "Compiling translations..."
source scripts/compilemessages

echo "Changing file permissions..."
chmod a+x utilpaisagem.sh

echo "Creating shortcut..."
python shortcut.py

echo ""
echo "Installation succesfull."
echo "Run Útil paisagem using the application shortcut or typing \"source $(get_script_dir)/utilpaisagem.sh\" on the terminal"
