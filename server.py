from flask import Flask, request, jsonify
from flask_cors import CORS
from gtts import gTTS
import speech_recognition as sr
import subprocess
import platform
import wikipedia
import datetime
import pytz
import os
from dotenv import load_dotenv
import os

load_dotenv()
from openai import OpenAI

# Initialize Flask app
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))  # Make sure key is set in environment

# ------------------ Utility Functions ------------------

def speak(text):
    """Convert text to speech and save as MP3."""
    tts = gTTS(text=text, lang='en')
    file_path = "response.mp3"
    tts.save(file_path)
    return file_path


def open_application(command, env):
    """Open desktop applications or return live info."""
    system = platform.system()

    if "chrome" in command:
        if env == "live":
            return "Click here to open Google: https://www.google.com"
        if system == "Windows":
            subprocess.run("start chrome", shell=True)
        elif system == "Darwin":
            subprocess.run("open -a 'Google Chrome'", shell=True)
        elif system == "Linux":
            subprocess.run("google-chrome &", shell=True)
        return "Opening Chrome"

    elif "notepad" in command:
        if env == "live":
            return "You can open Notepad by pressing Win + R and typing 'notepad'."
        if system == "Windows":
            subprocess.run("notepad", shell=True)
            return "Opening Notepad"
        return "Notepad is only available on Windows."

    elif "vscode" in command or "visual studio code" in command:
        if env == "live":
            return "You can open VS Code from your start menu or by running 'code' in a terminal."
        if system == "Windows":
            subprocess.run("code", shell=True)
        elif system == "Darwin":
            subprocess.run("open -a 'Visual Studio Code'", shell=True)
        elif system == "Linux":
            subprocess.run("code &", shell=True)
        return "Opening Visual Studio Code"

    elif "calculator" in command:
        if env == "live":
            return "Open the calculator manually on your device."
        if system == "Windows":
            subprocess.run("calc", shell=True)
        elif system == "Darwin":
            subprocess.run("open -a Calculator", shell=True)
        elif system == "Linux":
            subprocess.run("gnome-calculator &", shell=True)
        return "Opening Calculator"

    return None


def get_gpt_response(prompt):
    """Send user command to GPT for intelligent response."""
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # or "gpt-4-turbo" if available
            messages=[
                {"role": "system", "content": "You are a helpful AI assistant named Jarvis."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print("GPT error:", e)
        return "I'm having trouble connecting to my AI brain right now."


# ------------------ Flask Routes ------------------

@app.route("/")
def home():
    return "Hello, your Flask app is running with GPT integration!"


@app.route("/process_command", methods=["POST"])
def process_command():
    data = request.json
    command = data.get("command", "").lower()
    user_timezone = data.get("timezone", "UTC")

    client_host = request.host
    environment = "local" if ("127.0.0.1" in client_host or "localhost" in client_host) else "live"

    if not command:
        return jsonify({"response": "No Command Received."})

    response = None

    # ---- Priority 1: Open apps ----
    appresponse = open_application(command, environment)
    if appresponse:
        response = appresponse

    # ---- Priority 2: Time / Date ----
    elif "time" in command:
        local_tz = pytz.timezone(user_timezone)
        now = datetime.datetime.now(local_tz).strftime("%I:%M:%S %p")
        response = f"The current time is {now}."

    elif "date" in command:
        today = datetime.date.today().strftime("%B %d, %Y")
        response = f"Today's date is {today}."

    # ---- Priority 3: Wikipedia ----
    elif "wikipedia" in command:
        topic = command.replace("wikipedia", "").strip()
        try:
            summary = wikipedia.summary(topic, sentences=2)
            response = f"According to Wikipedia: {summary}"
        except wikipedia.exceptions.DisambiguationError:
            response = f"Multiple results found for {topic}, please be more specific."
        except wikipedia.exceptions.PageError:
            response = f"Sorry, no results found for {topic} on Wikipedia."

    # ---- Priority 4: Search ----
    elif "search" in command:
        search_query = command.replace("search", "").strip()
        url = f"https://www.google.com/search?q={search_query.replace(' ', '+')}"
        response = {
            "success": True,
            "url": url,
            "message": f"Searching for {search_query} on Google.",
            "searchText": search_query
        }

    # ---- Priority 5: Exit ----
    elif "exit" in command or "stop" in command:
        response = "Goodbye! Have a nice day."

    # ---- Priority 6: GPT fallback ----
    else:
        response = get_gpt_response(command)

    return jsonify({"response": response})


# ------------------ Main Entry ------------------

if __name__ == "__main__":
    from waitress import serve
    print("Starting server on port 8000 with GPT integration...")
    serve(app, host="0.0.0.0", port=8000)
