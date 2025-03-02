import requests
import gradio as gr
from PIL import Image
import io

# 🔹 FastAPI Backend URL
API_URL = "http://127.0.0.1:8000/get_images/"
QR_API_URL = "http://127.0.0.1:8080/generate_qr_image"


# 🔹 Function to fetch QR code image
def get_qr_code():
    response = requests.get(QR_API_URL)
    
    if response.status_code == 200:
        # Convert image data into a PIL Image
        img = Image.open(io.BytesIO(response.content))
        return img
    else:
        return "❌ Failed to load QR Code"


# 🔹 Function to call FastAPI endpoint
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


# 🔹 QR Code Section
qr_code_ui = gr.Interface(
    fn=get_qr_code,
    inputs=[],
    outputs=gr.Image(label="Upload your photos here"),
    title="QR Code for Photo Upload",
    description="Scan this QR code to upload your images.",
)

# 🔹 Create Gradio UI
gradio_app = gr.Interface(
    fn=gradio_interface,
    inputs=[
        gr.Textbox(label="Enter Prompt"),
        gr.Slider(10, 100, step=10, label="Time Limit (seconds)")
    ],
    outputs=[
        gr.Textbox(label="Selected Image Paths", lines=10),  # Display image paths
        gr.Textbox(label="Captions", lines=10)  # Display captions
    ],
    title="🔍 ClipFuse",
    description="Reels made Easy!",
)

# 🔹 Combine Both Interfaces
app = gr.TabbedInterface([qr_code_ui, gradio_app], ["QR Code", "ClipFuse"])

# 🔹 Run Gradio
if __name__ == "__main__":
    app.launch(share=True)
