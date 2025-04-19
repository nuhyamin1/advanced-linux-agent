# Enhanced Linux Assistant

A powerful terminal-based assistant that combines Linux command execution with AI agent to help with system administration, troubleshooting, and automation tasks.

## Features

- Execute Linux commands with real-time AI suggestions for errors
- Auto-generate multi-step task sequences
- Create executable bash scripts from natural language descriptions
- Schedule tasks with automatic cron job generation
- Get command explanations using man pages or tldr
- Ask questions about your command history and system state
- Chat mode for conversational assistance
- Support for multiple AI models (DeepSeek and Gemini)
- Safety checks for potentially dangerous commands

## Requirements

- Python 3.8+
- API keys for supported AI models (DeepSeek and/or Gemini)

## Installation

1. Clone the repository:
```
git clone https://github.com/nuhyamin1/advanced-linux-agent.git
cd linux-agent
```

2. Install the required dependencies:
```
pip install openai google-generativeai
```

3. Set up environment variables for your API keys (optional):
```
export DEEPSEEK_API_KEY="your-deepseek-api-key"
export GEMINI_API_KEY="your-gemini-api-key"
```

## Usage

Run the assistant:
```
python advanced_linux_agent.py
```

When started, you'll be prompted to choose which AI model to use initially. You can always switch models during your session.

### Available Commands

- Regular Linux commands are executed normally
- Special commands:
  - `ask [question]`: Ask about terminal history
  - `analyze`: Explain last command output
  - `task [description]`: Run multi-step task
  - `script [description]`: Generate a bash script
  - `explain [command]`: Explain a command
  - `schedule [description]`: Schedule a task with cron
  - `chat`: Enter chat mode
  - `set model [model_name]`: Switch AI models
  - `log`: View command history
  - `help`: Show available commands
  - `exit`: Quit the program

### Examples

Generate a script to monitor disk usage:
```
➜ /home/user $ script create a daily disk usage report and email it to admin@example.com
```

Run a multi-step task:
```
➜ /home/user $ task find all log files over 100MB and compress them
```

Get help with an error:
```
➜ /home/user $ netstat -tulpn
Error: netstat: command not found

Getting suggestions...
Suggested command: ss -tulpn
Run this? [y/N] y
```

## Safety Features

The assistant has built-in safety measures:
- Detection of potentially dangerous commands
- Confirmation prompts for risky operations
- Command timeout limits
- Proper shell escaping to prevent injection

## Customization

### Adding New AI Models

To add support for a new AI model:
1. Add a new entry to the `AIModel` enum
2. Update the `setup_model` method to handle the new model's API
3. Modify `get_ai_response` and `stream_ai_response` methods to work with the new model

### Extending Command Set

To add new special commands:
1. Add a new handler method in the `SimpleLinuxAssistant` class
2. Update the `run` method to detect and route to your new handler
3. Add your command to the help text

## Troubleshooting

- **API Key Issues**: If you encounter authentication errors, verify your API keys
- **Command Execution Failures**: Check that you have the necessary permissions
- **Model Switching Problems**: Ensure both models are properly configured

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Uses DeepSeek and Google Gemini APIs for AI assistance
- Inspired by the need for smarter terminal tooling