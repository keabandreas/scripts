#!/bin/bash

# ANSI color codes
BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Load configurations
config=$(cat ssh_docker.json)
servers_config=$(cat rsync.json)

validate_config() {
    local required_fields=("name" "user" "host" "type")
    local servers=$(echo "$config" | jq -r '.servers | keys[]')
    
    for server in $servers; do
        for field in "${required_fields[@]}"; do
            if [[ $(echo "$config" | jq -r ".servers[\"$server\"].$field") == null ]]; then
                echo "Error: Missing '$field' for server $server in configuration."
                exit 1
            fi
        done
    done
    echo "Configuration validation passed."
}

# Call this function after loading the config
config=$(cat ssh_docker.json)
validate_config

# In the ssh_scripts_for_server function, you could add:
if [[ ! -d "$script_dir" ]]; then
    echo -e "${YELLOW}Warning: No directory found for server type '$server_type'. Using default scripts.${NC}"
    script_dir="external_scripts/default"
fi

# Function to parse JSON (requires jq)
parse_json() {
    echo "$1" | jq -r "$2"
}

# Function to print a fancy header
print_header() {
    echo -e "${BLUE}"
    echo "┌───────────────────────────────────────┐"
    echo "│                                       │"
    echo "│         Main Management Script        │"
    echo "│                                       │"
    echo "└───────────────────────────────────────┘"
    echo -e "${NC}"
}

# Clear screen function
clear_screen() {
    clear
    print_header
}

# Function to handle quitting
quit_script() {
    echo -e "${BLUE}Thank you for using the Main Management Script. Goodbye!${NC}"
    exit 0
}

# SSH and Docker Management Functions
ssh_menu() {
    while true; do
        clear_screen
        echo -e "${YELLOW}=== SSH Options Menu ===${NC}"
        echo -e "${GREEN}1. Connection${NC}"
        echo -e "${GREEN}2. Scripts${NC}"
        echo -e "${GREEN}3. Rsync${NC}"
        echo -e "${GREEN}b. Back to main menu${NC}"
        echo -e "${GREEN}q. Quit${NC}"
        echo -e "${YELLOW}========================${NC}"
        echo -e "${YELLOW}Enter your choice:${NC} "
        read option

        case $option in
            1) ssh_connection_menu ;;
            2) ssh_scripts_menu ;;
            3) rsync_menu ;;
            b) return ;;
            q) quit_script ;;
            *) echo -e "${YELLOW}Invalid choice. Please try again.${NC}" ;;
        esac
    done
}

ssh_connection_menu() {
    while true; do
        clear_screen
        echo -e "${YELLOW}=== SSH Server Connection Menu ===${NC}"
        parse_json "$config" '.servers | to_entries[] | "\(.key). \(.value.name) (\(.value.user))"'
        echo -e "${GREEN}b. Back to SSH options${NC}"
        echo -e "${GREEN}q. Quit${NC}"
        echo -e "${YELLOW}===================================${NC}"
        echo -e "${YELLOW}Enter your choice:${NC} "
        read choice

        case $choice in
            [0-9]*) ssh_connect "$choice" ;;
            b) return ;;
            q) quit_script ;;
            *) echo -e "${YELLOW}Invalid choice. Please try again.${NC}" ;;
        esac
    done
}

ssh_connect() {
    local key="$1"
    local user=$(parse_json "$config" ".servers[\"$key\"].user")
    local host=$(parse_json "$config" ".servers[\"$key\"].host")
    echo -e "${BLUE}Connecting to $user@$host...${NC}"
    ssh "$user@$host"
}

ssh_scripts_menu() {
    while true; do
        clear_screen
        echo -e "${YELLOW}=== SSH Server Selection for Scripts ===${NC}"
        parse_json "$config" '.servers | to_entries[] | "\(.key). \(.value.name) (\(.value.user))"'
        echo -e "${GREEN}b. Back to SSH options${NC}"
        echo -e "${GREEN}q. Quit${NC}"
        echo -e "${YELLOW}==========================================${NC}"
        echo -e "${YELLOW}Enter your choice:${NC} "
        read server_choice

        case $server_choice in
            [0-9]*) ssh_scripts_for_server "$server_choice" ;;
            b) return ;;
            q) quit_script ;;
            *) echo -e "${YELLOW}Invalid choice. Please try again.${NC}" ;;
        esac
    done
}

ssh_scripts_for_server() {
    local key="$1"
    local server_type=$(parse_json "$config" ".servers[\"$key\"].type")
    local script_dir="external_scripts/${server_type,,}"  # Remove leading slash and convert to lowercase
    local full_path=$(readlink -f "$script_dir")

    echo "Debug: Server Type: $server_type"
    echo "Debug: Script Directory: $script_dir"
    echo "Debug: Full Path: $full_path"

    while true; do
        clear_screen
        echo -e "${YELLOW}=== SSH Scripts Menu for ${server_type} Server ===${NC}"
        list_scripts "$script_dir"
        echo -e "${GREEN}b. Back to server selection${NC}"
        echo -e "${GREEN}q. Quit${NC}"
        echo -e "${YELLOW}==========================================${NC}"
        echo -e "${YELLOW}Enter your choice:${NC} "
        read script_choice

        case $script_choice in
            [0-9]*)
                local script_file=$(get_script_file "$script_dir" "$script_choice")
                if [[ -n $script_file ]]; then
                    run_ssh_script "$key" "$script_file"
                else
                    echo -e "${YELLOW}Invalid script number. Please try again.${NC}"
                    sleep 2
                fi
                ;;
            b) return ;;
            q) quit_script ;;
            *) echo -e "${YELLOW}Invalid choice. Please try again.${NC}" ;;
        esac
    done
}

list_scripts() {
    local dir="$1"
    
    if [[ ! -d "$dir" ]]; then
        echo -e "${YELLOW}No scripts available for this server type.${NC}"
        return
    fi

    local scripts=($(ls "$dir"/*.sh 2>/dev/null))
    if [[ ${#scripts[@]} -eq 0 ]]; then
        echo -e "${YELLOW}No scripts available for this server type.${NC}"
        return
    fi

    for i in "${!scripts[@]}"; do
        echo -e "${GREEN}$((i+1)). $(basename "${scripts[$i]}" .sh)${NC}"
    done
}

get_script_file() {
    local dir="$1"
    local choice="$2"
    local scripts=($(ls "$dir"/*.sh 2>/dev/null))
    if [[ $choice -ge 1 && $choice -le ${#scripts[@]} ]]; then
        echo "${scripts[$((choice-1))]}"
    fi
}

run_ssh_script() {
    local key="$1"
    local script_path="$2"
    local user=$(parse_json "$config" ".servers[\"$key\"].user")
    local host=$(parse_json "$config" ".servers[\"$key\"].host")
    echo -e "${BLUE}Running script $(basename "$script_path") on $user@$host...${NC}"
    echo "Debug: Full script path: $script_path"
    if [[ -f "$script_path" ]]; then
        ssh "$user@$host" "bash -s" < "$script_path"
        echo -e "${GREEN}Script execution completed.${NC}"
    else
        echo -e "${YELLOW}Error: Script file not found.${NC}"
    fi
    read -p "Press Enter to continue..."
}

print_docker_server_menu() {
    clear_screen
    echo -e "${YELLOW}=== Docker Server Selection Menu ===${NC}"
    parse_json "$config" '.servers | to_entries[] | select(.value.server == "docker") | "\(.key). \(.value.name) (\(.value.host))"'
    echo -e "${GREEN}b. Back to main menu${NC}"
    echo -e "${GREEN}q. Quit${NC}"
    echo -e "${YELLOW}=====================================${NC}"
}

print_docker_container_menu() {
    local server_host="$1"
    clear_screen
    local server_name=$(parse_json "$config" ".servers[] | select(.host == \"$server_host\") | .name")
    echo -e "${YELLOW}=== Docker Container Connection Menu for $server_name ===${NC}"
    parse_json "$config" ".docker_containers[\"$server_host\"] | to_entries[] | \"\(.key). \(.value.name)\""
    echo -e "${GREEN}b. Back to Docker server selection${NC}"
    echo -e "${GREEN}q. Quit${NC}"
    echo -e "${YELLOW}=======================================================${NC}"
}

docker_connect() {
    local server_host="$1"
    local container_key="$2"
    local user=$(parse_json "$config" ".servers[] | select(.host == \"$server_host\") | .user")
    local container_name=$(parse_json "$config" ".docker_containers[\"$server_host\"][\"$container_key\"].name")
    echo -e "${BLUE}Connecting to Docker container $container_name on $server_host...${NC}"
    ssh -t "$user@$server_host" "docker exec -it $container_name /bin/bash"
}

docker_menu() {
    while true; do
        print_docker_server_menu
        echo -e "${YELLOW}Enter your choice:${NC} "
        read choice

        case $choice in
            [0-9]*)
                local server_host=$(parse_json "$config" ".servers[\"$choice\"].host")
                docker_container_menu "$server_host"
                ;;
            b) return ;;
            q) quit_script ;;
            *) echo -e "${YELLOW}Invalid choice. Please try again.${NC}" ;;
        esac
    done
}

docker_container_menu() {
    local server_host="$1"
    while true; do
        print_docker_container_menu "$server_host"
        echo -e "${YELLOW}Enter your choice:${NC} "
        read choice

        case $choice in
            [0-9]*) docker_connect "$server_host" "$choice" ;;
            b) return ;;
            q) quit_script ;;
            *) echo -e "${YELLOW}Invalid choice. Please try again.${NC}" ;;
        esac
    done
}

# Git Management Functions
handle_personal() {
    echo -e "${YELLOW}Choose a personal repository:${NC}"
    select repo in "dotfiles" "scripts" "wallpapers" "Back to Git menu" "Quit"; do
        case $repo in
            dotfiles)
                cd "$HOME/dotfiles/" || exit
                return 0
                ;;
            scripts)
                cd "$HOME/lib/scripts/" || exit
                return 0
                ;;
            wallpapers)
                cd "$HOME/lib/images/wallpapers/" || exit
                return 0
                ;;
            "Back to Git menu")
                return 1
                ;;
            "Quit")
                quit_script
                ;;
            *)
                echo -e "${YELLOW}Invalid option. Please try again.${NC}"
                ;;
        esac
    done
}

handle_work() {
    echo -e "${YELLOW}Choose work repository location:${NC}"
    select location in "local" "remote" "Back to Git menu" "Quit"; do
        case $location in
            local)
                cd "$HOME/lib/scripts/work/" || exit
                return 0
                ;;
            remote)
                cd "$HOME/digit/scripts/" || exit
                return 0
                ;;
            "Back to Git menu")
                return 1
                ;;
            "Quit")
                quit_script
                ;;
            *)
                echo -e "${YELLOW}Invalid option. Please try again.${NC}"
                ;;
        esac
    done
}

perform_git_operations() {
    echo -e "${BLUE}Staging changes...${NC}"
    git add .

    echo -e "${YELLOW}Enter commit message (or 'q' to quit):${NC}"
    read -r commit_message

    if [ "$commit_message" = "q" ]; then
        quit_script
    fi

    echo -e "${BLUE}Committing changes...${NC}"
    git commit -m "$commit_message"

    echo -e "${BLUE}Pushing to remote repository...${NC}"
    git push

    echo -e "${GREEN}Git operations completed successfully.${NC}"
    sleep 2
}

git_management() {
    while true; do
        clear_screen
        echo -e "${YELLOW}=== Git Management ===${NC}"
        echo -e "${GREEN}1. Personal Repository${NC}"
        echo -e "${GREEN}2. Work Repository${NC}"
        echo -e "${GREEN}b. Back to Main Menu${NC}"
        echo -e "${GREEN}q. Quit${NC}"
        echo -e "${YELLOW}========================${NC}"
        echo -e "${YELLOW}Enter your choice:${NC} "
        read choice

        case $choice in
            1)
                if handle_personal; then
                    perform_git_operations
                fi
                ;;
            2)
                if handle_work; then
                    perform_git_operations
                fi
                ;;
            b)
                return
                ;;
            q)
                quit_script
                ;;
            *)
                echo -e "${YELLOW}Invalid option. Please try again.${NC}"
                sleep 2
                ;;
        esac
    done
}

# Rsync Functions
rsync_menu() {
    while true; do
        clear_screen
        echo -e "${YELLOW}=== Rsync File Transfer Menu ===${NC}"
        echo -e "${GREEN}1. Copy files to remote server${NC}"
        echo -e "${GREEN}2. Copy files from remote server${NC}"
        echo -e "${GREEN}b. Back to SSH options${NC}"
        echo -e "${GREEN}q. Quit${NC}"
        echo -e "${YELLOW}==================================${NC}"
        echo -e "${YELLOW}Enter your choice:${NC} "
        read choice

        case $choice in
            1)
                select_server "to"
                ;;
            2)
                select_server "from"
                ;;
            b)
                return
                ;;
            q)
                quit_script
                ;;
            *)
                echo -e "${YELLOW}Invalid choice. Please try again.${NC}"
                sleep 2
                ;;
        esac
    done
}

select_server() {
    local direction=$1
    clear_screen
    echo -e "${YELLOW}=== Select Server ===${NC}"
    server_count=$(parse_json "$servers_config" '.rsync_servers | length')
    for ((i=0; i<server_count; i++)); do
        name=$(parse_json "$servers_config" ".rsync_servers[$i].name")
        echo -e "${GREEN}$((i+1)). $name${NC}"
    done
    echo -e "${GREEN}b. Back to Rsync menu${NC}"
    echo -e "${GREEN}q. Quit${NC}"
    echo -e "${YELLOW}=====================${NC}"
    echo -e "${YELLOW}Enter your choice:${NC} "
    read server_choice

    case $server_choice in
        [1-9])
            if [ "$server_choice" -le "$server_count" ]; then
                index=$((server_choice-1))
                ip=$(parse_json "$servers_config" ".rsync_servers[$index].host")
                user=$(parse_json "$servers_config" ".rsync_servers[$index].user")
                if [ "$direction" == "to" ]; then
                    rsync_to_remote "$user" "$ip"
                else
                    rsync_from_remote "$user" "$ip"
                fi
            else
                echo -e "${YELLOW}Invalid choice. Please try again.${NC}"
                sleep 2
            fi
            ;;
        b)
            return
            ;;
        q)
            quit_script
            ;;
        *)
            echo -e "${YELLOW}Invalid choice. Please try again.${NC}"
            sleep 2
            ;;
    esac
}

rsync_to_remote() {
    local user=$1
    local ip=$2
    echo -e "${YELLOW}Enter the local file/directory path to copy (or 'q' to quit):${NC}"
    read local_path
    [ "$local_path" = "q" ] && quit_script
    echo -e "${YELLOW}Enter the remote destination path (or 'q' to quit):${NC}"
    read remote_path
    [ "$remote_path" = "q" ] && quit_script
    echo -e "${BLUE}Copying files to remote server $ip...${NC}"
    rsync -avz --progress "$local_path" "$user@$ip:$remote_path"
    echo -e "${GREEN}Rsync operation completed.${NC}"
    sleep 2
}

rsync_from_remote() {
    local user=$1
    local ip=$2
    echo -e "${YELLOW}Enter the remote file/directory path to copy (or 'q' to quit):${NC}"
    read remote_path
    [ "$remote_path" = "q" ] && quit_script
    echo -e "${YELLOW}Enter the local destination path (or 'q' to quit):${NC}"
    read local_path
    [ "$local_path" = "q" ] && quit_script
    echo -e "${BLUE}Copying files from remote server $ip...${NC}"
    rsync -avz --progress "$user@$ip:$remote_path" "$local_path"
    echo -e "${GREEN}Rsync operation completed.${NC}"
    sleep 2
}

# Main menu
main_menu() {
    while true; do
        clear_screen
        echo -e "${YELLOW}=== Main Menu ===${NC}"
        echo -e "${GREEN}1. SSH and Docker Management${NC}"
        echo -e "${GREEN}2. Git Management${NC}"
        echo -e "${GREEN}q. Quit${NC}"
        echo -e "${YELLOW}==================${NC}"
        echo -e "${YELLOW}Enter your choice:${NC} "
        read choice

        case $choice in
            1) 
                ssh_menu
                ;;
            2)
                git_management
                ;;
            q) 
                quit_script
                ;;
            *) 
                echo -e "${YELLOW}Invalid choice. Please try again.${NC}"
                sleep 2
                ;;
        esac
    done
}

# Start the script
main_menu
