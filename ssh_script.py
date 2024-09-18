import json
import os
import subprocess
import sys

# Load configuration
with open('config.json', 'r') as config_file:
    config = json.load(config_file)

SERVERS = config['servers']
DOCKER_CONTAINERS = config['docker_containers']

# ... (rest of your imports and constants)

def print_ssh_menu():
    """Print the server selection menu."""
    clear_screen()
    print("=== SSH Server Connection Menu ===")
    for key, server in SERVERS.items():
        print(f"{key}. {server['name']} ({server['user']}@{server['host']})")
    print("b. Back to main menu")
    print("q. Quit")
    print("===================================")

def print_docker_server_menu():
    """Print the Docker server selection menu."""
    clear_screen()
    print("=== Docker Server Selection Menu ===")
    for key, server in SERVERS.items():
        if server['server'] == 'docker':
            print(f"{key}. {server['name']} ({server['host']})")
    print("b. Back to main menu")
    print("q. Quit")
    print("=====================================")

def print_docker_container_menu(server_host):
    """Print the Docker container selection menu for a specific server."""
    clear_screen()
    server_name = next(server['name'] for server in SERVERS.values() if server['host'] == server_host)
    print(f"=== Docker Container Connection Menu for {server_name} ===")
    for key, container in DOCKER_CONTAINERS[server_host].items():
        print(f"{key}. {container['name']}")
    print("b. Back to Docker server selection")
    print("q. Quit")
    print("=======================================================")

# ... (rest of your functions)

def main():
    # ... (your main function logic)

if __name__ == "__main__":
    main()