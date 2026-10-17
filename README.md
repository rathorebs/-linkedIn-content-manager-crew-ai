# LinkedIn Content Manager

A five-agent [CrewAI](https://www.crewai.com/) pipeline, powered by Claude, that turns a topic into a publish-ready LinkedIn post with a posting schedule:

**Research → Writing → Critique → Optimization → Scheduling**

You can use it in two ways:

- **Web app:** a FastAPI backend (`api.py`) and a React frontend (`frontend/`)
- **Command line:** `linkedin_content_manager.py`

---

## 1. Prerequisites

| Tool | Version | Check with |
|---|---|---|
| Python | **3.10 – 3.13** (CrewAI does not support 3.14 yet) | `python3 --version` |
| Node.js | **20.19+ or 22.12+** (needed only for the frontend) | `node --version` |
| npm | comes with Node.js | `npm --version` |

You also need two API keys:

- **Anthropic (Claude):** https://console.anthropic.com/settings/keys
- **Serper (Google search for the research agent):** https://serper.dev (has a free tier)

---

## 2. One-time setup

Clone the repository and run all commands from the project folder:

```bash
git clone https://github.com/rathorebs/-linkedIn-content-manager-crew-ai.git
cd -linkedIn-content-manager-crew-ai
```

### 2.1 Python environment and backend dependencies

```bash
python3.12 -m venv .venv              # skip if .venv already exists
source .venv/bin/activate             # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2.2 API keys

```bash
cp .env.example .env
```

Open `.env` and fill in your keys:

```dotenv
ANTHROPIC_API_KEY=sk-ant-...
SERPER_API_KEY=...

# Optional
CLAUDE_MODEL=claude-sonnet-5-5   # default: claude-opus-5-5
MAX_RETRIES=2                    # retries for temporary API errors
```

Keep `.env` private. It is already listed in `.gitignore`.

### 2.3 Frontend dependencies and build

```bash
cd frontend
npm install
npm run build        # creates frontend/dist, which the backend serves
cd ..
```

---

## 3. Running the app

### Option A: one process (recommended for everyday use)

The backend serves the built frontend, so you only start one server:

```bash
source .venv/bin/activate
python api.py
```

Open **http://127.0.0.1:8000**.

To use a different port, run `PORT=8080 python api.py`.

**Or use the helper script.** `./server.sh start` starts **both** the backend and the frontend dev server in the background, so you can close the terminal. See [Helper script](#helper-script-serversh) below.

### Option B: development mode (hot reload while editing the UI)

Use two terminals.

**Terminal 1, the backend:**

```bash
source .venv/bin/activate
python api.py                # API on http://127.0.0.1:8000
```

**Terminal 2, the frontend:**

```bash
cd frontend
npm run dev                  # UI on http://localhost:5173
```

Open **http://localhost:5173**. The Vite dev server forwards `/api` requests to the backend on port 8000. UI changes reload instantly.

When you're done editing, run `npm run build` again so Option A serves the latest UI.

### Helper script (`server.sh`)

One command starts both servers from Option B in the background, with no terminals to keep open and no `source .venv/bin/activate` needed:

```bash
./server.sh start       # backend (8000) + frontend (5173)
./server.sh stop        # stop both
./server.sh restart     # stop, then start both
./server.sh status      # which servers are running
./server.sh logs        # follow both logs (Ctrl+C to exit)
```

Then open **http://localhost:5173**. The backend also still serves the built UI at http://127.0.0.1:8000.

Add `backend` or `frontend` to act on just one, for example `./server.sh restart frontend`.

- **Logs:** written to `logs/backend.log` and `logs/frontend.log`.
- **First start:** if `frontend/node_modules` is missing, the script runs `npm install` first.
- **Other ports:** `PORT=8080 FRONTEND_PORT=5174 ./server.sh start`. The frontend's `/api` proxy follows `PORT` automatically. Use the same variables with `stop` and `status`.
- **Servers started by hand:** `stop` also finds a server started with `python api.py` or `npm run dev`, and only ever stops `api.py` or Vite processes.

### Option C: command line only (no frontend)

```bash
source .venv/bin/activate
python linkedin_content_manager.py "AI agents for B2B sales"
# or run it without a topic and it will ask for one
python linkedin_content_manager.py
```

The final brief prints in the terminal.

---

## 4. Using the web app

1. Type a topic, or click one of the examples, then click **Generate post**.
2. Watch the 5 stages progress. You can expand each stage's output as soon as it finishes.
3. When the run completes, you get:
   - A LinkedIn-style **preview of the final post**. The "…see more" cut-off shows what appears above the fold.
   - A **Copy post** button.
   - The full **publishing brief**: posting time, hashtag strategy and first-hour engagement plan.
4. Past runs are listed under **Saved reports** in the sidebar.

Notes:

- **Run time:** a run usually takes **5–20 minutes**. You can refresh the page and it will reconnect to the run in progress.
- **One run at a time:** while a run is in progress, the backend rejects new runs.
- **Saved reports:** every finished run is saved as Markdown in `outputs/`.

---

## 5. Cost

Every run makes several hundred Claude API calls. From test runs:

| Model (`CLAUDE_MODEL`) | Tokens per run | Approx. cost per run |
|---|---|---|
| `claude-sonnet-5-5` | ~1.5M | ~$4–5 |
| `claude-opus-5-5` (default) | ~2.7M | ~$13–14 |

These are estimates at list prices and will vary by topic.

---

## 6. API reference

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/health` | Model in use and any missing API keys |
| POST | `/api/runs` | Start a run. Body: `{"topic": "..."}` |
| GET | `/api/runs` | Runs since the server started |
| GET | `/api/runs/{id}` | Live status and stage outputs of one run |
| GET | `/api/reports` | Saved reports in `outputs/` |
| GET | `/api/reports/{name}` | Content of one saved report |

Interactive API docs are at **http://127.0.0.1:8000/docs** while the backend is running.

---

## 7. Troubleshooting

| Problem | Fix |
|---|---|
| `pip install` only finds an old CrewAI version | You're on Python 3.14. Create the venv with `python3.12` (see 2.1). |
| Yellow banner: "Missing API keys in .env" | Fill in `.env` (see 2.2), then restart `python api.py`. |
| "Can't reach the backend" in the browser | Start the backend with `python api.py`. |
| Blank page at http://127.0.0.1:8000 | The frontend hasn't been built yet. Run `npm run build` in `frontend/`. |
| `Address already in use` | Another server is on port 8000. Stop it, or use `PORT=8080 python api.py`. In development mode, start Vite with `API_PORT=8080 npm run dev` so its proxy follows (`server.sh` does this for you). |
| "Authentication failed" | Check `ANTHROPIC_API_KEY` and `SERPER_API_KEY` in `.env`. |
| "Anthropic credit balance is too low" | Add credit at https://console.anthropic.com/settings/billing. |
| The first run is slow before Stage 1 starts | Crew memory downloads a small local embedding model (~80 MB) once. |

---

## 8. Security

The app has **no login**. It is meant to run on your own machine at `127.0.0.1`. Don't expose port 8000 to the internet as-is, because anyone who can reach it could start runs that spend your API credit.

---

## 9. Project structure

```
CrewAI/
├── linkedin_content_manager.py   # The 5 agents, 5 tasks and crew; also the CLI
├── api.py                        # FastAPI backend (also serves frontend/dist)
├── server.sh                     # Start/stop backend + frontend in the background
├── requirements.txt              # Python dependencies
├── .env.example                  # Template for .env
├── outputs/                      # Saved reports (one .md per run)
└── frontend/                     # React + TypeScript + Vite app
    ├── src/
    │   ├── App.tsx               # Page layout, polling, state
    │   ├── api.ts                # Backend client
    │   ├── components/           # TopicForm, RunView, FinalPost, History, ReportView
    │   └── styles.css            # Light and dark themes
    ├── vite.config.ts            # Dev server and /api proxy
    └── package.json
```
