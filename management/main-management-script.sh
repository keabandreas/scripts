#!/bin/bash

# ANSI color codes
BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Load configurations
config=$(cat ssh_docker.json)
servers_config=$(cat rsync.json)

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

# SSH and Docker Management Functions
print_ssh_menu() {
    clear_screen
    echo -e "${YELLOW}=== SSH Server Connection Menu ===${NC}"
    parse_json "$config" '.servers | to_entries[] | "\(.key). \(.value.name) (\(.value.user)@\(.value.host))"'
    echo -e "${GREEN}b. Back to main menu${NC}"
    echo -e "${GREEN}q. Quit${NC}"
    echo -e "${YELLOW}===================================${NC}"
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

ssh_connect() {
    local key="$1"
    local user=$(parse_json "$config" ".servers[\"$key\"].user")
    local host=$(parse_json "$config" ".servers[\"$key\"].host")
    echo -e "${BLUE}Connecting to $user@$host...${NC}"
    ssh "$user@$host"
}

docker_connect() {
    local server_host="$1"
    local container_key="$2"
    local user=$(parse_json "$config" ".servers[] | select(.host == \"$server_host\") | .user")
    local container_name=$(parse_json "$config" ".docker_containers[\"$server_host\"][\"$container_key\"].name")
    echo -e "${BLUE}Connecting to Docker container $container_name on $server_host...${NC}"
    ssh -t "$user@$server_host" "docker exec -it $container_name /bin/bash"
}

ssh_menu() {
    while true; do
        print_ssh_menu
        echo -e "${YELLOW}Enter your choice:${NC} "
        read choice

        case $choice in
            [0-9]*) ssh_connect "$choice" ;;
            b) return ;;
            q) exit ;;
            *) echo -e "${YELLOW}Invalid choice. Please try again.${NC}" ;;
        esac
    done
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
            q) exit ;;
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
            q) exit ;;
            *) echo -e "${YELLOW}Invalid choice. Please try again.${NC}" ;;
        esac
    done
}

# Git Management Functions
handle_personal() {
    echo -e "${YELLOW}Choose a personal repository:${NC}"
    select repo in "dotfiles" "scripts" "wallpapers" "Back to Git menu"; do
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
            *)
                echo -e "${YELLOW}Invalid option. Please try again.${NC}"
                ;;
        esac
    done
}

handle_work() {
    echo -e "${YELLOW}Choose work repository location:${NC}"
    select location in "local" "remote" "Back to Git menu"; do
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
            *)
                echo -e "${YELLOW}Invalid option. Please try again.${NC}"
                ;;
        esac
    done
}

perform_git_operations() {
    echo -e "${BLUE}Staging changes...${NC}"
    git add .

    echo -e "${YELLOW}Enter commit message:${NC}"
    read -r commit_message

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
        echo -e "${GREEN}b. Back to main menu${NC}"
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
    echo -e "${YELLOW}=====================${NC}"
    echo -e "${YELLOW}Enter your choice:${NC} "
    read server_choice

    case $server_choice in
        [1-9])
            if [ "$server_choice" -le "$server_count" ]; then
                index=$((server_choice-1))
                ip=$(parse_json "$servers_config" ".rsync_servers[$index].ip")
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
        *)
            echo -e "${YELLOW}Invalid choice. Please try again.${NC}"
            sleep 2
            ;;
    esac
}

rsync_to_remote() {
    local user=$1
    local ip=$2
    echo -e "${YELLOW}Enter the local file/directory path to copy:${NC}"
    read local_path
    echo -e "${YELLOW}Enter the remote destination path:${NC}"
    read remote_path
    echo -e "${BLUE}Copying files to remote server $ip...${NC}"
    rsync -avz --progress "$local_path" "$user@$ip:$remote_path"
    echo -e "${GREEN}Rsync operation completed.${NC}"
    sleep 2
}

rsync_from_remote() {
    local user=$1
    local ip=$2
    echo -e "${YELLOW}Enter the remote file/directory path to copy:${NC}"
    read remote_path
    echo -e "${YELLOW}Enter the local destination path:${NC}"
    read local_path
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
        echo -e "${GREEN}3. Rsync File Transfer${NC}"
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
            3)
                rsync_menu
                ;;
            q) 
                echo -e "${BLUE}Thank you for using the Main Management Script. Goodbye!${NC}"
                exit 
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
