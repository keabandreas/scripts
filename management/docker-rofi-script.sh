#!/bin/bash

# Load configurations
config=$(cat ssh_docker.json)

# Function to parse JSON (requires jq)
parse_json() {
    echo "$1" | jq -r "$2"
}

# Docker connection function
docker_connect() {
    local server_host="$1"
    local container_key="$2"
    local user=$(parse_json "$config" ".servers[] | select(.host == \"$server_host\") | .user")
    local container_name=$(parse_json "$config" ".docker_containers[\"$server_host\"][\"$container_key\"].name")
    echo "Connecting to Docker container $container_name on $server_host..."
    ssh -t "$user@$server_host" "docker exec -it $container_name /bin/bash"
}

# Main menu
main_menu() {
    local docker_servers=$(parse_json "$config" '.servers | to_entries[] | select(.value.server == "docker") | "\(.key):\(.value.name) (\(.value.host))"')
    local server_choice=$(echo "$docker_servers" | rofi -dmenu -p "Select Docker Server" -i)
    
    if [ -n "$server_choice" ]; then
        local server_key=$(echo "$server_choice" | cut -d':' -f1)
        local server_host=$(parse_json "$config" ".servers[\"$server_key\"].host")
        
        local containers=$(parse_json "$config" ".docker_containers[\"$server_host\"] | to_entries[] | \"\(.key):\(.value.name)\"")
        local container_choice=$(echo "$containers" | rofi -dmenu -p "Select Docker Container" -i)
        
        if [ -n "$container_choice" ]; then
            local container_key=$(echo "$container_choice" | cut -d':' -f1)
            docker_connect "$server_host" "$container_key"
        fi
    fi
}

# Start the script
main_menu
