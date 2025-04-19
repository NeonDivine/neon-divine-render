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

# ⏱️ Zamik med komentarji
DELAY_BETWEEN_COMMENTS = (30, 90)  # sekund
MAX_REPLIES_PER_POST = 2


def ai_reply_to_comments(post_id, log):
    log(f"💬 Iščem komentarje za AI odgovor na objavi {post_id}...")
    url = f"https://graph.facebook.com/v19.0/{post_id}/comments?access_token={ACCESS_TOKEN}"
    res = requests.get(url)
    data = res.json()
    if "data" not in data:
        log("⚠️ Ni komentarjev za odgovor.")
        return

    for comment in random.sample(data["data"], min(MAX_REPLIES_PER_POST, len(data["data"]))):
        comment_id = comment["id"]
        message = comment["message"]
        prompt = (
            f"You are Neon Divine, a high-class inspirational AI woman. Respond kindly to this comment: '{message}'. "
            f"Use short, elegant, non-repetitive language, keep tone human and heartfelt."
        )
        try:
            chat_response = openai.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}]
            )
            reply_text = chat_response.choices[0].message.content.strip()
        except:
            reply_text = "Thank you for sharing your thoughts. It means a lot."

        reply_url = f"https://graph.facebook.com/v19.0/{comment_id}/replies"
        payload = {"message": reply_text, "access_token": ACCESS_TOKEN}
        requests.post(reply_url, data=payload)
        log(f"↪️ AI odgovorjeno: {reply_text}")
        time.sleep(random.randint(*DELAY_BETWEEN_COMMENTS))


def reply_to_recent_fb_posts(log):
    url = f"https://graph.facebook.com/v19.0/{FB_PAGE_ID}/feed?access_token={ACCESS_TOKEN}"
    res = requests.get(url)
    data = res.json()
    if "data" not in data:
        log("⚠️ Ni objav za Facebook.")
        return
    for post in data["data"][:5]:
        post_id = post.get("id") or post.get("post_id")
        if post_id:
            ai_reply_to_comments(post_id, log)


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
        if 'id' in pub_res:
            ai_reply_to_comments(pub_res['id'], log)
    else:
        log("❌ IG ni uspel.")

    fb_url = f"https://graph.facebook.com/v19.0/{FB_PAGE_ID}/photos"
    fb_payload = {"url": final_url, "caption": caption, "access_token": ACCESS_TOKEN}
    fb_res = requests.post(fb_url, data=fb_payload).json()
    log(f"✅ FB objavljeno: {fb_res}")
    if 'post_id' in fb_res:
        ai_reply_to_comments(fb_res['post_id'], log)

    return "\n".join(logs)


if __name__ == '__main__':
    output = post_once()
    print("\n--- REZULTAT ---\n")
    print(output)
    print("\n--- Odgovori na komentarje ---\n")
    reply_to_recent_fb_posts(lambda x: print(x))
