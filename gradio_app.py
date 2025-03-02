import requests
import gradio as gr
from PIL import Image
import io
import os
import time

# 🔹 FastAPI Backend URLs
API_URL = "http://127.0.0.1:8000/get_images/"
QR_API_URL = "http://127.0.0.1:8080/generate_qr_image"
PROCESS_VIDEO_API = "http://10.203.160.249:5000/process"
FINAL_VIDEO_PATH = "/Volumes/Suite/final_video/final_video.mp4"  # Ensure this is the correct output path

# 🔹 Function to fetch QR code image
def get_qr_code():
    response = requests.get(QR_API_URL)
    if response.status_code == 200:
        img = Image.open(io.BytesIO(response.content))
        return img
    else:
        return "❌ Failed to load QR Code"

# 🔹 Function to process video creation
def generate_video(prompt, time_limit):
    print("Sending request to image API...")
    
    payload = {"prompt": prompt, "time": time_limit}
    image_response = requests.post(API_URL, json=payload)

    if image_response.status_code != 200:
        return "❌ API Error in fetching images!"

    image_data = image_response.json()
    if "error" in image_data:
        return image_data["error"]

    print("Sending response to video processing API...")
    video_response = requests.post(PROCESS_VIDEO_API, json=image_data)

    if video_response.status_code != 200:
        return "❌ Video Processing Failed!"

    # Ensure video file exists before returning
    if os.path.exists(FINAL_VIDEO_PATH):
        print("✅ Video Generated Successfully!")
        return FINAL_VIDEO_PATH  # ✅ Only return the video path
    else:
        print("❌ Video File Not Found!")
        return "❌ Video File Not Found!"

# 🔹 Gradio Layout
with gr.Blocks() as app:
    gr.Markdown("<h1 style='text-align: center;'>ClipFuse.AI</h1>")
    gr.Markdown("<h2 style='text-align: center; color: white;'>Reels Made Easy!!</h2>")

    with gr.Row():
        qr_code_display = gr.Image(value=get_qr_code(), label="Scan QR Code to Upload Photos")

    with gr.Row():
        audio_upload = gr.Audio(label="Upload and Play Audio", type="filepath")  # ✅ Audio Upload (For Playback Only)

    with gr.Column():
        prompt_input = gr.Textbox(label="Enter Prompt")
        time_slider = gr.Slider(10, 100, step=10, label="Time Limit (seconds)")
        submit_button = gr.Button("Generate Video")

    # ✅ Define the Video Output Here (Fixes the issue)
    time.sleep(15)
    video_output = gr.Video(label="Generated Video")

    # ✅ Corrected Event Handling
    submit_button.click(
        fn=generate_video,
        inputs=[prompt_input, time_slider],
        outputs=video_output  # ✅ Correct way to pass video output
    )

if __name__ == "__main__":
    app.launch(share=True, allowed_paths=["/Volumes/Suite/final_video"])
