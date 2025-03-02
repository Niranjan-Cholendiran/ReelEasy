import requests
import gradio as gr

# 🔹 FastAPI Backend URL
API_URL = "http://127.0.0.1:8000/get_images/"

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
    
    for item in data["images"]:  # Ensure we access "images" key in response
        try:
            image_path = item["path"]
            caption = f"{image_path} - {item['caption']} (Similarity: {item['similarity']}%)"
            
            # Store image path instead of displaying the image
            image_paths.append(image_path)
            captions.append(caption)
        except Exception as e:
            print(f"Error processing image {image_path}: {e}")

    return "\n".join(image_paths), "\n".join(captions)

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

# 🔹 Run Gradio
if __name__ == "__main__":
    gradio_app.launch(share=True)
