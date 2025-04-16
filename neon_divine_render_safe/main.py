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

# 🔁 Objavi 1x - za Render cron job (4x/dan)
def post_once():
    locations = [
        "walking through the cherry blossoms in Kyoto",
        "standing under the Eiffel Tower in Paris",
        "on the cliffs of Santorini at sunset",
        "in front of the futuristic skyline of Dubai Marina",
        "walking on a neon-lit street in Tokyo",
        "sitting by the canals of Venice"
    ]
    themes = [
        "confidence and self-worth",
        "resilience and power",
        "ambition and discipline",
        "vision and legacy",
        "inner peace and presence",
        "strength and fearlessness"
    ]

    chosen_location = random.choice(locations)
    chosen_theme = random.choice(themes)
    prompt = f"Futuristic high-class woman with neon aura, sharp eyes, silver hair, cyberpunk fashion, ultra-detailed, {chosen_location}"
    print(f"🧠 Generiram sliko z DALL·E: {prompt}")

    response = openai.images.generate(
        model="dall-e-3",
        prompt=prompt,
        n=1,
        size="1024x1024"
    )
    image_url = response.data[0].url
    print("🖼️ DALL·E URL:", image_url)

    img_data = requests.get(image_url).content
    local_filename = "generated_image.jpg"
    with open(local_filename, 'wb') as handler:
        handler.write(img_data)

    upload_result = cloudinary.uploader.upload(local_filename)
    final_image_url = upload_result['secure_url']
    print("🌐 Cloudinary URL:", final_image_url)

    caption_prompt = (
        f"Write a short, powerful, inspirational quote in the style of a world leader or philosopher. Theme: {chosen_theme}. Make it suitable for a social media post."
    )
    print("✍️ Generiram caption...")
    chat_response = openai.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": caption_prompt}]
    )
    caption = chat_response.choices[0].message.content.strip()
    print("📝 Caption:", caption)

    print("📤 Objavljam na Instagram...")
    create_url = f"https://graph.facebook.com/v19.0/{IG_USER_ID}/media"
    create_payload = {
        'image_url': final_image_url,
        'caption': caption,
        'access_token': ACCESS_TOKEN
    }
    create_res = requests.post(create_url, data=create_payload)
    create_data = create_res.json()
    print("📦 IG Container:", create_data)

    if 'id' in create_data:
        creation_id = create_data['id']
        time.sleep(5)
        publish_url = f"https://graph.facebook.com/v19.0/{IG_USER_ID}/media_publish"
        publish_payload = {
            'creation_id': creation_id,
            'access_token': ACCESS_TOKEN
        }
        publish_res = requests.post(publish_url, data=publish_payload)
        print("✅ Objavljeno na Instagram:", publish_res.json())
    else:
        print("❌ Napaka pri IG objavi:", create_data)

    print("📘 Objavljam na Facebook...")
    fb_post_url = f"https://graph.facebook.com/v19.0/{FB_PAGE_ID}/photos"
    fb_payload = {
        'url': final_image_url,
        'caption': caption,
        'access_token': ACCESS_TOKEN
    }
    fb_res = requests.post(fb_post_url, data=fb_payload)
    print("✅ Objavljeno na Facebook:", fb_res.json())

# 🚀 Zagon za Render cron
if __name__ == '__main__':
    post_once()
