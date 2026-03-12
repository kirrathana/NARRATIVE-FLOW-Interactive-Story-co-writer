# Story Waver

A local AI-powered story narration chatbot built with **Streamlit** and **Ollama**. No cloud, no API keys — everything runs on your machine.

---

## Features

- **6+ Genres** — Romantic, Horror, Fantasy, Mystery, Humor, Suspense, Sci-Fi, Adventure
- **Writing Modes** — Beginning, Continue, Climax, Ending
- **Tone Control** — Dramatic, Lighthearted, Dark, Whimsical, Suspenseful, and more
- **Creativity Slider** — Fine-tune the model's temperature (0–100)
- **Response Length** — Short, Medium, or Long outputs
- **Quick Prompts** — One-click story starters
- **Story History** — Last 5 stories shown in sidebar
- **Real-time Streaming** — Words appear as they are generated
- **Save Story** — Download any story as a `.txt` file
- **Ollama Status Indicator** — Live online/offline badge in sidebar

---

## Requirements

| Tool | Version |
|------|---------|
| Python | 3.9+ |
| Ollama | Latest |
| phi model | `ollama pull phi` |

---

## Setup

### 1. Install Ollama

Download and install Ollama from [https://ollama.com](https://ollama.com).

### 2. Pull the Phi model

```bash
ollama pull phi
```

> To use a different model (e.g. phi3, mistral), pull it and update `OLLAMA_MODEL` in `.env`.

### 3. Clone / download this project

```bash
git clone <your-repo-url>
cd story-waver
```

### 4. Create a virtual environment (recommended)

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 5. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 6. Configure environment

```bash
cp .env.example .env
```

Edit `.env` if needed:

```env
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=phi
```

### 7. Start Ollama (in a separate terminal)

```bash
ollama serve
```

> On most systems Ollama starts automatically after installation.

### 8. Run the app

```bash
streamlit run app.py
```

Open your browser at `http://localhost:8501`.

---

## Project Structure

```
story-waver/
├── app.py              # Streamlit UI (login, main writer, history pages)
├── ollama_helper.py    # Ollama API integration & prompt builder
├── db.py               # JSON database — users, passwords, story history
├── data/
│   └── stories.json    # Persistent story & user storage (auto-created)
├── .env                # Your local config (not committed)
├── .env.example        # Config template
├── requirements.txt    # Python dependencies
└── README.md
```

## User Accounts & Story History

- **Register** a username + password (stored with SHA-256 hash + salt — never plain text)
- **Login** to access your personal story library
- Every generated story is **auto-saved** to `data/stories.json` under your account
- **My Stories page** — browse all saved stories, filter by genre, view full story, load back into writer, delete, or download as `.txt`
- Sidebar shows the **5 most recent stories** with genre tag and date
- **Logout** clears the session; stories remain saved for next login

---

## Switching Models

1. Pull your preferred model:
   ```bash
   ollama pull phi3:mini
   # or
   ollama pull mistral
   ```

2. Update `.env`:
   ```env
   OLLAMA_MODEL=phi3:mini
   ```

3. Restart the app.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `● OFFLINE` badge in sidebar | Run `ollama serve` in a terminal |
| Model not found error | Run `ollama pull phi` (or your chosen model) |
| Slow generation | Use a smaller model (`phi` instead of `phi3`) or reduce Response Length |
| Port already in use | Change port: `streamlit run app.py --server.port 8502` |

---

## Tech Stack

- [Streamlit](https://streamlit.io) — Frontend UI
- [Ollama](https://ollama.com) — Local LLM runtime
- [Phi (Microsoft)](https://ollama.com/library/phi) — Default language model
- [python-dotenv](https://pypi.org/project/python-dotenv/) — Environment management
