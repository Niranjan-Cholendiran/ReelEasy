import requests
import gradio as gr
from PIL import Image
import io
import os
import shutil

# 🔹 FastAPI Backend URLs
API_URL = "http://127.0.0.1:8000/get_images/"
QR_API_URL = "http://127.0.0.1:8080/generate_qr_image"
MEDIA_SAVE_PATH = "saved_audio/"  # Directory to save uploaded audio

# 🔹 Ensure the directory exists
os.makedirs(MEDIA_SAVE_PATH, exist_ok=True)

# 🔹 Function to fetch QR code image
def get_qr_code():
    response = requests.get(QR_API_URL)
    
    if response.status_code == 200:
        # Convert image data into a PIL Image
        img = Image.open(io.BytesIO(response.content))
        return img
    else:
        return "❌ Failed to load QR Code"

# 🔹 Function to call FastAPI endpoint (without audio file)
def gradio_interface(prompt, time_limit):
    # Prepare JSON payload
    payload = {
        "prompt": prompt,
        "time": time_limit
    }

    # Call FastAPI API with JSON body
    response = requests.post(API_URL, json=payload)
    print(response.status_code)

    if response.status_code != 200:
        return "❌ API Error!", None

    data = response.json()
    if "error" in data:
        return data["error"], None

    # Process received image paths & captions
    image_paths = []
    captions = []

    for item in data.get("images", []):  # Ensure we access "images" key in response
        try:
            image_path = item.get("path", "Unknown Path")
            caption = f"{image_path} - {item.get('caption', 'No caption')} (Similarity: {item.get('similarity', 'N/A')}%)"

            # Store image path instead of displaying the image
            image_paths.append(image_path)
            captions.append(caption)
        except Exception as e:
            print(f"Error processing image {image_path}: {e}")

    return "\n".join(image_paths), "\n".join(captions)

# 🔹 Function to save video and return path for playback and download
def save_video(video_file):
    if video_file and os.path.exists(video_file):
        filename = os.path.basename(video_file)
        saved_path = os.path.join(MEDIA_SAVE_PATH, filename)

        shutil.copy(video_file, saved_path)  # Save the file

        # ✅ Return the saved file path for playback and download
        return saved_path, saved_path
    return None, None

# 🔹 Gradio Layout
with gr.Blocks() as app:
    # Title & Subtitle (Center-Aligned)
    with gr.Column(elem_id="title_section"):
        gr.Markdown("<h1 style='text-align: center;'>ClipFuse.AI</h1>", elem_id="title")
        gr.Markdown("<h2 style='text-align: center; color: white;'>Reels Made Easy!!</h2>", elem_id="subtitle")

    # QR Code (Centered at the Top)
    with gr.Row():
        qr_code_display = gr.Image(value=get_qr_code(), label="Scan QR Code to Upload Photos", show_label=True)

    # Audio Upload (Single Component for Upload + Playback with source)
    with gr.Row():
        audio_upload = gr.Audio(label="Upload and Play Audio", type="filepath", value=None)  # ✅ Set source later

    with gr.Row():
        # video_upload = gr.File(label="Upload Video", type="filepath", file_types=[".mp4", ".avi", ".mov"])
        video_upload = gr.Video(label="Upload Video")

    # Prompt, Time Slider & Generate Button
    with gr.Column():
        prompt_input = gr.Textbox(label="Enter Prompt")
        time_slider = gr.Slider(10, 100, step=10, label="Time Limit (seconds)")
        submit_button = gr.Button("Generate")

    # Output Section
    selected_image_paths = gr.Textbox(label="Selected Image Paths", lines=5)
    selected_captions = gr.Textbox(label="Captions", lines=5)

    # Event Handling
    submit_button.click(
        fn=gradio_interface,
        inputs=[prompt_input, time_slider],
        outputs=[selected_image_paths, selected_captions],
    )


# 🔹 Run Gradio
if __name__ == "__main__":
    app.launch(share=True)

