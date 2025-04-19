import openai
import requests
import time
import random
import cloudinary
import cloudinary.uploader
import base64
import os
from datetime import datetime

# 🔐 API Ključi iz okolja
openai.api_key = os.getenv("OPENAI_API_KEY")
ELEVEN_API_KEY = os.getenv("ELEVEN_API_KEY")
DID_API_KEY = os.getenv("DID_API_KEY")
IG_USER_ID = os.getenv("IG_USER_ID")
FB_PAGE_ID = os.getenv("FB_PAGE_ID")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")

# ☁️ Cloudinary
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

# 🎨 AI vizualni stili
visual_styles = [
    "digital goddess with glowing tattoos",
    "hyper-realistic AI woman with futuristic braids",
    "sci-fi queen in chrome armor and soft neon light",
    "elegant AI model with cybernetic facial lines",
    "ultra-detailed woman with liquid metal outfit"
]

def post_once():
    logs = []
    def log(msg):
        print(msg)
        logs.append(msg)

    categories = {
        "luxury": [
            "posing beside a futuristic Rolls Royce",
            "standing in front of a marble mansion with neon pools",
            "relaxing on a floating villa in Dubai",
            "walking through a golden hallway in a luxury hotel",
            "in a glass elevator overlooking a cyber city"
        ],
        "nature": [
            "under the Northern Lights in Finland",
            "amidst giant redwoods in California",
            "walking across a glowing bridge in Iceland",
            "on a cliffside villa in Santorini",
            "next to bioluminescent waves at midnight"
        ]
    }
    themes = [
        "resilience and power", "confidence and self-worth", "peace and clarity",
        "legacy and greatness", "bold vision and courage", "rebirth and growth"
    ]

    category = random.choice(list(categories.keys()))
    location = random.choice(categories[category])
    style = random.choice(visual_styles)
    theme = random.choice(themes)

    prompt = f"{style}, {location}, soft neon lights, cinematic lighting, photorealistic"
    log(f"🧠 Generiram sliko z DALL·E: {prompt}")

    response = openai.images.generate(
        model="dall-e-3",
        prompt=prompt,
        n=1,
        size="1024x1024"
    )
    image_url = response.data[0].url
    img_data = requests.get(image_url).content
    with open("generated_image.jpg", "wb") as f:
        f.write(img_data)

    uploaded = cloudinary.uploader.upload("generated_image.jpg")
    final_url = uploaded['secure_url']
    log(f"☁️ Cloudinary: {final_url}")

    caption_prompt = (
        f"Write a powerful, real, short inspirational quote. Theme: {theme}. Include 5 trending motivational hashtags."
    )
    chat = openai.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": caption_prompt}]
    )
    caption = chat.choices[0].message.content.strip()
    log(f"✍️ Caption: {caption}")

    ig_url = f"https://graph.facebook.com/v19.0/{IG_USER_ID}/media"
    ig_payload = {"image_url": final_url, "caption": caption, "access_token": ACCESS_TOKEN}
    ig_res = requests.post(ig_url, data=ig_payload).json()
    log(f"📦 IG Container: {ig_res}")

    if 'id' in ig_res:
        time.sleep(5)
        pub_url = f"https://graph.facebook.com/v19.0/{IG_USER_ID}/media_publish"
        pub_payload = {"creation_id": ig_res['id'], "access_token": ACCESS_TOKEN}
        pub_res = requests.post(pub_url, data=pub_payload).json()
        log(f"✅ IG objavljeno: {pub_res}")
    else:
        log("❌ IG ni uspel.")

    fb_url = f"https://graph.facebook.com/v19.0/{FB_PAGE_ID}/photos"
    fb_payload = {"url": final_url, "caption": caption, "access_token": ACCESS_TOKEN}
    fb_res = requests.post(fb_url, data=fb_payload).json()
    log(f"✅ FB objavljeno: {fb_res}")

    return "\n".join(logs)

if __name__ == '__main__':
    now = datetime.utcnow()
    hour = now.hour
    # Objava ob 8:00 UTC (EU zjutraj), 20:00 UTC (EU zvečer), 01:00 UTC (ZDA popoldne/večer)
    if hour in [8, 20, 1]:
        output = post_once()
        print("\n--- REZULTAT ---\n")
        print(output)
    else:
        print("⏳ Čas ni pravi za objavo, čakamo na naslednji slot.")
