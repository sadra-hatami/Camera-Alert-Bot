<div align="center">

# Camera Alert Bot
# 📷🤖

### A Personal Camera Alert for Telegram

A local Python app that watches your own camera, detects a person, matches known faces, and sends the event to your Telegram chat.

<br>

# 👨‍💻 **Sadra Hatami**

### *Developer • Software Engineer • Creator*

<br>

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![OpenCV](https://img.shields.io/badge/OpenCV-Camera-5C3EE8?style=for-the-badge&logo=opencv&logoColor=white)](https://opencv.org/)
[![YOLO](https://img.shields.io/badge/YOLO-Ultralytics-111F68?style=for-the-badge)](https://docs.ultralytics.com/)
[![DeepFace](https://img.shields.io/badge/DeepFace-Facenet-1ABC9C?style=for-the-badge)](https://github.com/serengil/deepface)
[![Telegram](https://img.shields.io/badge/Telegram-Bot%20API-26A5E4?style=for-the-badge&logo=telegram&logoColor=white)](https://core.telegram.org/bots/api)
[![Persian](https://img.shields.io/badge/Commands-Persian-success?style=for-the-badge)](https://en.wikipedia.org/wiki/Persian_language)
[![License](https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge)](https://opensource.org/license/mit)

<br>

[🌐 GitHub Profile](https://github.com/sadra-hatami)
•
[📧 Email](mailto:sadra.hatami.1732@gmail.com)

</div>

---

# About

**Camera Alert Bot** is a personal camera notifier.

It opens a local camera, uses YOLO to find a person, then uses DeepFace to compare the face with people you already saved. A known match and an unknown face both become an event. The event photo and a short caption go to one Telegram admin chat.

The bot commands are Persian. The camera, face store, and event log stay on the machine that runs the script.

> **Tagline:** *A personal camera alert bot that detects a person, matches known faces, and sends the event to Telegram.*

This is for a camera you own. Do not point it at people who have not agreed to be stored.

---

# Why this project

A camera demo usually stops at a box on the screen.

This one keeps the loop:

- The camera runs in its own thread
- Person detection is confirmed across several frames
- Known faces are stored as embeddings, not only as names
- Alerts have a cooldown so one person does not spam the chat
- Events are written with a safe JSON save

It is a portfolio piece for connecting vision, storage, and a messaging bot.

---

# Features

- Local camera on and off from Telegram
- Person detection with YOLO
- Face match with DeepFace Facenet
- Add, list, and delete known people
- Event log with image and timestamp
- Cooldown and confirm-frame settings
- Optional region of interest
- Admin-only commands
- Safe JSON writes for people, settings, and events

---

# Commands

| Command | Role |
|---|---|
| `/start` | Main menu and counts |
| `/status` | Camera, people, events, and settings |
| `/camera_on` | Start the camera |
| `/camera_off` | Stop the camera |
| `/addperson` | Save a new face from a photo |
| `/list` | List saved people |
| `/deleteperson` | Remove a saved person |
| `/events` | Recent events |
| `/settings` | Current thresholds |
| `/help` | Command list |

Only the configured admin chat can use these commands.

---

# Project structure

```text
Camera-Alert-Bot/
├── bot.py
├── data/          # created at runtime — do not commit
├── faces/         # created at runtime — do not commit
├── events/        # created at runtime — do not commit
├── models/        # YOLO weights — optional, do not commit large files
└── README.md
```

`bot.py` is the application: camera loop, detection, face store, and Telegram handlers.

---

# Technologies

- Python 3.10+
- OpenCV
- Ultralytics YOLO
- DeepFace
- pyTelegramBotAPI
- NumPy and Pillow

---

# Installation

```bash
git clone https://github.com/sadra-hatami/Camera-Alert-Bot.git
cd Camera-Alert-Bot
pip install opencv-python numpy ultralytics deepface pyTelegramBotAPI Pillow
```

```bash
python bot.py
```

The first run can download the YOLO weights. Keep that file out of git if it is large.

---

# Configuration

Put the token and admin chat id in environment variables, not in the source file.

```text
TELEGRAM_BOT_TOKEN
TELEGRAM_ADMIN_CHAT_ID
```

`.gitignore`:

```text
.env
data/
faces/
events/
models/
__pycache__/
```

---

# Usage

1. Set the token and admin id.
2. Run `bot.py`.
3. Open the bot in Telegram and send `/start`.
4. Save a face with `/addperson`.
5. Turn the camera on with `/camera_on`.

A known face sends a named alert. An unknown face sends an unknown alert. Both are stored in the local event log.

---

# Security notes

- Never commit a live bot token or chat id.
- Do not commit face photos, embeddings, or event images.
- Use it only on a camera you control.
- Store a face only with that person's agreement.

---

# FAQ

### Does it need a server?

No. It runs on the computer that has the camera.

### Does it work in a group?

The commands are limited to one admin chat. Alerts go to that same chat.

### Are faces sent to Telegram every frame?

No. A track must stay for several frames, and a cooldown blocks repeat alerts.

---

# Contact

### Sadra Hatami

📧 [Email](mailto:sadra.hatami.1732@gmail.com)

🌐 [GitHub](https://github.com/sadra-hatami)

---

# License

This project is licensed under the MIT License.

---

<div align="center">

## Designed and developed with care by **Sadra Hatami**

</div>
