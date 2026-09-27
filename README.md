# Chatly — AI-Powered Customer Support Chatbot

Chatly is a lightweight Flask customer-support chatbot with a responsive web interface, local Transformer-powered responses, conversation context, and SQLite interaction history. It is designed to run directly on Replit without an external AI API or database service.

## Features

- Responsive desktop and mobile chat interface
- Welcome message when the chat opens
- Separate user and assistant message bubbles with avatars
- Context-aware responses from `HuggingFaceTB/SmolLM2-135M-Instruct`
- Conversation history sent with recent chat requests
- Typing/loading indicator while the model responds
- Auto-scrolling conversation area
- Enter to send and Shift+Enter for a new line
- Send button disabled during response generation
- 2,000-character message limit with friendly validation errors
- Clear Chat control for the current browser conversation
- SQLite logging for successful user messages and bot responses
- History page with recent interactions
- Clear History action for stored interaction logs
- No database file, secrets, uploads, or environment files committed to Git

## Technologies

- Python 3.13+
- Flask
- SQLite3
- PyTorch
- Hugging Face Transformers
- `HuggingFaceTB/SmolLM2-135M-Instruct`
- HTML, CSS, and vanilla JavaScript

## Setup

### Local setup with uv

This project includes `pyproject.toml` and `uv.lock`:

```bash
uv sync
uv run python app.py
```

### Local setup with pip

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

On Windows, activate the environment with:

```powershell
.venv\Scripts\activate
```

### Replit

The project is configured to run with:

```bash
python app.py
```

The Flask server binds to `0.0.0.0` on port `5000`, which makes it available through the Replit preview.

## Usage

1. Start the Flask server.
2. Open the web preview.
3. Enter a message in the composer and press Enter or click Send.
4. Use Shift+Enter to add a line break.
5. Use **Clear Chat** to reset the current browser conversation.
6. Open **History** to view saved interactions.
7. Use **Clear History** to delete all saved SQLite interaction logs.

The first message may take longer because the Transformer model is downloaded and cached locally. Later messages reuse the loaded model.

## API

### `POST /chat`

Accepts a message and optional recent conversation history:

```json
{
  "message": "How can I reset my password?",
  "history": [
    {
      "role": "user",
      "content": "I need help with my account."
    },
    {
      "role": "assistant",
      "content": "I can help with that."
    }
  ]
}
```

Returns:

```json
{
  "response": "..."
}
```

The older `/api/chat` route is retained as a compatibility alias.

## Project structure

```text
.
├── app.py                 # Flask routes, model generation, and SQLite logging
├── templates/
│   ├── index.html         # Chat interface
│   └── history.html       # Saved interaction history
├── chatbot.db             # Runtime-created SQLite database (ignored by Git)
├── requirements.txt       # pip dependencies
├── pyproject.toml         # Project metadata and dependencies
├── uv.lock                # Reproducible uv dependency lockfile
└── .replit                # Replit run and port configuration
```

## Limitations

- The local 135M-parameter model is optimized for a small Replit deployment, so responses may be less capable than hosted large language models.
- CPU generation can take several seconds, especially during the first request.
- The model is loaded into the application process and is not streamed token by token.
- SQLite is local to the Replit workspace and is not intended for multi-instance production deployments.
- There is no authentication, user account system, rate limiting, or moderation layer yet.
- Chat history is shared within the local database; per-user history is not implemented.
- The application uses Flask's development server. A production deployment should use a production WSGI server.

## Data and secrets

The following are intentionally excluded from version control:

- `chatbot.db` and other SQLite/database files
- `.env` files and environment variables
- API keys, private keys, and certificates
- Uploaded files and local model caches
- Replit memory, cache, and screenshot artifacts
