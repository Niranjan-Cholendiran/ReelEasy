# 🎮 ReelEasy - Reels Made Easy!

[![GitHub License](https://img.shields.io/github/license/Niranjan-Cholendiran/ClipFuse_AI_V02)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![Gradio](https://img.shields.io/badge/gradio-UI-orange)](https://www.gradio.app/)

## 🚀 Introduction

**ReelEasy** is an AI-powered video generation tool that allows users to create engaging **video clips from prompts** with ease. Using a **FastAPI backend** and a **Gradio-powered frontend**, ReelEasy provides a seamless experience for generating short reels.

## ✨ Features
👉 **AI-Based Video Generation** – Create videos using user prompt and images.  
👉 **Gradio UI** – Easy-to-use interface for interaction.  
👉 **QR Code Uploads** – Upload images using a QR code scanner.  
👉 **Audio Playback** – Upload an audio file for custom voiceover  
👉 **FastAPI Backend** – Handles API requests efficiently.  
👉 **Publicly Shareable Links** – Deploy via Gradio.  

---

## ✨ Architecture

![WhatsApp Image 2025-03-02 at 11 28 06](https://github.com/user-attachments/assets/570dfba1-e639-4f45-8005-d51d2b60830b)




---


## 🛠️ Installation

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/Niranjan-Cholendiran/ClipFuse_AI_V02.git
cd ClipFuse_AI_V02
```

### 2️⃣ Set Up a Virtual Environment (Optional but Recommended)
```bash
python -m venv env
source env/bin/activate  # On macOS/Linux
env\Scripts\activate  # On Windows
```

### 3️⃣ Install Dependencies
```bash
pip install -r requirements.txt
```

### 4️⃣ Run the Gradio App
```bash
python gradio_app.py
```

The app will launch at:  
📍 **Local URL:** `http://127.0.0.1:7860`  
📍 **Public URL:** (if using `share=True`)  

---

## 🎥 How to Use ReelEasy AI
1. **Launch the Gradio app** (`python gradio_app.py`).
2. **Enter a text prompt** (e.g., "create a short video of todays hackathon").
3. **Set a time limit** (duration of the video).
4. **Upload an audio file** (for custom voiceover).
5. **Click "Generate Video"** – The AI will process images and create a video.
6. **Download the generated video**.

---

## 🔗 API Endpoints (FastAPI Backend)
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/get_images/` | `POST` | Generates images based on the prompt |
| `/generate_qr_image/` | `GET` | Returns a QR code for image uploads |
| `/process/` | `POST` | Processes images & creates a final video |

---

## ⚡ Deployment Options
### ✅ **Run Locally**
- Start the FastAPI backend and then run `gradio_app.py`.


---

## 👥 Contributing
We welcome contributions! Follow these steps:
1. **Fork** the repository.
2. **Clone** your fork:
   ```bash
   git clone https://github.com/your-username/ClipFuse_AI_V02.git
   ```
3. **Create a feature branch**:
   ```bash
   git checkout -b feature-new
   ```
4. **Commit changes** and submit a **Pull Request**.

---

## 📝 License
This project is licensed under the **MIT License** – see the [LICENSE](LICENSE) file for details.

