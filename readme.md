# JANUS — AI Ship Systems Interface

JANUS is a custom AI-driven starship interface designed for Discord.  
It provides real-time voice responses, AI-generated dialogue, ship diagnostics, and modular command systems.

This project uses:
- **Discord.py** for Discord integration  
- **Ollama** (local LLM) for AI responses  
- **FFmpeg** + TTS for voice output  
- **JSON files** for persistent ship state and profile management

---

## 🚀 Features

### **AI Voice Interface**
- Text-to-speech output using FFmpeg  
- Connects to Discord voice channels  
- Auto-generates audio responses using a configurable TTS voice  
- Temp audio files automatically cleaned

### **Local AI Brain (Ollama)**
- Real-time responses from a local LLM  
- Configurable model (e.g., `llama3.1`)  
- HTTP-based interaction from the bot

### **Ship Systems & Commands**
JANUS includes modular systems such as:
- `!diagnostics` — system overview  
- `!join` — connect to voice  
- `!leave` — disconnect from voice  
- `!test <message>` — TTS output test  
- `!commands` — list available commands  

### **State & Configuration Files**
- `ship_data.json` — ship profile and static configuration  
- `zone_state.json` — module state, dynamic ship data  

These enable persistent behavior across sessions.

---

## 🛠️ Requirements

### **Software**
- Python 3.10+  
- Discord.py  
- Ollama (running locally)  
- FFmpeg installed (or placed locally)  

### **Python Packages**
Install using:

```bash
pip install discord.py requests
