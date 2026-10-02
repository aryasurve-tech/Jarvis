# 🤖 JARVIS: Personal AI Computer Agent

A terminal-based AI agent that can operate your computer: browse your filesystem, run safe commands, open apps and sites, take screenshots, control the mouse and keyboard, talk and listen, and spin up parallel sub-agents for complex tasks.

Powered by **Llama 3.3 70B Instruct** via Hugging Face Inference Providers (Together).

---

## ✨ Features

| Feature | What it does |
|---|---|
| **Tool-calling agent** | The LLM decides which tools to use and chains up to 6 tool calls per request |
| **Filesystem access** | List directories, read text files (up to 2 MB), write files, create folders |
| **Restricted terminal** | Runs only allowlisted commands, with a 20s timeout |
| **App / website launcher** | Opens Windows apps and URLs |
| **Screen control** | Screenshots, mouse clicks, typing, key presses, hotkeys (via PyAutoGUI) |
| **Voice I/O** | Speech-to-text input and text-to-speech replies |
| **Agent swarm** | Runs up to 5 specialist sub-agents in parallel (researcher, coder, planner, critic, analyst) |
| **Persistent memory** | Saves facts you ask it to remember in a local JSON file |
| **Clean terminal UI** | Colored output with a status banner |

---

## 📋 Requirements

- **Python 3.9+**
- **Windows** (app launching and several tool descriptions are Windows-specific; other OSes are untested)
- A **Hugging Face access token** with Inference Providers permission
- A microphone and speakers (only for voice mode)

### Python dependencies

```
huggingface_hub
colorama
pyautogui
pyttsx3
SpeechRecognition
PyAudio
```

> `pyautogui`, `pyttsx3`, and `SpeechRecognition` are optional at runtime. JARVIS still starts without them and just disables those features.

---

## 🚀 Installation

```bash
# 1. Clone the repo
git clone https://github.com/<your-username>/<your-repo>.git
cd <your-repo>

# 2. (Recommended) create a virtual environment
python -m venv venv
venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
```

**PyAudio won't install?** On Windows, install a prebuilt wheel:

```bash
pip install pipwin
pipwin install pyaudio
```

---

## 🔑 Configuration

Open `jarvis_agent.py` and set your token:

```python
HF_TOKEN = "hf_YOUR_NEW_TOKEN_HERE"
```

Get a token at [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens).

**⚠️ Never commit your real token to GitHub.** Safer option: load it from an environment variable.

```python
HF_TOKEN = os.environ["HF_TOKEN"]
```

```bash
set HF_TOKEN=hf_xxxxxxxxxxxx
```

Other settings at the top of the file:

| Variable | Default | Description |
|---|---|---|
| `MODEL_ID` | `meta-llama/Llama-3.3-70B-Instruct` | Model to use |
| `PROVIDER` | `together` | Inference provider |

---

## ▶️ Usage

```bash
python jarvis_agent.py
```

You'll see the status banner, then a `YOU >` prompt. Just type what you want.

### Example prompts

```
YOU > What's in my Downloads folder?
YOU > Create a folder called "projects" on my Desktop and add a README.md inside it
YOU > Open YouTube
YOU > Take a screenshot
YOU > Remember that I prefer Python over JavaScript
YOU > Use your sub-agents to plan a launch strategy for a SaaS product
```

### In-app commands

| Command | Description |
|---|---|
| `/voice` | Switch to microphone input (replies are spoken aloud) |
| `/text` | Switch back to keyboard input |
| `/clear` | Clear the current conversation |
| `/memory` | Show saved memories |
| `/help` | List commands |
| `/exit` | Quit |

---

## 🧰 Available Tools

| Tool | Description |
|---|---|
| `get_computer_info` | Detects username, home directory, known folders, and drives |
| `list_directory` | Lists files and folders in a path |
| `read_file` | Reads a UTF-8 text file (max 2 MB) |
| `write_file` | Creates or overwrites a text file |
| `create_folder` | Creates a folder (including parents) |
| `run_terminal` | Runs an allowlisted command |
| `open_app` | Launches a Windows app or target |
| `open_website` | Opens a URL in the default browser |
| `take_screenshot` | Saves a screenshot to `~/Pictures/JARVIS_Screenshots` |
| `mouse_click` | Clicks at screen coordinates (left / right / middle) |
| `type_text` | Types text into the focused window |
| `press_key` | Presses a key from a fixed allowed list |
| `hotkey` | Presses a shortcut of up to 4 keys (e.g. `ctrl+c`) |
| `remember` | Saves a note to local memory |
| `swarm` | Runs parallel specialist sub-agents |

### Terminal allowlist

```
dir, where, whoami, hostname, ver, ipconfig, tasklist,
systeminfo, python, py, pip, git, node, npm, code
```

Edit `SAFE_COMMANDS` in `jarvis_agent.py` to change it.

---

## 🧠 Agent Swarm

For complex tasks, JARVIS can spawn specialist sub-agents that work **in parallel** and report back. The main agent then combines their output into one answer.

| Role | Focus |
|---|---|
| `researcher` | Finding and organizing information |
| `coder` | Code architecture, bugs, implementation |
| `planner` | Steps, dependencies, risks, order of execution |
| `critic` | Mistakes, edge cases, contradictions |
| `analyst` | Breaking problems down, comparing approaches |

Sub-agents are plain LLM calls. They don't have tool access.

---

## 💾 Data & Storage

| What | Where |
|---|---|
| Memory | `~/.jarvis_memory.json` (last 100 entries) |
| Screenshots | `~/Pictures/JARVIS_Screenshots/` |
| Conversation | In memory only; the last 20 messages are sent to the model and everything is lost on exit |

---

## 🔒 Security & Privacy

This agent can read/write files and control your mouse and keyboard. Treat it accordingly.

- **Run it only on a machine you control.** Don't point it at untrusted content (web pages, documents) that could contain prompt injections.
- **The terminal allowlist is not a sandbox.** Commands like `python`, `pip`, `git`, `node`, and `npm` can execute arbitrary code, and only the first word of the command is checked. Remove those from `SAFE_COMMANDS` if you want a stricter setup.
- **Filesystem tools are unrestricted.** The model can read and overwrite any file your user account can.
- **Your data goes to a third party.** File contents, screenshots paths, and your prompts are sent to Hugging Face / Together as part of the conversation.
- **Voice input uses Google's online speech recognition**, so audio is sent to Google.
- **PyAutoGUI failsafe:** slam the mouse into a screen corner to abort runaway automation.
- **Never commit your Hugging Face token.**

---

## 🛠️ Troubleshooting

| Problem | Fix |
|---|---|
| `Screen control: INSTALL PYAUTOGUI` | `pip install pyautogui` |
| `Voice output: INSTALL PYTTSX3` | `pip install pyttsx3` |
| `Voice input: INSTALL SPEECHRECOGNITION` | `pip install SpeechRecognition PyAudio` |
| `Microphone error` | Check your default input device and mic permissions |
| Auth / 401 errors | Check your token and its Inference Providers permission |
| "App launching is currently configured for Windows" | `open_app` is Windows-only |
| "Reached the tool-operation limit" | Break the request into smaller steps |

---

## 🗺️ Roadmap Ideas

- [ ] Confirmation prompts before file writes and clicks
- [ ] Path sandboxing for filesystem tools
- [ ] macOS / Linux support for app launching
- [ ] Wake-word activation
- [ ] Tool access for sub-agents

---

## 📄 License

Add your license here (e.g. MIT).

---

## 🙌 Acknowledgements

- [Hugging Face](https://huggingface.co/) for Inference Providers
- [Meta](https://ai.meta.com/) for Llama 3.3
- [PyAutoGUI](https://github.com/asweigart/pyautogui), [pyttsx3](https://github.com/nateshmbhat/pyttsx3), [SpeechRecognition](https://github.com/Uberi/speech_recognition)
