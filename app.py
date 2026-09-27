import os
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path

import torch
from flask import Flask, jsonify, redirect, render_template, request, url_for
from transformers import AutoModelForCausalLM, AutoTokenizer

app = Flask(__name__)

MODEL_NAME = os.getenv("CHAT_MODEL_NAME", "HuggingFaceTB/SmolLM2-135M-Instruct")
DATABASE_PATH = Path(__file__).with_name("chatbot.db")
MAX_CONTEXT_MESSAGES = 6
MAX_MESSAGE_LENGTH = 2000

_model = None
_tokenizer = None
_model_lock = threading.Lock()


def get_db_connection():
    connection = sqlite3.connect(DATABASE_PATH, timeout=10)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database():
    try:
        connection = get_db_connection()
        try:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS chat_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_message TEXT NOT NULL,
                    bot_response TEXT NOT NULL,
                    timestamp TEXT NOT NULL
                )
                """
            )
            connection.commit()
        finally:
            connection.close()
    except sqlite3.Error:
        app.logger.exception("Unable to initialize the SQLite database")


def save_chat_log(user_message, bot_response):
    connection = get_db_connection()
    try:
        connection.execute(
            """
            INSERT INTO chat_logs (user_message, bot_response, timestamp)
            VALUES (?, ?, ?)
            """,
            (
                user_message,
                bot_response,
                datetime.now(timezone.utc).isoformat(timespec="seconds"),
            ),
        )
        connection.commit()
    finally:
        connection.close()


def get_recent_chat_logs(limit=100):
    connection = get_db_connection()
    try:
        return connection.execute(
            """
            SELECT id, user_message, bot_response, timestamp
            FROM chat_logs
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    finally:
        connection.close()


def delete_chat_logs():
    connection = get_db_connection()
    try:
        connection.execute("DELETE FROM chat_logs")
        connection.commit()
    finally:
        connection.close()


def get_model():
    """Load the conversational model once, only when the first chat starts."""
    global _model, _tokenizer

    if _model is None or _tokenizer is None:
        with _model_lock:
            if _model is None or _tokenizer is None:
                _tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
                _model = AutoModelForCausalLM.from_pretrained(MODEL_NAME)
                _model.eval()

                if _tokenizer.pad_token is None:
                    _tokenizer.pad_token = _tokenizer.eos_token

    return _tokenizer, _model


def generate_response(message, history):
    tokenizer, model = get_model()

    conversation = [
        {
            "role": "system",
            "content": (
                "You are a helpful, concise assistant. Answer the user's "
                "latest message directly and naturally. Do not reply with "
                "only a greeting unless the user is greeting you."
            ),
        }
    ]
    for item in history[-MAX_CONTEXT_MESSAGES:]:
        if not isinstance(item, dict):
            continue

        content = str(item.get("content", "")).strip()
        if content:
            role = "user" if item.get("role") == "user" else "assistant"
            conversation.append({
                "role": role,
                "content": content[:MAX_MESSAGE_LENGTH],
            })

    conversation.append({"role": "user", "content": message})
    prompt = tokenizer.apply_chat_template(
        conversation,
        tokenize=False,
        add_generation_prompt=True,
    )
    inputs = tokenizer(
        prompt,
        return_tensors="pt",
        truncation=True,
        max_length=768,
    )

    with torch.inference_mode():
        output_ids = model.generate(
            **inputs,
            max_new_tokens=120,
            do_sample=False,
            repetition_penalty=1.05,
            no_repeat_ngram_size=3,
            pad_token_id=tokenizer.eos_token_id,
        )

    generated_ids = output_ids[0, inputs["input_ids"].shape[-1] :]
    response = tokenizer.decode(generated_ids, skip_special_tokens=True).strip()
    return response or "I’m not sure how to respond to that yet. Could you try rephrasing?"


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/history")
def history():
    try:
        logs = get_recent_chat_logs()
        database_error = None
    except sqlite3.Error:
        app.logger.exception("Unable to read chat history")
        logs = []
        database_error = "Chat history is temporarily unavailable. Please try again."

    return render_template(
        "history.html",
        logs=logs,
        database_error=database_error,
    )


@app.post("/chat")
@app.post("/api/chat")
def chat():
    data = request.get_json(silent=True) or {}
    raw_message = data.get("message", "")
    message = raw_message.strip() if isinstance(raw_message, str) else ""
    history = data.get("history", [])

    if not message:
        return jsonify({"error": "Please enter a message."}), 400

    if len(message) > MAX_MESSAGE_LENGTH:
        return jsonify({"error": "Your message is too long. Please keep it under 2,000 characters."}), 400

    if not isinstance(history, list):
        history = []

    try:
        response = generate_response(message, history)
    except Exception:
        app.logger.exception("Unable to generate chatbot response")
        return jsonify({
            "error": "The AI model could not generate a response right now. Please try again.",
        }), 503

    try:
        save_chat_log(message, response)
        return jsonify({"response": response})
    except sqlite3.Error:
        app.logger.exception("Unable to save chat interaction")
        return jsonify({
            "response": response,
            "warning": "The response was generated, but this interaction could not be saved.",
        })


@app.post("/clear-history")
def clear_history():
    try:
        delete_chat_logs()
    except sqlite3.Error:
        app.logger.exception("Unable to clear chat history")

    return redirect(url_for("history"))


initialize_database()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)