from flask import Flask
from neon_divine_render_safe.main import post_once

app = Flask(__name__)

@app.route('/')
def home():
    return "✅ Neon Divine web service is up and running!"

@app.route('/test')
def run_post():
    try:
        post_once()
        return "✅ Post was attempted! Check Render logs for result."
    except Exception as e:
        return f"❌ Error: {str(e)}"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
