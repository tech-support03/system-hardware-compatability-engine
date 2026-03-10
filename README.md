# 🖥️ System Hardware Compatibility Engine (SHCE)

> **A Python application that automatically checks whether your PC can run a game — by pulling your live hardware specs, fetching real requirements from Steam, and using AI to give you a detailed performance analysis.**

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue?logo=python&logoColor=white)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Steam API](https://img.shields.io/badge/Steam-API%20Integrated-171a21?logo=steam&logoColor=white)](https://store.steampowered.com/api)
[![Gemini](https://img.shields.io/badge/Google-Gemini%202.5%20Flash-4285F4?logo=google&logoColor=white)](https://aistudio.google.com)

---

## 📖 Overview

SHCE detects your CPU, GPU, RAM, and monitor resolution in real time, looks up a game's system requirements directly from Steam, and sends everything to an AI model to produce a detailed compatibility report — including expected FPS, recommended graphics settings, and any hardware bottlenecks.

No more guessing. No more manually comparing spec sheets.

---

## 🗂️ Project Structure

This repository contains **four prototypes** and an **archive** of exploratory scripts that document the development process.

```
system-hardware-compatability-engine/
│
├── archive/                     # Standalone exploratory scripts (pre-prototype)
│   ├── system.py                # Full hardware diagnostic (prints to console)
│   ├── system2.py               # Refactored hardware module (callable functions)
│   ├── monitor_resolution.py    # Screen resolution detection proof of concept
│   ├── requirements.py          # Steam API game requirements fetcher
│   ├── query.py                 # LLM communication test (OpenAI SDK → LM Studio)
│   ├── GUI.py                   # Early Tkinter UI shell (stubbed logic)
│   └── backend.py               # First integrated pipeline (hardware + Steam + LLM)
│
├── gemini/                      # Prototype 1 & 2 (Eel web app variants)
│   ├── GeminiOnly.py            # Proto 1: Gemini AI only, no Steam API
│   ├── steamAPI_Gemini.py       # Proto 2 (web): Steam API + Gemini, Eel frontend
│   ├── main.py                  # Proto 2 (desktop): Steam API + Gemini, Tkinter UI
│   └── web/
│       └── index.html           # Shared dark-mode web frontend (Tailwind CSS)
│
├── local-ai/                    # Prototype 3 & 4 (fully local AI, no API key needed)
│   ├── SteamAPI_Local.py        # Proto 3: Steam API + HuggingFace Transformers
│   ├── SteamAPI_LlamaCCP.py     # Proto 4: Steam API + llama-cpp-python (GGUF)
│   └── web/
│       └── index.html           # Shared dark-mode web frontend
│
└── requirements.txt             # All Python dependencies
```

---

## 🚀 The Four Prototypes

| # | Name | AI Backend | Requirements Source | Interface | API Key? |
|---|------|-----------|--------------------|-----------|---------:|
| 1 | **GeminiOnly** | Gemini 2.5 Flash | Gemini training data | Eel web UI | Yes |
| 2 | **SteamAPI + Gemini** | Gemini 2.5 Flash | Live Steam API | Tkinter + Eel web | Yes |
| 3 | **SteamAPI + Local AI** | Phi-3.5-mini (HuggingFace) | Live Steam API | Eel web UI | No |
| 4 | **SteamAPI + LlamaCPP** | Llama-3.2-3B (GGUF) | Live Steam API | Eel web UI | No |

---

## ⚡ Quick Start

### Prototype 2 — SteamAPI + Gemini (Recommended)

The best balance of accuracy and ease of setup.

**1. Clone the repo**
```bash
git clone https://github.com/tech-support03/system-hardware-compatability-engine.git
cd system-hardware-compatability-engine
```

**2. Install dependencies**
```bash
pip install -r requirements.txt
```

**3. Set your Google AI API key**

Create a `.env` file in the `gemini/` folder:
```
GOOGLE_AI_API_KEY=your_api_key_here
```
> Get a free API key at [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)

**4. Run the app**

*Web UI version (recommended):*
```bash
cd gemini
python steamAPI_Gemini.py
```

*Desktop Tkinter version:*
```bash
cd gemini
python main.py
```

---

## 🛠️ All Prototypes — Setup Guide

### Prototype 1 — GeminiOnly
```bash
cd gemini
# Create .env with GOOGLE_AI_API_KEY=your_key
python GeminiOnly.py
```
> Uses Gemini to both recall game requirements **and** analyse your hardware. No Steam API call required.

---

### Prototype 2 — SteamAPI + Gemini *(Best accuracy)*
```bash
cd gemini
# Create .env with GOOGLE_AI_API_KEY=your_key
python steamAPI_Gemini.py   # Eel web UI
# OR
python main.py              # Tkinter desktop UI
```
> Fetches live requirements from Steam, then uses Gemini for hardware analysis.

---

### Prototype 3 — SteamAPI + Local AI *(No API key needed)*
```bash
pip install transformers torch
cd local-ai
python SteamAPI_Local.py
```
> Downloads `microsoft/Phi-3.5-mini-instruct` (~2.2 GB) automatically on first run.  
> Requires 7–8 GB VRAM for GPU inference, or falls back to CPU (slower).

---

### Prototype 4 — SteamAPI + LlamaCPP *(Fast local inference)*
```bash
pip install llama-cpp-python
```
Download a GGUF model and place it in `local-ai/models/`:
- Recommended: [`Llama-3.2-3B-Instruct-Q4_K_M.gguf`](https://huggingface.co/models?library=gguf) (~2 GB)

```bash
cd local-ai
python SteamAPI_LlamaCCP.py
```
> Update `MODEL_PATH` in the script if your filename differs.  
> Runs on machines with as little as 4 GB RAM. No GPU required.

---

## 📦 Dependencies

```
requests
beautifulsoup4
psutil
screeninfo
eel
google-generativeai
python-dotenv
openai
transformers      # Prototype 3 only
torch             # Prototype 3 only
llama-cpp-python  # Prototype 4 only
```

Install everything:
```bash
pip install -r requirements.txt
```

---

## 🔍 How It Works

```
┌─────────────────────────────────────────────────────────┐
│                      User Input                         │
│                  "Can I run Cyberpunk?"                 │
└───────────────────────┬─────────────────────────────────┘
                        │
           ┌────────────▼────────────┐
           │   Hardware Detection    │
           │  CPU · GPU · RAM · Res  │
           │  (psutil + subprocess)  │
           └────────────┬────────────┘
                        │
           ┌────────────▼────────────┐
           │    Steam API Lookup     │  ← Prototypes 2, 3, 4
           │  Search → App Details  │
           │  BeautifulSoup cleanup  │
           └────────────┬────────────┘
                        │
           ┌────────────▼────────────┐
           │      AI Analysis        │
           │  Gemini / Phi / Llama   │
           │  FPS · Settings · Score │
           └────────────┬────────────┘
                        │
           ┌────────────▼────────────┐
           │       Results UI        │
           │  Web (Eel) or Tkinter   │
           └─────────────────────────┘
```

---

## 🖼️ Interface Preview

The web UI (shared across Prototypes 1, 2, 3, 4) features:

- **Dark mode** design with Tailwind CSS
- **Live sidebar** showing your detected GPU and CPU on load
- **Three UI states** — loading, error, and results
- **Hardware spec grid** — CPU, GPU, RAM, OS, resolution, storage
- **AI analysis panel** — plain-language compatibility report

---

## 🧠 GPU Detection

All prototypes use a two-tier GPU classification system to handle laptops and remote desktop setups:

1. **Virtual adapter filter** — removes Parsec, VNC, TeamViewer, RDP, Citrix, VMware, Hyper-V, and Standard VGA entries
2. **Dedicated vs. integrated classification** — prefers discrete NVIDIA/AMD GPUs over Intel UHD / Intel Iris / integrated Radeon Graphics

This ensures the application always reports your real gaming GPU, not a remote desktop virtual adapter.

---

## ⚖️ Choosing a Prototype

| Your situation | Recommended prototype |
|---|---|
| Want the most accurate results | **Prototype 2** (SteamAPI + Gemini) |
| Want the simplest setup | **Prototype 1** (GeminiOnly) |
| No API key, high-end GPU available | **Prototype 3** (Local AI / Transformers) |
| No API key, any hardware | **Prototype 4** (LlamaCPP / GGUF) |

---

## 📄 Documentation

Full project documentation (10–15 pages) is available in the repository covering the architecture of all four prototypes, hardware detection strategy, AI prompt design, and scientific findings.

---

## 👥 Authors

- **Arjun Khedkar** ([@tech-support03](https://github.com/tech-support03))
- **Amogh Dhekane** ([@swimsamurai](https://github.com/swimsamurai))

*Built as a science project exploring AI-assisted hardware compatibility analysis.*

---

## 📝 License

This project is open source under the [MIT License](LICENSE).