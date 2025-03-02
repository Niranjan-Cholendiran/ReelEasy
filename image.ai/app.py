from fastapi import FastAPI, Query
from pydantic import BaseModel
import requests
import base64
import os
import time
from PIL import Image
from typing import List, Dict
from dotenv import load_dotenv
import os
import json
from langchain_community.chat_models import ChatOpenAI
# from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage

# 🔹 Hugging Face API Keys
BLIP2_API_KEY = "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"  # BLIP-2 Captioning
SIMILARITY_API_KEY = "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"  # Sentence Similarity

# 🔹 API Endpoints
BLIP2_API_URL = "https://api-inference.huggingface.co/models/Salesforce/blip-image-captioning-base"
SIMILARITY_API_URL = "https://api-inference.huggingface.co/models/sentence-transformers/all-MiniLM-L6-v2"

# 🔹 Path to Folder Containing Images
IMAGE_FOLDER = "/Volumes/Suite/HackCU-11"

# Initialize FastAPI
app = FastAPI(title="Image Captioning & Ranking API")

# Load environment variables from .env file
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")

# 🔹 ChatGPT API for Word Association
def generate_related_words(input_text):
    prompt = f"""
    You are a creative word assistant.
    Given the descriptive input below, generate exactly 5 words that capture distinct, unique, and diverse aspects related to it.
    Each word should represent a different facet of work typically done in a 24-hour hackathon.
    For example, if the input is "Create a video of me participating in hackathon", 
    you might generate words like "coding", "brainstorm", "collaboration", "energy", and "innovation".
    Return your answer STRICTLY in JSON format with the keys "Word_1", "Word_2", "Word_3", "Word_4", and "Word_5".
    
    Input: "{input_text}"
    
    Example output:
    {{
      "Word_1": "coding",
      "Word_2": "brainstorm",
      "Word_3": "collaboration",
      "Word_4": "energy",
      "Word_5": "innovation"
    }}
    
    """

    # Initialize the ChatOpenAI client
    llm = ChatOpenAI(
        model="gpt-3.5-turbo",
        openai_api_key=openai_api_key,
        temperature=1,
    )
    
    try:
        # Call the model by passing a list with one HumanMessage.
        response = llm([HumanMessage(content=prompt)])
        # Since the response is a single AIMessage, extract its content.
        reply = response.content
        result = json.loads(reply)
        return result
    except Exception as e:
        print("Error generating related words:", e)
        return None

# 🔹 Convert & Save Clean Image Before Uploading
def clean_and_save_image(image_path):
    image = Image.open(image_path).convert("RGB")
    clean_image_path = image_path.replace(".jpg", "_clean.jpg")
    image.save(clean_image_path, "JPEG")
    return clean_image_path

# 🔹 Convert Image to Base64
def encode_image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

# 🔹 Run BLIP Captioning API for an image
def generate_caption(image_path):
    clean_path = clean_and_save_image(image_path)
    base64_image = encode_image_to_base64(clean_path)

    headers = {"Authorization": f"Bearer {BLIP2_API_KEY}"}
    data = {"inputs": base64_image}

    max_retries = 5
    for attempt in range(max_retries):
        response = requests.post(BLIP2_API_URL, headers=headers, json=data)

        if response.status_code == 503:
            print(f"⏳ Model loading... Retrying in 10s ({attempt+1}/{max_retries})")
            time.sleep(10)
            continue
        elif response.status_code == 429:
            print(f"🚨 Rate limit exceeded! Retrying in 30s...")
            time.sleep(30)
            continue
        elif response.status_code != 200:
            print(f"❌ API Error: {response.status_code}, {response.text}")
            return None

        try:
            response_json = response.json()
            if not response_json:
                print("⚠️ Empty response. Retrying...")
                time.sleep(5)
                continue
            return response_json[0]["generated_text"]
        except requests.exceptions.JSONDecodeError:
            print("❌ API Error: Invalid JSON response. Retrying...")
            time.sleep(5)

    return None

# 🔹 Compute Similarity Score
def calculate_similarity(user_prompt, generated_caption):
    headers = {"Authorization": f"Bearer {SIMILARITY_API_KEY}"}
    data = {"inputs": {"source_sentence": generated_caption, "sentences": [user_prompt]}}

    response = requests.post(SIMILARITY_API_URL, headers=headers, json=data)

    if response.status_code == 200:
        return round(response.json()[0] * 100, 2)
    else:
        print(f"❌ Similarity API Error: {response.status_code}, {response.text}")
        return None

# 🔹 Process Images & Rank
def process_and_rank_images(folder_path, user_prompt):
    if "hackathon" in user_prompt.lower():
        user_prompt = "food, group, presentation, shirt, working"

    image_extensions = (".jpg", ".jpeg", ".png", ".heic")
    images = [f for f in os.listdir(folder_path) if f.lower().endswith(image_extensions)]

    if not images:
        print("❌ No images found in the folder.")
        return []

    print(f"\n📂 Processing {len(images)} images in: {folder_path}")

    results = []

    for image in images:
        image_path = os.path.join(folder_path, image)
        print(f"\n🖼️ Processing: {image}")

        generated_caption = generate_caption(image_path)
        if not generated_caption:
            print(f"❌ Failed to generate caption for {image}")
            continue

        similarity_score = calculate_similarity(user_prompt, generated_caption)
        if similarity_score is not None:
            results.append((image_path, generated_caption, similarity_score))

    # 🔹 Sort images based on similarity score (Descending)
    results.sort(key=lambda x: x[2], reverse=True)
    
    return results

# 🔹 API Input Model
class ImageQuery(BaseModel):
    prompt: str
    time: int = Query(..., description="Duration in seconds (1 image per 10s)")

# 🔹 API Endpoint
@app.post("/get_images/")
def get_images(query: ImageQuery):
    prompt = query.prompt
    time_limit = query.time
    n_images = max(1, time_limit // 10)  # Each image = 10 seconds
    result = generate_related_words(prompt)
    if result:
        print("hiiiiiii")
    # Extract words from the result in order and join them as a comma-separated string
        words = [result.get(f"Word_{i}", "") for i in range(1, 6)]
        new_prompt = ", ".join(words)
        print(new_prompt)
    else:
        print("Failed to generate related words.")

    ranked_images = process_and_rank_images(IMAGE_FOLDER, new_prompt)

    # Return only top N images based on time limit
    selected_images = ranked_images[:n_images]

    return {
        "total_images": len(ranked_images),
        "selected_images": len(selected_images),
        "images": [{"path": img[0], "caption": img[1], "similarity": img[2]} for img in selected_images],
    }
