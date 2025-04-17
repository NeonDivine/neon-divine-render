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

def ai_reply_to_comments(post_id, log):
    log(f"💬 Iščem komentarje za AI odgovor na objavi {post_id}...")

    url = f"https://graph.facebook.com/v19.0/{post_id}/comments?access_token={ACCESS_TOKEN}"
    res = requests.get(url)
    data = res.json()

    if "data" not in data:
        log("⚠️ Ni komentarjev za odgovor.")
        return

    for comment in random.sample(data["data"], min(2, len(data["data"]))):
        comment_id = comment["id"]
        message = comment["message"]

        prompt = (
            f"You are Neon Divine, a high-class inspirational female influencer. "
            f"Respond in 1-2 short, kind and thoughtful sentences to this comment: \"{message}\". "
            "Be soft, warm, real, and down-to-earth. Use simple, elegant language. If the comment is unclear, reply with 'Thank you so much for being here ✨'"
        )

        try:
            chat_response = openai.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}]
            )
            reply_text = chat_response.choices[0].message.content.strip()
        except Exception as e:
            reply_text = "Thank you for your kind comment. You are appreciated ✨"

        reply_url = f"https://graph.facebook.com/v19.0/{comment_id}/replies"
        payload = {
            "message": reply_text,
            "access_token": ACCESS_TOKEN
        }
        reply_res = requests.post(reply_url, data=payload)
        log(f"↪️ AI odgovorjeno: {reply_text}")

def reply_to_all_recent_posts():
    def log(msg):
        print(msg)

    for platform, endpoint in {
        "Instagram": f"https://graph.facebook.com/v19.0/{IG_USER_ID}/media",
        "Facebook": f"https://graph.facebook.com/v19.0/{FB_PAGE_ID}/feed"
    }.items():
        res = requests.get(endpoint, params={"access_token": ACCESS_TOKEN})
        data = res.json()
        if "data" not in data:
            log(f"⚠️ Ni objav za {platform}.")
            continue

        for post in data["data"][:5]:  # pregleda zadnjih 5 objav
            post_id = post.get("id") or post.get("post_id")
            if post_id:
                ai_reply_to_comments(post_id, log)

# 🔁 Objavi 1x - za Render cron job (4x/dan + ponoči za dodatne časovne cone)
def post_once():
    logs = []
    def log(msg):
        print(msg)
        logs.append(msg)

    categories = {
        "urban": [
            "walking through the neon-lit streets of Seoul",
            "posing in Times Square at night",
            "in front of a glowing tram in Lisbon",
            "waiting at a crosswalk in downtown Los Angeles",
            "walking along the canals of Amsterdam"
        ],
        "nature": [
            "standing on the cliffs of Santorini at sunset",
            "next to the crashing waves in Iceland",
            "amidst giant redwoods in California",
            "walking through a foggy forest in Canada",
            "relaxing by the lake in Switzerland"
        ],
        "epic": [
            "on top of a sand dune in the Sahara at golden hour",
            "standing on a cliff edge in Norway",
            "under the Northern Lights in Finland",
            "posing on a glass bridge above a canyon",
            "meditating in the snowy peaks of the Himalayas"
        ],
        "romantic": [
            "sitting at a cozy café in Paris",
            "walking through the cherry blossoms in Kyoto",
            "smiling under cherry blossoms in Japan",
            "standing under the Eiffel Tower at dusk",
            "walking on the beach in Bali during sunset"
        ],
        "nighttime": [
            "under the moonlight on a rooftop in NYC",
            "next to glowing lanterns in Taiwan",
            "on a quiet street in Berlin at 2 AM",
            "walking solo through neon-lit Hong Kong alleys",
            "in a misty Tokyo side street after midnight"
        ]
    }

    themes = [
        "confidence and self-worth",
        "resilience and power",
        "ambition and discipline",
        "vision and legacy",
        "inner peace and presence",
        "strength and fearlessness",
        "self-love and strength",
        "freedom and confidence",
        "growth and ambition",
        "peace and clarity",
        "balance and focus",
        "joy and simplicity"
    ]

    category = random.choice(list(categories.keys()))
    chosen_location = random.choice(categories[category])
    chosen_theme = random.choice(themes)

    prompt = (
        f"Futuristic high-class woman with minimalistic glowing futuristic outfit, soft neon aura, silver-blonde hair, " +
        f"sharp confident eyes, ultra-detailed photorealistic style, {chosen_location}"
    )
    log(f"🧐 Generiram sliko z DALL·E: {prompt}")

    response = openai.images.generate(
        model="dall-e-3",
        prompt=prompt,
        n=1,
        size="1024x1024"
    )
    image_url = response.data[0].url
    log("🖼️ DALL·E URL: " + image_url)

    img_data = requests.get(image_url).content
    local_filename = "generated_image.jpg"
    with open(local_filename, 'wb') as handler:
        handler.write(img_data)

    upload_result = cloudinary.uploader.upload(local_filename)
    final_image_url = upload_result['secure_url']
    log("🌐 Cloudinary URL: " + final_image_url)

    caption_prompt = (
        f"Write a short, powerful, inspirational quote in the style of a world leader or philosopher. "
        f"Theme: {chosen_theme}. Make it suitable for a social media post. "
        "Add 5 trending motivational hashtags at the end (e.g. #mindset #success #focus)."
    )
    log("✍️ Generiram caption...")
    chat_response = openai.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": caption_prompt}]
    )
    caption = chat_response.choices[0].message.content.strip()
    log("📝 Caption: " + caption)

    log("📤 Objavljam na Instagram...")
    create_url = f"https://graph.facebook.com/v19.0/{IG_USER_ID}/media"
    create_payload = {
        'image_url': final_image_url,
        'caption': caption,
        'access_token': ACCESS_TOKEN
    }
    create_res = requests.post(create_url, data=create_payload)
    create_data = create_res.json()
    log("📦 IG Container: " + str(create_data))

    if 'id' in create_data:
        creation_id = create_data['id']
        time.sleep(5)
        publish_url = f"https://graph.facebook.com/v19.0/{IG_USER_ID}/media_publish"
        publish_payload = {
            'creation_id': creation_id,
            'access_token': ACCESS_TOKEN
        }
        publish_res = requests.post(publish_url, data=publish_payload)
        log("✅ Objavljeno na Instagram: " + str(publish_res.json()))

        if 'id' in publish_res.json():
            insta_post_id = publish_res.json()['id']
            ai_reply_to_comments(insta_post_id, log)
    else:
        log("❌ Napaka pri IG objavi: " + str(create_data))

    log("📜 Objavljam na Facebook...")
    fb_post_url = f"https://graph.facebook.com/v19.0/{FB_PAGE_ID}/photos"
    fb_payload = {
        'url': final_image_url,
        'caption': caption,
        'access_token': ACCESS_TOKEN
    }
    fb_res = requests.post(fb_post_url, data=fb_payload)
    log("✅ Objavljeno na Facebook: " + str(fb_res.json()))

    if 'post_id' in fb_res.json():
        fb_post_id = fb_res.json()['post_id']
        ai_reply_to_comments(fb_post_id, log)

    return "\n".join(logs)

# 🚀 Za test z ukazom: python main.py
if __name__ == '__main__':
    output = post_once()
    print("🚪 Rezultat:")
    print(output)
    reply_to_all_recent_posts()
