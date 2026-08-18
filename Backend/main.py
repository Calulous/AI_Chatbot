# Flask endpoint
# send post request to server

import os
from pathlib import Path

# Flask creates the HTTP server.
# request reads data sent by the frontend.
# jsonify sends JSON responses back to the frontend.
# render_template displays our HTML page.
from flask import Flask, jsonify, render_template, request

# dotenv loads environment variables from .env
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
    static_folder=str(FRONTEND_DIR)
)


# ============================
# Environment variables
# ============================

# Load the .env file from Backend/.env
# We are NOT using the API key in this temporary test.
load_dotenv(BACKEND_DIR / ".env")


# ============================
# Temporary conversation memory
# ============================

# Example:
#
# {
#     "session-123": [
#         {"role": "user", "content": "Hello"},
#         {"role": "assistant", "content": "Test successful! You said: Hello"}
#     ]
# }
#
# This resets whenever Flask restarts.
conversations = {}


# ============================
# Home page
# ============================

# When the user opens the URL, display homepage.html.
@app.get("/")
def home():
    return render_template("homepage.html")


# ============================
# Chat endpoint
# ============================

@app.post("/api/chat")
def chat():

    # Frontend sends a JSON package.
    # silent=True prevents invalid JSON from crashing Flask.
    # If there is no JSON, use an empty dictionary instead.
    data = request.get_json(silent=True) or {}

    # Read message and session ID.
    # strip() removes unnecessary spaces.
    message = str(data.get("message", "")).strip()
    session_id = str(data.get("session_id", "")).strip()

    # Validation: reject an empty message.
    if not message:
        return jsonify({
            "error": "Please enter a message."
        }), 400

    # Validation: every conversation needs a session ID.
    if not session_id:
        return jsonify({
            "error": "Session ID is required."
        }), 400

    # Get this session's conversation.
    # If it does not exist, create an empty message list.
    history = conversations.setdefault(session_id, [])

    # Save the user's new message.
    history.append({
        "role": "user",
        "content": message
    })

    try:
        # ==========================================
        # TEMPORARY TEST RESPONSE
        # ==========================================
        #
        # We are NOT calling OpenAI here.
        # This lets us test:
        #
        # frontend
        # ↓
        # JavaScript
        # ↓
        # POST /api/chat
        # ↓
        # Flask
        # ↓
        # JSON response
        #
        # without needing a working API key.

        assistant_reply = f"Test successful! You said: {message}"

        # Save the test assistant reply in conversation history.
        history.append({
            "role": "assistant",
            "content": assistant_reply
        })

        # Return the reply to the frontend as JSON.
        return jsonify({
            "reply": assistant_reply,
            "session_id": session_id
        })

    except Exception as error:

        # Print technical error in the backend terminal.
        print("Backend error:", error)

        # Remove the failed user message from history.
        if history and history[-1]["role"] == "user":
            history.pop()

        # Send a friendly error to the frontend.
        return jsonify({
            "error": "Something went wrong. Please try again."
        }), 500


# ============================
# Clear current conversation
# ============================

@app.delete("/api/chat/<session_id>")
def clear_chat(session_id):

    # Remove the conversation if it exists.
    # None prevents an error if it does not exist.
    conversations.pop(session_id, None)

    return jsonify({
        "message": "Conversation cleared."
    })


# ============================
# Start Flask server
# ============================

if __name__ == "__main__":
    app.run(
        debug=True,
        port=5000
    )