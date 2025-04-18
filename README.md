# Advanced Linux Agent

This script provides an enhanced command-line assistant for Linux environments. It integrates with AI models (DeepSeek and Gemini) to help users execute commands, automate tasks, understand system operations, and more, directly from the terminal.

## Features

*   **AI-Powered Task Execution:** Break down complex natural language tasks into executable Linux command sequences (`task` command).
*   **Script Generation:** Automatically generate bash scripts based on task descriptions (`script` command).
*   **Command Execution:** Run standard Linux commands directly.
*   **Safety Checks:** Warns before executing potentially dangerous commands (e.g., `rm -rf`, `dd`).
*   **Command Explanation:** Get explanations for Linux commands using `tldr` or `man` (`explain` command).
*   **Task Scheduling:** Generate and add cron jobs for scheduled tasks (`schedule` command).
*   **Context-Aware AI:** Provides system context (OS, running services, disk space, etc.) to the AI for more relevant responses.
*   **Command History Analysis:** Ask questions about recent command history and outputs (`ask` command).
*   **Error Suggestions:** Suggests potential fixes if a command results in an error.
*   **Interactive Chat Mode:** Engage in a general conversation with the selected AI model (`chat` command).
*   **Multiple AI Model Support:** Switch between supported AI models (DeepSeek, Gemini) on the fly (`set model` command).
*   **Command Logging:** View the history of executed commands and their outputs (`log` command).
*   **Color-Coded Output:** Uses terminal colors for improved readability of commands, outputs, and AI analysis.

## Requirements

*   Python 3.x
*   `openai` library (`pip install openai`)
*   `google-generativeai` library (`pip install google-generativeai`)
*   API Key for DeepSeek and/or Google AI (Gemini).
*   Standard Linux utilities (`cat`, `grep`, `cut`, `systemctl`, `df`, `ip`, `free`, `crontab`, `man`).
*   (Optional but Recommended) `tldr` (`sudo apt install tldr` or equivalent) for concise command explanations.

## Installation

1.  **Clone the repository or download the script:**
    ```bash
    # If using git
    # git clone <repository_url>
    # cd <repository_directory>
    # Otherwise, just ensure advanced_linux_agent.py is in your directory
    ```
2.  **Install Python dependencies:**
    ```bash
    pip install openai google-generativeai
    ```
3.  **(Optional) Install tldr:**
    ```bash
    # Debian/Ubuntu
    sudo apt update && sudo apt install tldr

    # Fedora
    sudo dnf install tldr

    # Arch Linux
    sudo pacman -S tldr
    ```

## Configuration

The agent requires API keys for the AI models you intend to use.

*   **Recommended:** Set the keys as environment variables:
    ```bash
    export DEEPSEEK_API_KEY='your_deepseek_api_key'
    export GEMINI_API_KEY='your_google_ai_api_key'
    ```
    You can add these lines to your shell profile (e.g., `~/.bashrc`, `~/.zshrc`) for persistence.

*   **Alternative:** If the environment variables are not set, the script will prompt you to enter the keys manually when you first select a model.

## Usage

1.  **Run the script:**
    ```bash
    python advanced_linux_agent.py
    ```
2.  **Choose an initial AI model:** You will be prompted to select either `deepseek` or `gemini`.
3.  **Interact with the agent:**
    *   Enter standard Linux commands directly (e.g., `ls -l`, `pwd`).
    *   Use the special commands provided by the agent:
        *   `ask [question]`: Ask a question about the recent command history.
        *   `analyze`: (Implicit) Explains the output of the last command if it contained an error or suggests fixes.
        *   `task [description]`: Execute a multi-step task described in natural language.
        *   `script [description]`: Generate a bash script for the described task.
        *   `explain [command]`: Get an explanation for a specific Linux command.
        *   `schedule [description]`: Create a cron job for the described task.
        *   `chat`: Enter interactive chat mode with the AI. Type `exit` to return.
        *   `set model [deepseek|gemini]`: Switch the active AI model.
        *   `log`: Display the command history.
        *   `help`: Show the list of available special commands.
        *   `exit`: Quit the agent.

## Supported AI Models

*   **DeepSeek:** Accessed via the `openai` library pointing to the DeepSeek API endpoint.
*   **Gemini:** Accessed via the `google-generativeai` library.

## Safety Features

The agent includes a basic check for potentially destructive commands (like `rm -rf`, `dd`, `mkfs`). If such a command pattern is detected, it will ask for explicit confirmation (`y/N`) before proceeding. **Always review commands carefully before confirming execution.**
