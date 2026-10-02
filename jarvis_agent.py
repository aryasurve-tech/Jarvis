import json
import os
import subprocess
import threading
import time
import webbrowser
from pathlib import Path
from typing import Any

from huggingface_hub import InferenceClient
from colorama import Fore, Style, init

try:
    import pyautogui
except ImportError:
    pyautogui = None

try:
    import pyttsx3
except ImportError:
    pyttsx3 = None

try:
    import speech_recognition as sr
except ImportError:
    sr = None


# ============================================================
# JARVIS - PERSONAL AI AGENT
# ============================================================
# Features:
# - Llama 3.3 70B through Hugging Face/Together
# - Full filesystem discovery/read/write/create
# - Safe terminal with a command allowlist
# - Open apps / websites
# - Screen screenshots
# - Mouse / keyboard control
# - Voice input + voice output
# - Agent swarm / sub-agents
# - Conversation memory
# - Fast tool execution
# - Clean terminal UI
#
# Install:
#   pip install -r requirements.txt
#
# Put your NEW Hugging Face token below.
# ============================================================


init(autoreset=True)

HF_TOKEN = "hf_YOUR_NEW_TOKEN_HERE"
MODEL_ID = "meta-llama/Llama-3.3-70B-Instruct"
PROVIDER = "together"

client = InferenceClient(
    provider=PROVIDER,
    model=MODEL_ID,
    token=HF_TOKEN,
)

HOME = Path.home()
MEMORY_FILE = HOME / ".jarvis_memory.json"
SCREENSHOTS_DIR = HOME / "Pictures" / "JARVIS_Screenshots"
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

conversation = []


# ============================================================
# MEMORY
# ============================================================

def load_memory():
    try:
        if MEMORY_FILE.exists():
            data = json.loads(MEMORY_FILE.read_text(encoding="utf-8"))
            if isinstance(data, list):
                return data
    except Exception:
        pass
    return []


def save_memory(memory):
    try:
        MEMORY_FILE.write_text(
            json.dumps(memory[-100:], indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
    except Exception:
        pass


memory = load_memory()


def remember(text: str):
    memory.append({
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "text": text,
    })
    save_memory(memory)


# ============================================================
# PATHS / COMPUTER INFO
# ============================================================

def resolve_path(path: str) -> Path:
    return Path(path).expanduser().resolve()


def get_computer_info() -> str:
    try:
        lines = [
            f"Username: {HOME.name}",
            f"Home: {HOME}",
            f"OS: {os.name}",
            f"Platform: {os.environ.get('OS', 'unknown')}",
            "",
            "Known folders:",
        ]

        known = {
            "Desktop": HOME / "Desktop",
            "Documents": HOME / "Documents",
            "Downloads": HOME / "Downloads",
            "Pictures": HOME / "Pictures",
            "Videos": HOME / "Videos",
            "Music": HOME / "Music",
        }

        for name, path in known.items():
            if path.exists():
                lines.append(f"{name}: {path}")

        if os.name == "nt":
            lines.append("")
            lines.append("Available drives:")
            for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
                drive = Path(f"{letter}:\\")
                if drive.exists():
                    lines.append(str(drive))

        return "\n".join(lines)
    except Exception as e:
        return f"Unable to inspect computer: {e}"


# ============================================================
# FILESYSTEM
# ============================================================

def list_directory(path=".") -> str:
    try:
        folder = resolve_path(path)

        if not folder.exists():
            return f"Directory does not exist: {folder}"

        if not folder.is_dir():
            return f"Not a directory: {folder}"

        items = sorted(
            folder.iterdir(),
            key=lambda x: (not x.is_dir(), x.name.lower()),
        )

        lines = [f"Directory: {folder}", ""]

        for item in items:
            if item.is_dir():
                lines.append(f"[FOLDER] {item.name}")
            else:
                try:
                    size = item.stat().st_size
                    lines.append(f"[FILE]   {item.name} ({size:,} bytes)")
                except Exception:
                    lines.append(f"[FILE]   {item.name}")

        if len(lines) == 2:
            lines.append("(empty)")

        return "\n".join(lines)

    except Exception as e:
        return f"Unable to list directory: {e}"


def read_file(path: str) -> str:
    try:
        file = resolve_path(path)

        if not file.exists():
            return f"File does not exist: {file}"

        if not file.is_file():
            return f"Not a file: {file}"

        size = file.stat().st_size
        if size > 2_000_000:
            return "File is larger than 2 MB. Read a smaller file or a specific portion."

        try:
            return file.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            return "This is not a normal UTF-8 text file."

    except Exception as e:
        return f"Unable to read file: {e}"


def write_file(path: str, content: str) -> str:
    try:
        file = resolve_path(path)
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(content, encoding="utf-8")
        return f"Written successfully: {file}"
    except Exception as e:
        return f"Unable to write file: {e}"


def create_folder(path: str) -> str:
    try:
        folder = resolve_path(path)
        folder.mkdir(parents=True, exist_ok=True)
        return f"Folder created: {folder}"
    except Exception as e:
        return f"Unable to create folder: {e}"


# ============================================================
# SAFE TERMINAL
# ============================================================
# This intentionally uses an allowlist instead of giving the
# model unrestricted shell execution.
# ============================================================

SAFE_COMMANDS = {
    "dir",
    "where",
    "whoami",
    "hostname",
    "ver",
    "ipconfig",
    "tasklist",
    "systeminfo",
    "python",
    "py",
    "pip",
    "git",
    "node",
    "npm",
    "code",
}


def run_terminal(command: str) -> str:
    try:
        stripped = command.strip()

        if not stripped:
            return "No command supplied."

        first = stripped.split()[0].lower()
        first = Path(first).name.lower()

        if first not in SAFE_COMMANDS:
            return (
                f"Command blocked for safety: {first}. "
                f"Allowed commands: {', '.join(sorted(SAFE_COMMANDS))}"
            )

        result = subprocess.run(
            stripped,
            shell=True,
            capture_output=True,
            text=True,
            timeout=20,
        )

        output = result.stdout.strip()
        error = result.stderr.strip()

        return (
            f"Exit code: {result.returncode}\n"
            f"OUTPUT:\n{output[:12000]}\n"
            f"ERROR:\n{error[:6000]}"
        )

    except subprocess.TimeoutExpired:
        return "Command timed out after 20 seconds."
    except Exception as e:
        return f"Terminal error: {e}"


# ============================================================
# APP / WEBSITE CONTROL
# ============================================================

def open_app(target: str) -> str:
    try:
        if os.name != "nt":
            return "App launching is currently configured for Windows."

        # Windows Start command handles installed apps and URLs.
        subprocess.Popen(
            ["cmd", "/c", "start", "", target],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        return f"Opened: {target}"

    except Exception as e:
        return f"Unable to open {target}: {e}"


def open_website(url: str) -> str:
    try:
        webbrowser.open(url)
        return f"Opened website: {url}"
    except Exception as e:
        return f"Unable to open website: {e}"


# ============================================================
# SCREEN CONTROL
# ============================================================

def take_screenshot() -> str:
    if pyautogui is None:
        return "pyautogui is not installed."

    try:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        path = SCREENSHOTS_DIR / f"screen_{timestamp}.png"
        image = pyautogui.screenshot()
        image.save(path)
        return f"Screenshot saved to: {path}"
    except Exception as e:
        return f"Unable to take screenshot: {e}"


def mouse_click(x: int, y: int, button: str = "left") -> str:
    if pyautogui is None:
        return "pyautogui is not installed."

    if button not in {"left", "right", "middle"}:
        return "Invalid mouse button."

    try:
        pyautogui.click(x=x, y=y, button=button)
        return f"Clicked {button} at ({x}, {y})."
    except Exception as e:
        return f"Mouse error: {e}"


def type_text(text: str) -> str:
    if pyautogui is None:
        return "pyautogui is not installed."

    try:
        pyautogui.write(text, interval=0.01)
        return "Text typed successfully."
    except Exception as e:
        return f"Typing error: {e}"


def press_key(key: str) -> str:
    if pyautogui is None:
        return "pyautogui is not installed."

    allowed = {
        "enter", "esc", "escape", "tab", "space",
        "backspace", "delete", "up", "down", "left",
        "right", "home", "end", "pageup", "pagedown",
        "ctrl", "shift", "alt", "win",
        "f1", "f2", "f3", "f4", "f5", "f6",
        "f7", "f8", "f9", "f10", "f11", "f12",
    }

    key = key.lower()

    if key not in allowed:
        return f"Key blocked. Allowed keys include: {', '.join(sorted(allowed))}"

    try:
        pyautogui.press(key)
        return f"Pressed {key}."
    except Exception as e:
        return f"Keyboard error: {e}"


def hotkey(keys: list[str]) -> str:
    if pyautogui is None:
        return "pyautogui is not installed."

    if not keys or len(keys) > 4:
        return "Hotkey must contain between 1 and 4 keys."

    try:
        pyautogui.hotkey(*keys)
        return f"Pressed hotkey: {' + '.join(keys)}"
    except Exception as e:
        return f"Hotkey error: {e}"


# ============================================================
# VOICE
# ============================================================

tts_engine = None
voice_lock = threading.Lock()

if pyttsx3 is not None:
    try:
        tts_engine = pyttsx3.init()
        tts_engine.setProperty("rate", 185)
        tts_engine.setProperty("volume", 1.0)
    except Exception:
        tts_engine = None


def speak(text: str):
    if tts_engine is None:
        return

    clean = text.replace("*", "").replace("#", "")
    clean = clean[:3000]

    def worker():
        with voice_lock:
            try:
                tts_engine.say(clean)
                tts_engine.runAndWait()
            except Exception:
                pass

    threading.Thread(target=worker, daemon=True).start()


def listen() -> str:
    if sr is None:
        return "SpeechRecognition is not installed."

    recognizer = sr.Recognizer()
    recognizer.pause_threshold = 0.7
    recognizer.energy_threshold = 300

    try:
        with sr.Microphone() as source:
            print(Fore.YELLOW + "Listening...")
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio = recognizer.listen(
                source,
                timeout=8,
                phrase_time_limit=15,
            )

        print(Fore.YELLOW + "Processing voice...")

        text = recognizer.recognize_google(audio)
        return text

    except sr.WaitTimeoutError:
        return ""
    except sr.UnknownValueError:
        return ""
    except sr.RequestError as e:
        return f"Voice recognition service error: {e}"
    except Exception as e:
        return f"Microphone error: {e}"


# ============================================================
# AGENT SWARM
# ============================================================

AGENT_ROLES = {
    "researcher": """
You are the Research Agent.
Find and organize relevant information.
Be factual and concise.
""",
    "coder": """
You are the Coding Agent.
Analyze technical problems, code architecture, bugs,
and implementation details.
""",
    "planner": """
You are the Planning Agent.
Turn complicated goals into practical steps,
dependencies, risks, and execution order.
""",
    "critic": """
You are the Critic Agent.
Review the proposed approach for mistakes,
missing cases, contradictions, and improvements.
""",
    "analyst": """
You are the Analysis Agent.
Break problems into logical components and
compare possible approaches.
""",
}


def run_subagent(role: str, task: str) -> str:
    role_prompt = AGENT_ROLES.get(
        role,
        "You are a general-purpose specialist sub-agent."
    )

    prompt = f"""
{role_prompt}

You are a temporary sub-agent of JARVIS.

Main task:
{task}

Return a concise, useful result for the main JARVIS agent.
Do not pretend to have access to tools you were not given.
"""

    try:
        response = client.chat_completion(
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": task},
            ],
            max_tokens=700,
            temperature=0.4,
        )

        return response.choices[0].message.content

    except Exception as e:
        return f"Sub-agent error: {e}"


def swarm(task: str, roles: list[str]) -> str:
    roles = [r for r in roles if r in AGENT_ROLES]

    if not roles:
        roles = ["planner", "analyst", "critic"]

    results = []

    # Run independent agents concurrently.
    def worker(role):
        result = run_subagent(role, task)
        results.append((role, result))

    threads = []

    for role in roles[:5]:
        thread = threading.Thread(
            target=worker,
            args=(role,),
            daemon=True,
        )
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()

    results.sort(key=lambda item: item[0])

    return "\n\n".join(
        f"=== {role.upper()} AGENT ===\n{result}"
        for role, result in results
    )


# ============================================================
# TOOL DEFINITIONS
# ============================================================

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_computer_info",
            "description": "Discover the real Windows user, home directory, common folders, and drives.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_directory",
            "description": "List files and folders in a real directory on the computer.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a UTF-8 text file from the computer.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Create or replace a text file on the computer.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "content": {"type": "string"},
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_folder",
            "description": "Create a folder on the computer.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_terminal",
            "description": "Run a safe, allowlisted Windows terminal command.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string"},
                },
                "required": ["command"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "open_app",
            "description": "Open a Windows application or installed program.",
            "parameters": {
                "type": "object",
                "properties": {
                    "target": {"type": "string"},
                },
                "required": ["target"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "open_website",
            "description": "Open a website in the default browser.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string"},
                },
                "required": ["url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "take_screenshot",
            "description": "Take a screenshot of the current computer screen.",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "mouse_click",
            "description": "Click at a specific screen coordinate.",
            "parameters": {
                "type": "object",
                "properties": {
                    "x": {"type": "integer"},
                    "y": {"type": "integer"},
                    "button": {
                        "type": "string",
                        "enum": ["left", "right", "middle"],
                    },
                },
                "required": ["x", "y"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "type_text",
            "description": "Type text into the currently focused application.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                },
                "required": ["text"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "press_key",
            "description": "Press an allowed keyboard key.",
            "parameters": {
                "type": "object",
                "properties": {
                    "key": {"type": "string"},
                },
                "required": ["key"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "hotkey",
            "description": "Press a keyboard shortcut such as ctrl+c or alt+tab.",
            "parameters": {
                "type": "object",
                "properties": {
                    "keys": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                },
                "required": ["keys"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "remember",
            "description": "Save a useful user preference or fact to local JARVIS memory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                },
                "required": ["text"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "swarm",
            "description": (
                "Spawn several specialist sub-agents in parallel. "
                "Use this for complicated tasks where research, coding, "
                "planning, analysis, or criticism can be done independently."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "task": {"type": "string"},
                    "roles": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": [
                                "researcher",
                                "coder",
                                "planner",
                                "critic",
                                "analyst",
                            ],
                        },
                    },
                },
                "required": ["task", "roles"],
            },
        },
    },
]


# ============================================================
# TOOL ROUTER
# ============================================================

def execute_tool(name: str, args: dict[str, Any]) -> str:

    if name == "get_computer_info":
        return get_computer_info()

    if name == "list_directory":
        return list_directory(args.get("path", "."))

    if name == "read_file":
        return read_file(args.get("path", ""))

    if name == "write_file":
        return write_file(
            args.get("path", ""),
            args.get("content", ""),
        )

    if name == "create_folder":
        return create_folder(args.get("path", ""))

    if name == "run_terminal":
        return run_terminal(args.get("command", ""))

    if name == "open_app":
        return open_app(args.get("target", ""))

    if name == "open_website":
        return open_website(args.get("url", ""))

    if name == "take_screenshot":
        return take_screenshot()

    if name == "mouse_click":
        return mouse_click(
            int(args.get("x", 0)),
            int(args.get("y", 0)),
            args.get("button", "left"),
        )

    if name == "type_text":
        return type_text(args.get("text", ""))

    if name == "press_key":
        return press_key(args.get("key", ""))

    if name == "hotkey":
        return hotkey(args.get("keys", []))

    if name == "remember":
        remember(args.get("text", ""))
        return "Saved to JARVIS memory."

    if name == "swarm":
        return swarm(
            args.get("task", ""),
            args.get("roles", []),
        )

    return f"Unknown tool: {name}"


# ============================================================
# SYSTEM PROMPT
# ============================================================

SYSTEM_PROMPT = """
You are JARVIS, a capable personal AI computer agent.

PERSONALITY
- Calm
- Intelligent
- Precise
- Practical
- Slightly witty
- Natural
- Never childish
- Never excessively formal

You may call the user "Sir" occasionally.

Do not fill responses with "Certainly", "Absolutely", or
other generic chatbot filler.

Give the useful answer first.

COMPUTER
You can inspect and operate the user's computer using tools.

You can:
- Discover computer information
- Inspect directories
- Read/write text files
- Create folders
- Run allowlisted terminal commands
- Open applications
- Open websites
- Take screenshots
- Click
- Type
- Press keys
- Use keyboard shortcuts

Never claim that a tool succeeded unless its result says so.

PATHS
Never invent Windows usernames or folder paths.
Use get_computer_info when the actual path is unknown.

SCREEN
Use screenshots when useful.
Mouse coordinates refer to the current screen.

TERMINAL
Use run_terminal only for useful, allowlisted commands.
If a command is blocked, do not try to bypass the restriction.

VOICE
Voice is controlled by the local Python application.
Keep spoken responses relatively concise.

MEMORY
Remember only useful long-term preferences or project information
when the user explicitly asks you to remember something.

AGENT SWARM
You have specialist sub-agents:
- researcher
- coder
- planner
- critic
- analyst

For complicated tasks, you may spawn a swarm yourself.
Use parallel specialists when their work can be done independently.
Do not spawn agents for trivial requests.

When using a swarm, synthesize their findings into one clear answer.
Do not dump unnecessary internal discussion on the user.

IMPORTANT
Think before using tools.
Prefer the smallest number of tools necessary.
For simple requests, answer directly.
For computer tasks, actually perform the task rather than merely
explaining how the user could do it.
"""


# ============================================================
# AGENT LOOP
# ============================================================

def ask_jarvis(user_text: str, speak_response: bool = False) -> str:

    conversation.append({
        "role": "user",
        "content": user_text,
    })

    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT,
        }
    ]

    # Add compact memory context.
    if memory:
        recent_memory = memory[-20:]
        memory_text = "\n".join(
            f"- {item['text']}"
            for item in recent_memory
        )

        messages.append({
            "role": "system",
            "content": f"Relevant local memory:\n{memory_text}",
        })

    # Keep conversation bounded for speed.
    messages.extend(conversation[-20:])

    for _ in range(6):

        response = client.chat_completion(
            messages=messages,
            tools=tools,
            max_tokens=1000,
            temperature=0.5,
        )

        message = response.choices[0].message

        if not message.tool_calls:
            answer = message.content or "I have nothing to add."

            conversation.append({
                "role": "assistant",
                "content": answer,
            })

            if speak_response:
                speak(answer)

            return answer

        tool_calls_for_message = []

        for call in message.tool_calls:
            tool_calls_for_message.append({
                "id": call.id,
                "type": "function",
                "function": {
                    "name": call.function.name,
                    "arguments": call.function.arguments,
                },
            })

        messages.append({
            "role": "assistant",
            "content": message.content or "",
            "tool_calls": tool_calls_for_message,
        })

        for call in message.tool_calls:

            try:
                args = json.loads(call.function.arguments)
            except Exception:
                args = {}

            print(
                Fore.MAGENTA +
                f"  [TOOL] {call.function.name}"
            )

            result = execute_tool(
                call.function.name,
                args,
            )

            messages.append({
                "role": "tool",
                "tool_call_id": call.id,
                "content": result,
            })

    answer = "I reached the tool-operation limit for this request."

    conversation.append({
        "role": "assistant",
        "content": answer,
    })

    if speak_response:
        speak(answer)

    return answer


# ============================================================
# UI
# ============================================================

def print_banner():
    print()
    print(Fore.CYAN + "╔════════════════════════════════════════════════════╗")
    print(Fore.CYAN + "║                 J A R V I S                       ║")
    print(Fore.CYAN + "║          PERSONAL COMPUTER AGENT                  ║")
    print(Fore.CYAN + "╚════════════════════════════════════════════════════╝")
    print()
    print(Fore.WHITE + "AI              : ONLINE")
    print(Fore.WHITE + "Filesystem      : ONLINE")
    print(Fore.WHITE + "Terminal        : SAFE MODE")
    print(Fore.WHITE + "Screen control  : ONLINE" if pyautogui else Fore.YELLOW + "Screen control  : INSTALL PYAUTOGUI")
    print(Fore.WHITE + "Voice output    : ONLINE" if tts_engine else Fore.YELLOW + "Voice output    : INSTALL PYTTSX3")
    print(Fore.WHITE + "Voice input     : ONLINE" if sr else Fore.YELLOW + "Voice input     : INSTALL SPEECHRECOGNITION")
    print(Fore.WHITE + "Agent swarm     : ONLINE")
    print()
    print(Fore.YELLOW + "Commands: /voice  /text  /clear  /memory  /help  /exit")
    print()


def main():
    print_banner()

    voice_mode = False

    while True:
        try:

            if voice_mode:
                user_text = listen()

                if not user_text:
                    continue

                print(
                    Fore.GREEN +
                    f"YOU [VOICE] > {user_text}"
                )

            else:
                user_text = input(
                    Fore.GREEN +
                    "YOU > " +
                    Style.RESET_ALL
                ).strip()

            if not user_text:
                continue

            command = user_text.lower()

            if command == "/exit":
                print(Fore.CYAN + "\nJARVIS > Shutting down.")
                break

            if command == "/voice":
                voice_mode = True
                print(Fore.YELLOW + "Voice mode enabled.")
                speak("Voice mode enabled.")
                continue

            if command == "/text":
                voice_mode = False
                print(Fore.YELLOW + "Text mode enabled.")
                continue

            if command == "/clear":
                conversation.clear()
                print(Fore.YELLOW + "Conversation cleared.")
                continue

            if command == "/memory":
                if not memory:
                    print(Fore.YELLOW + "No saved memories.")
                else:
                    for item in memory[-20:]:
                        print(Fore.WHITE + f"- {item['text']}")
                continue

            if command == "/help":
                print(
                    Fore.WHITE +
                    "\n/voice   Enable microphone mode\n"
                    "/text    Return to text mode\n"
                    "/clear   Clear current conversation\n"
                    "/memory  Show local memory\n"
                    "/help    Show commands\n"
                    "/exit    Exit JARVIS\n"
                )
                continue

            print()

            answer = ask_jarvis(
                user_text,
                speak_response=voice_mode,
            )

            print(
                Fore.CYAN +
                "\nJARVIS > " +
                Style.RESET_ALL +
                answer
            )

            print()

        except KeyboardInterrupt:
            print(Fore.CYAN + "\nJARVIS > Shutting down.")
            break

        except Exception as e:
            print(
                Fore.RED +
                f"\nSYSTEM ERROR: {e}\n"
            )


if __name__ == "__main__":
    main()
