# Flask endpoint
# send post request to server

import os
from pathlib import Path

# Flask creates the HTTP server.
# request reads data sent by the frontend.
# jsonify sends JSON responses back to the frontend.
# render_template displays our HTML page.
from flask import Flask, jsonify, render_template, request

# Official OpenAI Python client.
from openai import OpenAI
from dotenv import load_dotenv


# ============================
# Project paths
# ============================

# Folder containing this file:
# AI_Chatbot/Backend
BACKEND_DIR = Path(__file__).resolve().parent

# Main project folder:
# AI_Chatbot
PROJECT_DIR = BACKEND_DIR.parent

# Frontend folder:
# AI_Chatbot/Frontend
FRONTEND_DIR = PROJECT_DIR / "Frontend"


# ============================
# Flask setup
# ============================

# Tell Flask where the HTML templates and frontend files are located.
app = Flask(
    __name__,
    template_folder=str(FRONTEND_DIR / "templates"),
    static_folder=str(FRONTEND_DIR),
    static_url_path="/static"
)


# ============================
# Environment variables
# ============================

# Explicitly load:
# AI_Chatbot/Backend/.env
load_dotenv(BACKEND_DIR / ".env")

# Read the API key from .env instead of hardcoding it.
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)


# Temporary in-memory conversation storage.
conversations = {}


# HOME PAGE:
# When the user opens the URL, this is the first page they see.
@app.get("/")
def home():
    return render_template("homepage.html")


# React/HTML sends chat messages to this endpoint.
@app.post("/api/chat")
def chat():
    # frontend sends JSON package 
    # {} just gonna prevent the file from crashing if there is no JSON input
    data = request.get_json(silent=True) or {} # valid json then use if not then {}; silent=true if json is missing it returns NONE

    # Read Message and Session ID.
    # strip() to get rid of unncessary spaces.
    message = str(data.get("message", "")).strip()
    session_id = str(data.get("session_id", "")).strip()

    # Validation: reject an empty message.
    if not message:
        return jsonify({
            "error": "Please enter a message."
        }), 400 # sends http status code to bad request

    # Validation: conversation needs a session id
    if not session_id:
        return jsonify({
            "error": "Session ID is required."
        }), 400

    # Every chat has a session. Get this session's (chats) conversation. 
    # If the session does not exist, create an empty message list.
    history = conversations.setdefault(session_id, [])

    # Save the user's new message. 
    history.append({
        "role": "user",
        "content": message
    })

    try:
        # Send the complete conversation history to the AI.
        # This gives the AI context and basic memory.
        # when u open the chat, it displays the conversation & remembers the context!
        
        # CHAT MODEL! - will use the mini model at this stage to ensure no runtime delays.
        response = client.responses.create(
            model="gpt-4.1-mini",
            input=history
        )

        # Extract the assistant's text from the API response.
        assistant_reply = response.output_text

        # Validate that the AI actually returned text.
        if not assistant_reply:
            raise ValueError("The AI returned an empty response.")

        # Save the assistant reply in conversation history.
        history.append({
            "role": "assistant",
            "content": assistant_reply
        })

        # Return the answer to the frontend as JSON.
        return jsonify({
            "reply": assistant_reply,
            "session_id": session_id
        })

    except Exception as error:
        # Print the technical error in the backend terminal
        # so the developer can debug it.
        print("AI API error:", error)

        # Remove the last user message because the request failed.
        # This prevents failed messages from remaining in context.
        if history and history[-1]["role"] == "user":
            history.pop()

        # Send a friendly error to the frontend.
        # Never expose the API key or full technical error to the user.
        return jsonify({
            "error": "The AI service is temporarily unavailable. Please try again."
        }), 500


# Clear the current conversation.
@app.delete("/api/chat/<session_id>")
def clear_chat(session_id):
    # Remove the conversation if it exists.
    # None prevents an error if it does not exist.
    conversations.pop(session_id, None)

    return jsonify({
        "message": "Conversation cleared."
    })


# Start the Flask server when app.py is run directly.
if __name__ == "__main__":
    app.run(debug=True, port=5000)