import os
import subprocess
import shlex
import json
import re
from enum import Enum
from openai import OpenAI
import google.generativeai as genai
from typing import List, Dict

class AIModel(Enum):
    DEEPSEEK = "deepseek"
    GEMINI = "gemini"

class SimpleLinuxAssistant:
    COLORS = {
        "command": "\033[33m",   # Yellow
        "output": "\033[90m",    # Gray
        "analysis": "\033[36m",  # Cyan
        "error": "\033[31m",     # Red
        "reset": "\033[0m",
        "chat": "\033[34m",      # Blue
        "warning": "\033[33m",   # Yellow warning
    }

    DANGEROUS_COMMANDS = [
        "rm -rf", "dd", "mkfs", "shred",
        "fdisk", "mv", "chmod 777", "> /dev/sda"
    ]

    def __init__(self, initial_model: AIModel):
        self.ai_model = initial_model
        self.api_keys = {
            AIModel.DEEPSEEK: None,
            AIModel.GEMINI: None
        }
        self.clients = {}
        self.history = []
        self.work_dir = subprocess.getoutput("pwd")
        self.system_context = self.get_system_context()
        self.setup_model(self.ai_model)

    def get_system_context(self) -> Dict:
        """Collect critical system information"""
        return {
            "os": subprocess.getoutput("cat /etc/os-release | grep PRETTY_NAME | cut -d'\"' -f2"),
            "work_dir": self.work_dir,
            "package_manager": "apt" if os.path.exists("/usr/bin/apt") else "rpm",
            "critical_services": subprocess.getoutput("systemctl list-units --type=service --state=running --no-legend | grep -E '(ssh|nginx|apache|postgres|mysql)' | cut -d' ' -f1"),
            "disk_space": subprocess.getoutput("df -h --output=source,pcent,target | grep -v snap"),
            "network_ips": subprocess.getoutput("ip -brief address | awk '{print $1,$3}'"),
            "cpu_cores": os.cpu_count(),
            "memory_total": subprocess.getoutput("free -h | awk '/Mem:/ {print $2}'"),
            "essential_env_vars": "\n".join([f"{k}=[...]" if len(v) > 50 else f"{k}={v}" for k,v in os.environ.items() if k in {'PATH','USER','HOME','LANG'}]),
        }

    def setup_model(self, model: AIModel):
        try:
            if model == AIModel.DEEPSEEK and not self.api_keys[model]:
                key = os.environ.get('DEEPSEEK_API_KEY')
                if not key:
                    key = input("Enter DeepSeek API key: ")
                self.api_keys[model] = key
                self.clients[model] = OpenAI(api_key=key, base_url="https://api.deepseek.com")
            
            elif model == AIModel.GEMINI and not self.api_keys[model]:
                key = os.environ.get('GEMINI_API_KEY')
                if not key:
                    key = input("Enter Google AI API key: ")
                self.api_keys[model] = key
                genai.configure(api_key=key)
                self.clients[model] = genai.GenerativeModel('gemini-2.5-pro-exp-03-25')
        
        except Exception as e:
            print(f"{self.COLORS['error']}Model setup failed: {str(e)}{self.COLORS['reset']}")

    def check_dangerous_command(self, command: str) -> bool:
        """Check if command is potentially dangerous"""
        return any(dc in command for dc in self.DANGEROUS_COMMANDS)

    def execute(self, command: str) -> str:
        try:
            # Safety check
            if self.check_dangerous_command(command):
                confirm = input(f"{self.COLORS['warning']}WARNING: This command is dangerous. Confirm? [y/N] {self.COLORS['reset']}")
                if confirm.lower() != 'y':
                    return "Command cancelled by user\n"

            result = subprocess.run(
		            command,  # Pass the full string, not shlex.split()
		            shell=True,  # Critical for pipes/operators
		            stdout=subprocess.PIPE,
		            stderr=subprocess.PIPE,
		            text=True,
		            timeout=30,  # Optional: Increase for long-running tasks
		            cwd=self.work_dir
		        )
            output = result.stdout if result.returncode == 0 else result.stderr
            output = output if output.endswith('\n') else output + '\n'
            self.history.append({"command": command, "output": output, "success": result.returncode == 0})
            return output
        except Exception as e:
            error_msg = f"Error: {str(e)}\n"
            self.history.append({"command": command, "output": error_msg, "success": False})
            return error_msg

    def remove_markdown(self, text: str) -> str:
        """Remove markdown formatting from text"""
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # Remove bold
        text = re.sub(r'```.*?\n(.*?)```', r'\1', text, flags=re.DOTALL)  # Remove code blocks
        text = re.sub(r'`(.*?)`', r'\1', text)  # Remove inline code
        text = re.sub(r'\* (.*)', r'- \1', text)  # Convert markdown lists to plain
        return text.strip()

    def remove_markdown(self, text: str) -> str:
        """Remove markdown formatting from text"""
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # Remove bold
        text = re.sub(r'```.*?\n(.*?)```', r'\1', text, flags=re.DOTALL)  # Remove code blocks
        text = re.sub(r'`(.*?)`', r'\1', text)  # Remove inline code
        text = re.sub(r'\* (.*)', r'- \1', text)  # Convert markdown lists to plain
        return text.strip()

    def get_ai_response(self, prompt: str, question_mode: bool = False) -> dict:
        context = {
            "system_info": self.system_context,
            "command_history": self.history[-5:]
        }

        history_str = ""
        if question_mode:
            history_entries = []
            for c in context['command_history']:
                entry = f"Command: {c['command']}\nOutput: {c['output']}\nSuccess: {c['success']}"
                history_entries.append(entry)
            history_str = "Recent commands:\n" + "\n".join(history_entries)

        system_prompt = f"""Respond ONLY with valid JSON. Linux expert assistant. Context:
        {json.dumps({k:(v[:75]+'...' if isinstance(v,str) and len(v)>75 else v) for k,v in context['system_info'].items()}, indent=2)}
        {history_str[:200]}...
        Response format:
        {{
            "analysis": "concise technical analysis",
            "commands": ["step1", "step2"],
            "rollback": ["undo-command1", "undo-command2"]
        }}"""

        try:
            if self.ai_model == AIModel.DEEPSEEK:
                response = self.clients[AIModel.DEEPSEEK].chat.completions.create(
                    model="deepseek-chat",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    response_format={"type": "json_object"}
                )
                return json.loads(response.choices[0].message.content)
            
            elif self.ai_model == AIModel.GEMINI:
                response = self.clients[AIModel.GEMINI].generate_content(
                    f"{system_prompt}\nUser question: {prompt}"
                )
                # Handle Gemini's text output format
                if response.text.startswith('```json'):
                    json_str = response.text.split('```json')[1].split('```')[0].strip()
                else:
                    json_str = response.text
                return json.loads(json_str)
        
        except Exception as e:
            return {"error": str(e)}

    def handle_multi_step_task(self, task_description: str):
        """Handle complex tasks with multiple commands"""
        response = self.get_ai_response(f"Break this task into Linux commands: {task_description}")
        
        # Handle potential errors in response
        if "error" in response:
            print(f"{self.COLORS['error']}AI Error: {response['error']}{self.COLORS['reset']}")
            return
            
        commands = response.get("commands", [])
        
        if not commands:
            print(f"{self.COLORS['error']}No commands generated for task{self.COLORS['reset']}")
            return

        print(f"{self.COLORS['analysis']}\nTask Plan:{self.COLORS['reset']}")
        for i, cmd in enumerate(commands, 1):
            print(f"{i}. {cmd}")
        
        confirm = input(f"{self.COLORS['warning']}Run all commands? [y/N] {self.COLORS['reset']}")
        if confirm.lower() != 'y':
            return

        for cmd in commands:
            print(f"\n{self.COLORS['command']}Executing: {cmd}{self.COLORS['reset']}")
            output = self.execute(cmd)
            print(f"{self.COLORS['output']}{output}{self.COLORS['reset']}", end='')

            if "error" in output.lower():
                print(f"{self.COLORS['warning']}\nError detected. Suggesting rollback...{self.COLORS['reset']}")
                if response.get('rollback'):
                    print(f"Rollback commands: {response['rollback']}")
                    rb_confirm = input(f"{self.COLORS['warning']}Run rollback? [y/N] {self.COLORS['reset']}")
                    if rb_confirm.lower() == 'y':
                        for rb_cmd in response['rollback']:
                            self.execute(rb_cmd)
                break

    def generate_script(self, task_description: str):
        """Generate and save a bash script for a task"""
        response = self.get_ai_response(f"Generate executable bash commands for: {task_description}")
        if "error" in response:
            print(f"{self.COLORS['error']}AI Error: {response['error']}{self.COLORS['reset']}")
            return
            
        if response.get('commands'):
            script_name = "generated_script.sh"
            with open(script_name, "w") as f:
                f.write("#!/bin/bash\n\n")
                f.write("# Auto-generated script\n")
                f.write("# Usage: ./generated_script.sh\n\n")
                f.write("\n".join(response['commands']) + "\n")
            os.chmod(script_name, 0o755)
            print(f"{self.COLORS['analysis']}Script saved to {script_name}{self.COLORS['reset']}")
            print(f"Execute with: ./{script_name}")

    def explain_command(self, command: str):
        """Explain a command using man or tldr"""
        try:
            summary = subprocess.getoutput(f"tldr {command} --short")
            if "not found" in summary:
                summary = subprocess.getoutput(f"man {command} | head -n 20")
            print(f"{self.COLORS['analysis']}{summary}{self.COLORS['reset']}")
        except Exception as e:
            print(f"{self.COLORS['error']}Error fetching explanation: {str(e)}{self.COLORS['reset']}")

    def schedule_task(self, task_description: str):
        """Schedule a task using cron"""
        response = self.get_ai_response(f"Generate a cron job for: {task_description}")
        if response.get('commands'):
            cron_job = response['commands'][0]
            print(f"{self.COLORS['analysis']}Cron job: {cron_job}{self.COLORS['reset']}")
            confirm = input(f"{self.COLORS['warning']}Add to crontab? [y/N] {self.COLORS['reset']}")
            if confirm.lower() == 'y':
                self.execute(f"(crontab -l; echo '{cron_job}') | crontab -")
                print(f"{self.COLORS['analysis']}Cron job added.{self.COLORS['reset']}")

    def run(self):
        print(f"{self.COLORS['analysis']}Enhanced Linux Assistant{self.COLORS['reset']}")
        print(f"Current AI model: {self.ai_model.value}\n")
        print("Available commands:")
        print("- ask [question]: Ask about terminal history")
        print("- analyze: Explain last command output")
        print("- task [description]: Run multi-step task")
        print("- script [description]: Generate a bash script")
        print("- explain [command]: Explain a command")
        print("- schedule [description]: Schedule a task with cron")
        print("- chat: Enter chat mode")
        print("- set model [model_name]: Switch AI models")
        print("- log: View command history")
        print("- help: Show available commands")
        print("- exit: Quit the program")
        
        while True:
            try:
                user_input = input(f"\n{self.COLORS['command']}➜ {self.work_dir} ${self.COLORS['reset']} ").strip()

                if user_input.lower() == 'exit':
                    break

                if user_input.lower() == 'help':
                    print("Available commands:")
                    print("- ask [question]: Ask about terminal history")
                    print("- analyze: Explain last command output")
                    print("- task [description]: Run multi-step task")
                    print("- script [description]: Generate a bash script")
                    print("- explain [command]: Explain a command")
                    print("- schedule [description]: Schedule a task with cron")
                    print("- chat: Enter chat mode")
                    print("- set model [model_name]: Switch AI models")
                    print("- log: View command history")
                    print("- help: Show available commands")
                    print("- exit: Quit the program")
                    continue

                if user_input.lower().startswith('set model '):
                    new_model = user_input.split()[-1].lower()
                    try:
                        self.ai_model = AIModel(new_model)
                        if self.ai_model not in self.clients:
                            self.setup_model(self.ai_model)
                        print(f"{self.COLORS['analysis']}Switched to {new_model} model{self.COLORS['reset']}")
                    except ValueError:
                        print(f"{self.COLORS['error']}Invalid model. Available: {[m.value for m in AIModel]}{self.COLORS['reset']}")
                    continue

                if user_input.lower().startswith('task '):
                    task_desc = user_input[5:].strip()
                    self.handle_multi_step_task(task_desc)
                    continue

                if user_input.lower().startswith('script '):
                    task_desc = user_input[7:].strip()
                    self.generate_script(task_desc)
                    continue

                if user_input.lower().startswith('explain '):
                    command = user_input[8:].strip()
                    self.explain_command(command)
                    continue

                if user_input.lower().startswith('schedule '):
                    task_desc = user_input[9:].strip()
                    self.schedule_task(task_desc)
                    continue

                if user_input.lower() == 'log':
                    for entry in self.history:
                        print(f"Command: {entry['command']}")
                        print(f"Output: {entry['output']}")
                        print(f"Success: {entry['success']}\n")
                    continue

                if user_input.lower().startswith('ask '):
                    question = user_input[4:].strip()
                    if not self.history:
                        print(f"{self.COLORS['error']}No history to analyze{self.COLORS['reset']}")
                        continue
                    
                    history_str = "\n".join([f"Command: {c['command']}\nOutput: {c['output'][:200]}" for c in self.history[-5:]])
                    system_prompt = f"""You are a Linux sysadmin assistant. Current directory: {self.work_dir}
                    Recent command history:
                    {history_str}
                    Answer technical questions about these commands and their outputs."""
                    
                    print(f"\n{self.COLORS['analysis']}Q: {question}{self.COLORS['reset']}\n{self.COLORS['analysis']}A: ", end="", flush=True)
                    self.stream_ai_response(question, system_prompt)
                    print()  # Newline after response
                    continue

                if user_input.lower() == 'chat':
                    self.chat_mode()
                    continue

                output = self.execute(user_input)
                print(f"{self.COLORS['output']}{output}{self.COLORS['reset']}", end='')

                if "Error" in output:
                    print(f"{self.COLORS['analysis']}\nGetting suggestions...{self.COLORS['reset']}")
                    response = self.get_ai_response(user_input)  # This stays JSON-based
                    
                    if response.get('commands'):
                        cmd = response['commands'][0]
                        print(f"\n{self.COLORS['command']}Suggested command: {cmd}{self.COLORS['reset']}")
                        confirm = input("Run this? [y/N] ").lower()
                        if confirm == 'y':
                            output = self.execute(cmd)
                            print(f"{self.COLORS['output']}{output}{self.COLORS['reset']}", end='')


            except KeyboardInterrupt:
                print("\nExiting...")
                break
            except Exception as e:
                print(f"{self.COLORS['error']}Error: {str(e)}{self.COLORS['reset']}")



    def chat_mode(self):
        print(f"\n{self.COLORS['analysis']}Chat Mode ({self.ai_model.value}) - Type 'exit' to return{self.COLORS['reset']}")
        chat_history = []

        while True:
            user_msg = input(f"{self.COLORS['command']}You: {self.COLORS['reset']}").strip()
            if user_msg.lower() == 'exit':
                print(f"{self.COLORS['analysis']}Exiting chat mode...{self.COLORS['reset']}")
                return

            try:
                if self.ai_model == AIModel.DEEPSEEK:
                    # DeepSeek streaming (existing implementation)
                    stream = self.clients[AIModel.DEEPSEEK].chat.completions.create(
                        model="deepseek-chat",
                        messages=[
                            {"role": "system", "content": "You are a helpful AI assistant."},
                            *chat_history,
                            {"role": "user", "content": user_msg}
                        ],
                        stream=True
                    )
                    
                    print(f"{self.COLORS['chat']}AI: ", end="", flush=True)
                    full_response = []
                    for chunk in stream:
                        if chunk.choices[0].delta.content:
                            content = chunk.choices[0].delta.content
                            print(content, end="", flush=True)
                            full_response.append(content)
                    print(self.COLORS['reset'])
                    chat_history.extend([
                        {"role": "user", "content": user_msg},
                        {"role": "assistant", "content": "".join(full_response)}
                    ])

                elif self.ai_model == AIModel.GEMINI:
                    # Gemini streaming implementation
                    print(f"{self.COLORS['chat']}AI: ", end="", flush=True)
                    full_response = []
                    
                    # Enable streaming for Gemini
                    response = self.clients[AIModel.GEMINI].generate_content(
                        user_msg,
                        stream=True
                    )
                    
                    # Process streaming chunks
                    for chunk in response:
                        if chunk.text:
                            print(chunk.text, end="", flush=True)
                            full_response.append(chunk.text)
                    
                    print(self.COLORS['reset'])
                    chat_history.extend([
                        {"role": "user", "content": user_msg},
                        {"role": "assistant", "content": "".join(full_response)}
                    ])

            except Exception as e:
                print(f"\n{self.COLORS['error']}Chat error: {str(e)}{self.COLORS['reset']}")

    def stream_ai_response(self, prompt: str, system_prompt: str) -> str:
        try:
            full_response = []
            print(self.COLORS['analysis'], end="", flush=True)

            if self.ai_model == AIModel.DEEPSEEK:
                stream = self.clients[AIModel.DEEPSEEK].chat.completions.create(
                    model="deepseek-chat",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    stream=True
                )
                for chunk in stream:
                    if chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        print(content, end="", flush=True)
                        full_response.append(content)

            elif self.ai_model == AIModel.GEMINI:
                response = self.clients[AIModel.GEMINI].generate_content(
                    f"{system_prompt}\n{prompt}", 
                    stream=True
                )
                for chunk in response:
                    if chunk.text:
                        print(chunk.text, end="", flush=True)
                        full_response.append(chunk.text)

            print(self.COLORS['reset'], end="", flush=True)
            return ''.join(full_response)

        except Exception as e:
            print(f"{self.COLORS['error']}Stream error: {str(e)}{self.COLORS['reset']}")
            return ""

                

if __name__ == "__main__":
    print("Available AI models:")
    for model in AIModel:
        print(f"  - {model.value}")
    
    while True:
        model_choice = input("\nChoose initial model (deepseek/gemini): ").strip().lower()
        try:
            initial_model = AIModel(model_choice)
            break
        except ValueError:
            print(f"Invalid model! Please choose from {[m.value for m in AIModel]}")
    
    assistant = SimpleLinuxAssistant(initial_model)
    try:
        assistant.run()
    except KeyboardInterrupt:
        print("\nExiting cleanly...")