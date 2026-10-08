<div align="center">

# Camera Alert Bot
# 📷🤖

### A Personal Camera Alert for Telegram

A local Python app that watches your own camera, detects a person, matches known faces, and sends the event to your Telegram chat — with saved events and admin-only commands.

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
![Open Source](https://img.shields.io/badge/Open_Source-Project-black?style=for-the-badge&logo=github)

<br>

[🌐 GitHub Profile](https://github.com/sadra-hatami)
•
[📧 Email](mailto:sadra.hatami.1732@gmail.com)

</div>

---

# 📑 Table of Contents

- [About](#-about)
- [Related Repositories](#-related-repositories)
- [Why This Project?](#-why-this-project)
- [Key Features](#-key-features)
- [Architecture](#-architecture)
- [Project Structure](#-project-structure)
- [Technologies](#️-technologies)
- [Installation](#-installation)
- [Configuration](#️-configuration)
- [Usage](#️-usage)
- [Target Audience](#-target-audience)
- [Roadmap](#️-roadmap)
- [FAQ](#-faq)
- [Security Notes](#-security-notes)
- [Contributing](#-contributing)
- [Contact](#-contact)
- [License](#-license)
- [Copyright](#-copyright)
- [Support](#-support)

---

# 📖 About

**Camera Alert Bot** is a personal camera notifier for Telegram.

It opens a local camera, uses YOLO to find a person, then uses DeepFace to compare the face with people already saved. A known match and an unknown face both become an event. The event photo and a short Persian caption go to one admin chat.

The application is a single file, `bot.py`. Face photos, embeddings, and the event log stay on the machine that runs the script.

> **Tagline:** *A personal camera alert bot that detects a person, matches known faces, and sends the event to Telegram.*

This is for a camera you own. Do not point it at people who have not agreed to be stored.

---

# 🔗 Related Repositories

This bot sits with the other messaging projects in the profile.

| Repository | Role |
|------------|------|
| **[Camera Alert Bot](https://github.com/sadra-hatami/Camera-Alert-Bot)** | Personal camera alert (this repo) |
| **[World War Bot](https://github.com/sadra-hatami/World-War-Bot)** | World strategy game |
| **[Countries War Bot](https://github.com/sadra-hatami/Countries-War-Bot)** | Earlier nation strategy game |
| **[Rubika Group Bot](https://github.com/sadra-hatami/Rubika-Group-Bot)** | Complete group platform |
| **[Rubika Advanced Group Bot](https://github.com/sadra-hatami/Rubika-Advanced-Group-Bot)** | Newest, larger group platform |
| **[Telegram Rubika Account Panel](https://github.com/sadra-hatami/Telegram-Rubika-Account-Panel)** | Telegram panel for a Rubika user account |

Use this repository for a camera alert on your own machine.  
Use the war bots for strategy games.  
Use the group bots for moderation and automation.  
Use the **Account Panel** only to control a user account from Telegram.

---

# 🚀 Why This Project?

A camera demo usually stops at a box on the screen.

This project keeps the loop:

- The camera runs in its own thread
- Person detection is confirmed across several frames
- Known faces are stored as embeddings, not only as names
- Alerts have a cooldown so one person does not spam the chat
- Events are written with a safe JSON save

It shows how vision, local storage, and a messaging bot can sit in one process.

---

# ✨ Key Features

- 📷 Local camera on and off from Telegram
- 🚶 Person detection with YOLO
- 👤 Face match with DeepFace Facenet
- ➕ Add, list, and delete known people
- 📋 Event log with image and timestamp
- ⏱️ Cooldown and confirm-frame settings
- 📐 Optional region of interest
- 🔐 Admin-only commands
- 💾 Safe JSON writes for people, settings, and events

---

# 🏗️ Architecture

```text
Camera
 └─ bot.py
     ├─ YOLO person track
     ├─ DeepFace embedding
     ├─ local JSON store
     └─ Telegram admin chat
```

Detection and the camera run on background threads. Button and command handlers stay on the bot. Secrets belong in environment variables, not in the source file.

---

# 📁 Project Structure

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

# 🛠️ Technologies

- Python 3.10+
- OpenCV
- Ultralytics YOLO
- DeepFace
- pyTelegramBotAPI
- NumPy and Pillow

---

# 🚀 Installation

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

# ⚙️ Configuration

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

# ▶️ Usage

1. Put the token and admin id in the environment.
2. Run `bot.py`.
3. Open the bot in Telegram and send `/start`.
4. Save a face with `/addperson`.
5. Turn the camera on with `/camera_on`.

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

A known face sends a named alert. An unknown face sends an unknown alert. Both are stored in the local event log.

---

# 🎓 Target Audience

- Someone who wants an alert from a camera they own
- Developers studying a vision loop tied to a chat bot
- Students building a messaging portfolio

---

# 🗺️ Roadmap

- Move the token fully to the environment
- A shorter settings editor from chat
- Optional sound on an unknown face
- Clearer notes for the first model download

---

# ❓ FAQ

### Is this a group lock bot?

No. Group tools live in [Rubika Group Bot](https://github.com/sadra-hatami/Rubika-Group-Bot) and [Rubika Advanced Group Bot](https://github.com/sadra-hatami/Rubika-Advanced-Group-Bot).

### Does it need a server?

No. It runs on the computer that has the camera.

### Does it work in a group?

The commands are limited to one admin chat. Alerts go to that same chat.

### Are faces sent to Telegram every frame?

No. A track must stay for several frames, and a cooldown blocks repeat alerts.

### Can the token be published?

No. Use an environment variable only.

---

# 🔐 Security Notes

- Never commit a live bot token or chat id.
- Do not commit face photos, embeddings, or event images.
- Use it only on a camera you control.
- Store a face only with that person's agreement.

---

# 🤝 Contributing

Bug reports, menu polish, and safer configuration are welcome.

---

# 📬 Contact

**Developer:**

### Sadra Hatami

📧 [Email](mailto:sadra.hatami.1732@gmail.com)

🌐 [GitHub](https://github.com/sadra-hatami)

---

# 📄 License

This project is licensed under the **MIT License**.

---

# © Copyright

© 2026 **Sadra Hatami**

All rights reserved.

---

# ⭐ Support

If this bot belongs in a portfolio, please consider giving it a ⭐ on GitHub.

---

<div align="center">

## Designed & Developed with ❤️ for the developer community of Iran and the world by **Sadra Hatami**

</div>
