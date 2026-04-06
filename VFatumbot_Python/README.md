# VFatumbot Python 🐍

A Python port of the [VFatumbot](https://github.com/amoyx/VFatumbot) — the Randonautica-style quantum random location generator app.

## What is this?

This is an **Android application** built with Flet that generates random geographic coordinates using quantum entropy to find statistically anomalous points near your location. Based on the Fatum Project / Randonautica concepts.

### Point Types
- **🔴 Attractor** — Area of high point density (quantum random clustering)
- **🔵 Void** — Area of low point density (quantum random void)
- **⚡ Anomaly** — Any statistically significant pattern
- **🔀 Pair** — Attractor + Void pair
- **🎲 Quantum** — Pure quantum random point
- **🎯 Pseudo** — Pseudo-random point (for comparison)
- **❓ Mystery Point** — Blind point (unknown type)
- **💡 Intent Suggestions** — Random words from dictionary

## Setup

### 1. Install Python 3.10+

### 2. Install dependencies
```bash
cd VFatumbot_Python
pip install -r requirements.txt
```

### 3. Configure
```bash
copy .env.example .env
```
Edit `.env` and set optional:

- `GOOGLE_MAPS_API_KEY` — For map links, water detection, geocoding
- `W3W_API_KEY` — For What3Words addresses

### 4. Run
```bash
python main.py
```

## Architecture

```
VFatumbot_Python/
├── main.py              # Entry point (Flet UI)
├── config.py            # Configuration & constants
├── bot_logic/
│   ├── action_handler.py    # Command execution
│   ├── fatum_functions.py   # Core algorithm (replaces libAttract)
│   ├── helpers.py           # Utilities
│   └── card_factory.py      # URL & button generation
├── models/              # Data models
├── rngs/                # Random number generators
│   ├── quantum_rng.py   # ANU QRNG API client
│   └── pseudo_rng.py    # Fallback for testing
└── storage/
    └── database.py      # SQLite user storage
```

## Key Differences from Original C# Version

| Feature | Original (C#) | Python Port |
|:---|:---|:---|
| Platform | Multi (Telegram, Facebook, Discord, etc.) | Android (Flet) |
| Framework | Microsoft Bot Framework SDK | Flet |
| Database | Azure Cosmos DB | SQLite (local) |
| Attractor Engine | libAttract (C++ DLL) | Pure Python (numpy) |
| RNG Source | ANU QRNG API | ANU QRNG API (same) |
| Config | Hardcoded in Consts.cs | .env file |

## License

Based on the original VFatumbot project.
