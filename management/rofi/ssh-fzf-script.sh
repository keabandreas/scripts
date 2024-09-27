#!/bin/bash

# Load configurations
config=$(cat ssh_docker.json)

# Function to parse JSON (requires jq)
parse_json() {
    echo "$1" | jq -r "$2"
}

# SSH connection function
ssh_connect() {
    local key="$1"
    local user=$(parse_json "$config" ".servers[\"$key\"].user")
    local host=$(parse_json "$config" ".servers[\"$key\"].host")
    echo "Connecting to $user@$host..."
    ssh "$user@$host"
}

# Main menu
main_menu() {
    local servers=$(parse_json "$config" '.servers | to_entries[] | "\(.key):\(.value.name) (\(.value.user)@\(.value.host))"')
    local choice=$(echo "$servers" | fzf --prompt="Select SSH Server > ")
    
    if [ -n "$choice" ]; then
        local key=$(echo "$choice" | cut -d':' -f1)
        ssh_connect "$key"
    fi
}

# Start the script
main_menu
