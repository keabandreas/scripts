#!/bin/bash

# ============= Configuration Section =============
# Predefined paths
CONFIG_FILE="$HOME/lib/scripts/work/management/ssh_docker.json"
SCRIPTS_DIR="$HOME/lib/scripts/work/management"

# Define your scripts here
# Format: SCRIPTS["Menu Name"]="path/to/script.sh"
declare -A SCRIPTS
SCRIPTS["SSH"]="$SCRIPTS_DIR/ssh-runtime.sh"
SCRIPTS["Docker"]="$SCRIPTS_DIR/docker-rofi-script.sh"
SCRIPTS["Git"]="$SCRIPTS_DIR/git-rofi-script.sh"

# Add more scripts here as needed
# SCRIPTS["New Option"]="$SCRIPTS_DIR/new-script.sh"

# ============= Function Definitions =============

# Function to generate menu options
generate_menu() {
    for key in "${!SCRIPTS[@]}"; do
        echo "$key"
    done
}

# Function to execute the chosen script
execute_script() {
    local script_name="$1"
    local script_path="${SCRIPTS[$script_name]}"
    if [[ -f "$script_path" && -x "$script_path" ]]; then
        "$script_path"
    else
        echo "Error: Script not found or not executable: $script_path" >&2
        exit 1
    fi
}

# Main function
main() {
    # Generate menu options
    mapfile -t options < <(generate_menu)
    
    if [ ${#options[@]} -eq 0 ]; then
        echo "Error: No options available. Check SCRIPTS array and paths." >&2
        exit 1
    fi
    
    # Show menu and get user choice
    chosen=$(printf '%s\n' "${options[@]}" | rofi -dmenu -p "Choose script:" -i)
    
    # Run the chosen script
    if [[ -n "$chosen" && -n "${SCRIPTS[$chosen]}" ]]; then
        execute_script "$chosen"
    else
        echo "Error: Invalid selection or script not found." >&2
        exit 1
    fi
}

# Run the main function
main
