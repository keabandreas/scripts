#!/bin/bash

# Git repositories
declare -A repos=(
    ["Dotfiles"]="$HOME/dotfiles/"
    ["Scripts"]="$HOME/lib/scripts/"
    ["Wallpapers"]="$HOME/lib/images/wallpapers/"
    ["Work"]="$HOME/lib/scripts/work/"
    )

# Perform git operations
perform_git_operations() {
    local repo_path="$1"
    cd "$repo_path" || exit

    git add .
    
    commit_message=$(rofi -dmenu -p "Enter commit message")
    if [ -z "$commit_message" ]; then
        echo "Commit message is empty. Aborting."
        exit 1
    fi

    git commit -m "$commit_message"
    git push

    echo "Git operations completed successfully."
    sleep 2
}

# Main menu
main_menu() {
    local repo_list=""
    for key in "${!repos[@]}"; do
        repo_list+="$key\n"
    done

    local choice=$(echo -e "$repo_list" | rofi -dmenu -p "Select Git Repository" -i)
    
    if [ -n "$choice" ] && [ -n "${repos[$choice]}" ]; then
        perform_git_operations "${repos[$choice]}"
    fi
}

# Start the script
main_menu
