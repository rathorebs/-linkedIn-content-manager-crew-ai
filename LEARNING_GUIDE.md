# CrewAI Project: A Step-by-Step Guide for Beginners

This guide is written for beginners. It works even if you have never learned Python.

Each idea is first explained in **plain language with an example**, and then the **real code** is shown. Read it slowly, one part at a time.

---

## Part 0: What did we build? (The big picture)

Imagine you run a small **marketing company** with **5 employees**. Each employee has exactly one job:

| # | Employee | Their job |
|---|---|---|
| 1 | **Researcher** | Searches the internet to see what's trending on LinkedIn right now |
| 2 | **Writer** | Reads the research and writes the first draft of a LinkedIn post |
| 3 | **Critic** | Reviews the draft, points out problems, and gives it a score out of 10 |
| 4 | **Optimizer** | Rewrites the post using the Critic's feedback to make it better |
| 5 | **Scheduler** | Says which day and time to post, which hashtags to use, and so on |

The work happens **in order**. Each employee finishes their work and hands the result to the next one, like passing the baton in a relay race.

```
Topic  →  Researcher  →  Writer  →  Critic  →  Optimizer  →  Scheduler  →  Final Post ✅
```

**The twist:** these 5 employees aren't people. They are **AI agents**. Their "brain" is **Claude**, Anthropic's AI model, and the library that runs them as a team is called **CrewAI**.

We built this project in **3 parts**:

1. **Pipeline:** `linkedin_content_manager.py`. This is the actual AI team. You can also run it from the terminal.
2. **Backend (API):** `api.py`. This is the "waiter" between the website and the AI team.
3. **Frontend (website):** the `frontend/` folder. This is the screen you see in the browser, where you type a topic.

---

## Part 1: Some basic words first

Learn these words before you read the code. They come up again and again in this guide.

### 1.1 Python
A programming language, which is a way to talk to the computer. Python files end in `.py`.

### 1.2 Package / Library
Ready-made code written by someone else that we use in our project. For example, `crewai` is a library. Because of it, we don't have to write all the code for AI agents ourselves.

The command to install a library:
```bash
pip install crewai
```
`pip` is like Python's "app store". It downloads and installs libraries.

### 1.3 `requirements.txt`
This file holds **the list of all the libraries** the project needs. One command installs them all at once:
```bash
pip install -r requirements.txt
```

### 1.4 Virtual environment (`.venv`)
Think of each project as having its own separate **"room"**. So that Project A's libraries don't get mixed up with Project B's, every project gets its own virtual environment. Our room is the `.venv` folder.

```bash
python3.12 -m venv .venv          # build the room (only once)
source .venv/bin/activate         # enter the room (in every new terminal)
```

> **Why did we use Python 3.12?** Your Mac had Python 3.14, but CrewAI doesn't work on 3.14 yet. So we created `.venv` with Python 3.12.

### 1.5 API key
A **secret password** that online services like Claude (Anthropic) or Serper (Google search) use to know who is sending a request and who to bill.

### 1.6 The `.env` file
This is where we keep the API keys. We don't write keys directly in the code, because they would leak if the code were shared.

```dotenv
ANTHROPIC_API_KEY=sk-ant-...
SERPER_API_KEY=...
CLAUDE_MODEL=claude-sonnet-5-5
```

`.env.example` is an "empty copy" of that file that shows which keys are needed. The real keys only go in `.env`.

### 1.7 LLM (Large Language Model)
An AI that reads and writes text, such as Claude or ChatGPT. This is our agents' "brain".

### 1.8 The 4 main CrewAI words

| Word | Meaning | Office example |
|---|---|---|
| **Agent** | An AI worker with a role, a goal and a background | An employee |
| **Task** | A piece of work given to an agent | An assignment given to an employee |
| **Tool** | An extra ability the agent can use | The employee's laptop or internet access |
| **Crew** | The whole team of agents and tasks working together | The whole company |

---

## Part 2: The project's folders and files

```
CrewAI/
├── .venv/                        ← Python's "room" (libraries are installed here)
├── .env                          ← Your secret API keys (never share this!)
├── .env.example                  ← Empty template for .env
├── requirements.txt              ← List of Python libraries
├── linkedin_content_manager.py   ← ⭐ The AI team (5 agents + 5 tasks)
├── api.py                        ← Backend: the waiter between the website and the AI team
├── server.sh                     ← Script to start/stop backend + frontend in the background
├── logs/                         ← server.sh writes the servers' logs here
├── outputs/                      ← Each run's report is saved here (.md files)
├── README.md                     ← Steps to run the project
├── LEARNING_GUIDE.md             ← This file 🙂
└── frontend/                     ← The website (React)
    ├── package.json              ← List of the website's libraries (like Python's requirements.txt)
    └── src/                      ← The website's code
```

---

## Part 3: How development went (what we did, in what order)

This project wasn't built all at once. These steps happened one after another:

| Step | What we did | Why |
|---|---|---|
| 1 | Created a Python 3.12 `.venv` | CrewAI doesn't install on Python 3.14 |
| 2 | Wrote `linkedin_content_manager.py`: 5 agents, 5 tasks, 1 crew | This is the actual AI team |
| 3 | Created `requirements.txt` and `.env.example` | So anyone can set up the project |
| 4 | Fixed a warning (made the callback a "module-level function") | The newer CrewAI version required it (see Part 4.7) |
| 5 | **Switched from OpenAI to Claude** | You wanted to use a Claude API key |
| 6 | Added a local "embedder" for memory | Anthropic doesn't offer embeddings (see Part 4.8) |
| 7 | First real run (Claude Opus): all 5 stages passed ✅ | Testing |
| 8 | Switched the model to **Sonnet 5.5** (in `.env`) | Cost dropped to about a third |
| 9 | Built `api.py` (the backend) | So the AI team can run from a website |
| 10 | Built `frontend/` (the React website) | For a nicer screen, live progress and a copy button |
| 11 | Tested in the browser and fixed a table bug | Quality check |
| 12 | Wrote `README.md` and this guide | Documentation |
| 13 | Wrote `server.sh` (start/stop script) | One command starts or stops both backend and frontend in the background (see Part 5.7) |

Now let's look at each part in detail.

---

## Part 4: `linkedin_content_manager.py`, the AI team's code

This is the **most important file** in the project. We'll read it from top to bottom, one piece at a time.

### 4.1 `import`: bringing in libraries

```python
import os
import sys
import time
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()
```

**In plain words:**
- `import os` means: "Python, give me the toolbox called `os`."
  - `os` reads computer settings, such as environment variables.
  - `sys` can stop the program.
  - `time` can wait (sleep).
- `from datetime import datetime` means: "from the `datetime` toolbox, give me only the `datetime` tool." It gives today's date and time.
- `load_dotenv()` reads your `.env` file and loads the keys into the program.

> 💡 **Beginner tip:** a line that starts with `#` is a **comment**. Python ignores it. Comments are only there for people to read.

### 4.2 Constants: values that never change

```python
REQUIRED_ENV_VARS = {
    "ANTHROPIC_API_KEY": "https://console.anthropic.com/settings/keys",
    "SERPER_API_KEY": "https://serper.dev (free tier available)",
}

DEFAULT_MODEL = "claude-opus-5-5"
MAX_OUTPUT_TOKENS = 16000

STAGES = ["Research", "Writing", "Critique", "Optimization", "Scheduling"]
```

**In plain words:**
- `REQUIRED_ENV_VARS` is a **dictionary** (`{}`): a list of **key → value** pairs, like name → number in a phone book. Here it maps each key's name → the website where you get that key.
- `"claude-opus-5-5"` is a **string** (text). Text written inside quotes `" "` is a string.
- `16000` is an **integer** (a whole number). It's the limit on how many tokens (roughly words) Claude can write in one reply.
- `STAGES` is a **list** (`[]`), a line of items. `STAGES[0]` = `"Research"`. In Python, **counting starts at 0**!
- The names are in CAPITAL letters. That's a convention meaning "this value never changes".

### 4.3 Functions: giving a job a name

A **function** is a small machine: you give it input, it does the work, and it can give back output.

```python
def banner(title: str, char: str = "=") -> None:
    """Print a full-width section banner."""
    line = char * 80
    print(f"\n{line}\n{title.center(80)}\n{line}\n", flush=True)
```

**Line by line:**
- `def banner(...)` means "create a function called `banner`."
- `title: str` means the input is called `title` and should be a string.
- `char: str = "="`: if you don't pass `char`, the default `"="` is used.
- `-> None`: this function doesn't return anything. It only prints.
- `"""..."""` is a **docstring**, which describes what the function does.
- `char * 80` repeats the string 80 times: `"====...===="`.
- `f"...{line}..."` is an **f-string**. The variable's value goes inside the `{ }`.
- `\n` means a new line.

**How to use it:**
```python
banner("STAGE 1/5: RESEARCH")
```
The terminal shows:
```
================================================================================
                              STAGE 1/5: RESEARCH
================================================================================
```

> **Indentation (blank space at the start of a line) matters a lot!** In Python, lines inside a function are indented by 4 spaces. That's how Python knows which lines belong to the function.

### 4.4 Checks: are the keys and the topic valid?

```python
def missing_env_vars() -> list[str]:
    """Return the required API keys that are unset or still placeholders."""
    return [
        name
        for name in REQUIRED_ENV_VARS
        if not os.getenv(name) or os.getenv(name, "").startswith("your_")
    ]
```

**In plain words:** check every required key. If a key is **empty**, or still has the template value `your_...`, add that key's name to the list. At the end, return the list of "missing keys".

- `os.getenv("ANTHROPIC_API_KEY")` reads the key's value from `.env`.
- `[... for name in ... if ...]` is a **list comprehension**, a short way to build a list with a loop.

```python
def validate_topic(topic: str) -> str:
    topic = topic.strip()
    if len(topic) < 3:
        raise PipelineError("Topic must be at least 3 characters long.", ...)
    if len(topic) > 200:
        raise PipelineError("Topic is too long (max 200 characters). ...")
    return topic
```

- `.strip()` removes extra spaces at the start and end.
- `len(topic)` tells you how many characters the topic has.
- `if` means "if this is true, do this."
- `raise PipelineError(...)` means **throw an error**: "stop, something is wrong!"

**What is `PipelineError`?** It's an error type we made ourselves:
```python
class PipelineError(Exception):
    def __init__(self, message: str, hint: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.hint = hint
```
- A **class** is a "mould" (template). `PipelineError` is a special error that holds 2 things: `message` (what went wrong) and `hint` (how to fix it).
- `Exception` is Python's built-in error type. We built our error on top of it.

> 🧠 **Don't worry if classes don't fully make sense yet.** Just remember: "A class is a mould. Objects are made from it."

### 4.5 The LLM: the agents' brain (Claude)

```python
def build_llm() -> LLM:
    model = os.getenv("CLAUDE_MODEL", DEFAULT_MODEL)
    return LLM(
        model=f"anthropic/{model}",
        max_tokens=MAX_OUTPUT_TOKENS,
        timeout=300,
        max_retries=2,
    )
```

**In plain words:**
- `os.getenv("CLAUDE_MODEL", DEFAULT_MODEL)`: if `.env` sets `CLAUDE_MODEL`, use that model. Otherwise use the default (`claude-opus-5-5`). Your `.env` has `claude-sonnet-5-5`, so Sonnet runs.
- `LLM(...)` is the CrewAI class that connects to Claude.
- `"anthropic/..."` tells CrewAI the model comes from **Anthropic**.
- `timeout=300`: stop if Claude doesn't answer within 300 seconds (5 minutes).
- `max_retries=2`: if there's an error, try 2 more times.

**Some things were left out on purpose:**
- **No `temperature`:** newer Claude models don't accept it and return an error.
- **`max_tokens` set by us:** otherwise CrewAI asks for 128,000, and Anthropic's library refuses a request that large without streaming.

> We found both of these by reading CrewAI's internal code while switching from OpenAI to Claude.

### 4.6 Agents: the 5 AI employees

Every agent has these fields:

| Field | Meaning |
|---|---|
| `role` | Their job title |
| `goal` | What they need to achieve |
| `backstory` | Their experience and personality. This helps the AI "role-play" better |
| `tools` | Extra abilities (only the Researcher has them) |
| `llm` | The brain (Claude) |
| `verbose=True` | Show its thinking and work in the terminal |
| `allow_delegation=False` | Don't hand its work off to another agent |

**Researcher (the agent with tools):**
```python
researcher = Agent(
    role="LinkedIn Trend Researcher",
    goal="Research latest trending topics, hashtags, and content themes for a given niche",
    backstory=(
        "You are an expert social media researcher who monitors LinkedIn trends, "
        "viral posts, and industry news every day. ..."
    ),
    tools=[SerperDevTool(), ScrapeWebsiteTool()],
    llm=llm,
    verbose=True,
    allow_delegation=False,
    max_iter=15,
)
```

- `SerperDevTool()` lets the agent **search Google**. This is where the Serper key is needed.
- `ScrapeWebsiteTool()` lets the agent **read a website's content**.
- `max_iter=15`: the agent takes at most 15 "steps" (searching, reading, thinking). This keeps it from getting stuck in an endless loop.

**The other 4 agents** (Writer, Critic, Optimizer, Scheduler) are built the same way. The only difference is that their `tools=[]` is **empty**: they only think and write, without using the internet.

At the end, all the agents are returned in a **dictionary**:
```python
return {
    "researcher": researcher,
    "writer": writer,
    "critic": critic,
    "optimizer": optimizer,
    "scheduler": scheduler,
}
```
That way, writing `agents["writer"]` later gets you the Writer agent.

### 4.7 Tasks: each employee's assignment

```python
research_task = Task(
    description=(
        "Research the latest trends, viral content patterns, and hot topics on LinkedIn "
        "for the niche: {topic}.\n\n"
        ...
    ),
    expected_output=(
        "A structured research brief in markdown with these sections:\n"
        "1. Trending Topics ...\n"
        ...
    ),
    agent=agents["researcher"],
    callback=on_stage_complete,
)
```

| Field | Meaning |
|---|---|
| `description` | What the work is (the instructions) |
| `expected_output` | What the result should look like |
| `agent` | Who does this work |
| `context` | Which earlier tasks' results this task should read |
| `callback` | Which function to run when the task finishes |

**What is `{topic}`?** It's a **placeholder** (a blank to fill in). When you give the topic "AI agents for B2B sales", CrewAI puts that text in place of `{topic}`.

**The magic of `context`:** each task needs earlier results:
```python
writing_task       → context=[research_task]                    # read the research, then write
critique_task      → context=[writing_task]                     # read the draft, then critique it
optimization_task  → context=[writing_task, critique_task]      # read both the draft and the critique
scheduling_task    → context=[research_task, optimization_task] # read the research and the final post
```
The Optimizer needs **both the draft and the critique**. Only then can it apply the feedback and improve the draft.

**`callback=on_stage_complete`**: this function runs every time a task finishes:
```python
def on_stage_complete(output: TaskOutput) -> None:
    stage_index = ROLE_TO_STAGE.get(output.agent.strip())
    if stage_index is None:
        return
    banner(f"STAGE {stage_index + 1}/{len(STAGES)} COMPLETE: {STAGES[stage_index].upper()}")
    _emit("stage_completed", stage=stage_index, output=output.raw)
    ...
```
- This function prints a banner in the terminal, such as "STAGE 2/5 COMPLETE: WRITING".
- `_emit(...)` tells the website that a stage has finished (details in Part 5).
- `ROLE_TO_STAGE` is a dictionary that maps an agent's role to its stage number, for example `"Content Quality Critic"` → `2`.

> **The warning from Step 4:** at first we created a separate "inner" function (a closure) for each task. The newer CrewAI version warned that such functions can't be saved (serialized). So we made one **file-level function**, `on_stage_complete`, that all tasks share.

### 4.8 The crew: putting the whole team together

```python
def build_crew() -> Crew:
    agents = build_agents(build_llm())
    tasks = build_tasks(agents)

    return Crew(
        agents=list(agents.values()),
        tasks=tasks,
        process=Process.sequential,
        verbose=True,
        memory=True,
        embedder={"provider": "onnx"},
    )
```

| Setting | Meaning |
|---|---|
| `process=Process.sequential` | Tasks run **one after another**: 1 → 2 → 3 → 4 → 5 |
| `verbose=True` | Show everything in the terminal |
| `memory=True` | The team's **memory** is on. Agents can remember earlier things |
| `embedder={"provider": "onnx"}` | The tool that turns text into numbers for memory |

**What is an embedder?** A computer can't "remember" text directly. So text is turned into a **list of numbers** (an embedding). For example, "LinkedIn tips" → `[0.12, -0.45, 0.88, ...]` (384 numbers). Text with similar meaning gets similar numbers.

**Why did we use ONNX?** By default, CrewAI uses **OpenAI** embeddings for memory, and we had already switched from OpenAI to Claude. Anthropic doesn't offer an embeddings service. So we run a **small free model** (all-MiniLM-L6-v2, ~80 MB) on your own computer. No key needed, no cost.

### 4.9 Error handling: when something goes wrong

The internet and APIs sometimes fail. The code sorts errors into **2 groups**:

| Type | Example | What we do |
|---|---|---|
| **Fatal** (retrying won't help) | Wrong API key, no credit left, wrong model name | Stop right away with a clear message |
| **Transient** (a short-lived problem) | Rate limit, timeout, overloaded server | Wait a bit, then try again |

```python
def run_crew(topic: str):
    max_retries = int(os.getenv("MAX_RETRIES", "2"))

    for attempt in range(max_retries + 1):
        try:
            crew = build_crew()
            return crew.kickoff(inputs={"topic": topic})
        except Exception as exc:
            kind = classify_error(exc)
            if kind == "fatal":
                raise PipelineError(*fatal_message(exc)) from exc
            if attempt < max_retries and kind == "transient":
                wait = 10 * (2**attempt)      # 10s, then 20s, then 40s...
                time.sleep(wait)
                continue
            raise PipelineError("The crew failed to complete.", ...) from exc
```

**New Python words:**
- `for attempt in range(3):` is a **loop**. It runs 3 times, with `attempt` = 0, 1, 2.
- `try:` / `except:` means "**try** this code. If there's an error, don't crash; run the `except` part instead."
- `crew.kickoff(inputs={"topic": topic})` ⭐ **this one line starts the whole AI team!** Your topic is put in place of the `{topic}` placeholder.
- `return` gives back a value and ends the function.
- `continue` means "start the next round of the loop" (that is, try again).
- `2**attempt` means 2 to the power of `attempt`. The wait doubles each time. This is called **exponential backoff**.

### 4.10 Saving the report

```python
def save_report(topic: str, result) -> Path:
    OUTPUT_DIR.mkdir(exist_ok=True)
    slug = re.sub(r"[^a-z0-9]+", "-", topic.lower()).strip("-")[:50] or "post"
    path = OUTPUT_DIR / f"{datetime.now():%Y%m%d_%H%M%S}_{slug}.md"
    ...
    path.write_text("\n".join(parts), encoding="utf-8")
    return path
```

- `mkdir(exist_ok=True)` creates the `outputs` folder (no problem if it already exists).
- `slug` turns the topic into something file-name friendly: `"AI agents for B2B sales"` → `"ai-agents-for-b2b-sales"`.
- The file name looks like this: `20261017_134003_ai-agents-for-b2b-sales.md` (date_time_topic).
- `write_text(...)` writes the results of all 5 stages into the file.

### 4.11 `main()`: where the program starts

```python
def main() -> None:
    banner("AUTONOMOUS LINKEDIN CONTENT MANAGER")
    validate_environment()          # 1. Check the keys
    topic = get_topic()             # 2. Get the topic from the user

    try:
        result = run_crew(topic)    # 3. Run the AI team
    except PipelineError as exc:
        fail(exc.message, exc.hint) # 3b. On error, show the message and stop

    banner("FINAL PUBLISHING BRIEF")
    print(result.raw)               # 4. Print the final result
    report = save_report(topic, result)   # 5. Save it to a file


if __name__ == "__main__":
    main()
```

**What is `if __name__ == "__main__":`?**
- When you run `python linkedin_content_manager.py`, Python treats this file as "main", so `main()` runs.
- When `api.py` **imports** this file, `main()` does **not** run. Only the functions are used.

This trick lets **one file** run from the terminal and also work inside the website's backend.

---

## Part 5: `api.py`, the backend (the waiter)

### 5.1 Why do we need a backend?
A browser (the website) can't run Python code directly. So we need a **server** in between:

```
Website (browser)  ──"here's a topic, start a run"──▶  api.py  ──▶  AI team
Website (browser)  ◀──"stage 2 done, here's the output"──  api.py
```

Think of a restaurant: you (the website) give your order to the waiter (the API), the waiter takes it to the kitchen (the AI team), and brings the food back when it's ready.

### 5.2 FastAPI and endpoints
**FastAPI** is a Python library for building APIs. An **endpoint** is a URL that requests are sent to:

| Request | URL | Job |
|---|---|---|
| GET | `/api/health` | Is the server OK? Which model? Any keys missing? |
| POST | `/api/runs` | Start a new run (send the topic) |
| GET | `/api/runs/{id}` | Get a run's live status |
| GET | `/api/reports` | List of saved past reports |
| GET | `/api/reports/{name}` | The content of one report |

**GET** means "ask for something". **POST** means "send something / create something new".

```python
@app.get("/api/health")
def health() -> dict[str, Any]:
    return {
        "ok": True,
        "model": os.getenv("CLAUDE_MODEL", pipeline.DEFAULT_MODEL),
        "missing_keys": pipeline.missing_env_vars(),
        "stages": pipeline.STAGES,
    }
```
- `@app.get(...)` is a **decorator**. It tells FastAPI: "when someone opens `/api/health`, run this function."
- FastAPI converts the dictionary the function returns into **JSON** (the website's language) and sends it.

### 5.3 Threads: working in the background
The AI team takes **5 to 20 minutes** to run. If the server waited that long, the website would "hang". So we run the AI team in a **separate thread** (a background worker):

```python
threading.Thread(target=_execute, args=(run_id, topic), daemon=True).start()
```

Meaning: "create a new worker that runs `_execute(run_id, topic)`, so the main server stays free."

### 5.4 How do we track progress? (Listeners)
We built a small "notice board" system in the pipeline file:

```python
_progress_listeners = []           # the list of listeners

def _emit(event, **data):          # post news on the notice board
    for listener in list(_progress_listeners):
        listener(event, **data)
```

- `api.py` registers its own listener, which is like saying "let me know too."
- Whenever a stage starts or finishes, `_emit("stage_completed", stage=1, output=...)` runs.
- The API writes that news into its memory (the `_runs` dictionary).
- Every 2 seconds the website asks "any updates?" and shows the API's answer live.

### 5.5 Safety rules
- **Only one run at a time:** runs are long, cost money, and share memory. If you ask for a second run, the API returns a `409` error.
- **Path traversal blocked:** so nobody can request `/api/reports/../.env` and read your secret file, only `.md` files inside `outputs/` can be opened.
- **Lock (`threading.Lock`):** so two threads don't change the same data at once, we use a "lock".

### 5.6 Why did we create `PipelineError`?
Before, the code called `sys.exit()` on errors, which **stops the whole program**. That was fine for the terminal, but not for a server: one failed run would take down the whole website! So the pipeline now **raises** a `PipelineError`:
- The terminal version catches it and stops the program.
- The API catches it, shows a red error message on the website, and the server keeps running.

### 5.7 Starting and stopping both servers with `server.sh`

When you run `python api.py`, the server lives inside that terminal window. Close the window (or press Ctrl+C) and the server stops. During development you also need a second terminal for the frontend (`npm run dev`, see Part 6.4). That's two windows to keep open.

`server.sh` is a "remote control" that starts **both servers in the background** with one command, and stops them later from any terminal:

| Server | What it runs | Address |
|---|---|---|
| **backend** | `api.py` (FastAPI) | http://127.0.0.1:8000 |
| **frontend** | Vite dev server (React, with hot reload) | http://localhost:5173 |

```bash
./server.sh start      # start backend + frontend in the background
./server.sh stop       # stop both
./server.sh restart    # stop, then start both
./server.sh status     # which servers are running?
./server.sh logs       # watch both logs live (Ctrl+C to exit)
```

After `start`, open **http://localhost:5173**.

- `./` means "the file in this folder". So `./server.sh` runs the `server.sh` file from the project folder.
- The word after it (`start`, `stop`, ...) is an **argument**: it tells the script which job to do.
- You can add a **second argument** to act on just one server:
  ```bash
  ./server.sh restart frontend   # restart only the website
  ./server.sh logs backend       # only the backend's log
  ```

#### What is a `.sh` file?
It's a **shell script**: a list of terminal commands saved in a file, so you don't have to type them every time. It's written in **Bash**, the language of the terminal, not Python. The first line tells the computer which language to use:

```bash
#!/usr/bin/env bash
```

The file was made runnable once with `chmod +x server.sh` ("x" stands for execute).

#### Key idea: the PID
Every running program gets a number from the computer, called a **PID** (Process ID), like a token number at a bank. To stop a program, you tell the computer: "stop the program with PID 24277." That's what the `kill` command does.

When `start` runs a server, it saves that server's PID in a small file: `.backend.pid` for the backend and `.frontend.pid` for the frontend. Later, `stop` reads those numbers and stops exactly those programs.

#### How `start` works

`start` starts the backend first, then the frontend. The backend line:

```bash
PORT="$PORT" nohup "$PYTHON" api.py </dev/null >>"$log" 2>&1 &
echo $! >"$(pid_file "$1")"
```

- `"$PYTHON"` is `.venv/bin/python`, the Python inside our "room". So you **don't need `source .venv/bin/activate`**.
- `nohup` keeps the server running even after you close the terminal.
- `>>"$log" 2>&1` sends everything the server prints (normal output and errors) into `logs/backend.log` instead of the screen.
- The `&` at the end means "run this in the background and give me the terminal back."
- `$!` is the PID of the program just started. `echo $! > .backend.pid` saves it to the file.

The frontend line works the same way, but runs Vite inside the `frontend` folder:

```bash
(cd frontend && API_PORT="$PORT" exec nohup ./node_modules/.bin/vite \
    --port "$FRONTEND_PORT" --strictPort) </dev/null >>"$log" 2>&1 &
```

- `( ... )` runs the commands in a small separate shell, so `cd frontend` doesn't change the folder for the rest of the script.
- `./node_modules/.bin/vite` is the same program `npm run dev` runs. We call it directly because of `exec`: it makes the saved PID belong to Vite itself, so `stop` can stop it. (With `npm run dev`, the PID would belong to `npm`, and stopping `npm` can leave Vite still running.)
- `--strictPort` means: if port 5173 is taken, fail with an error instead of quietly picking another port.
- `API_PORT="$PORT"` tells Vite where the backend is, so its `/api` proxy (Part 6.4) points to the right port.

Then, for each server, the script waits up to 30 seconds and keeps asking it "are you there?" with `curl`. For the backend it asks `/api/health` (the same endpoint from 5.2); for the frontend it asks for the home page. As soon as the server answers, it prints "Running". If the server crashes instead, it shows the last 20 lines of its log so you can see why.

`start` also checks a few things first:
- Is the server **already running**? Then it just says so, instead of starting a second copy.
- Does `.venv` exist? Is `npm` installed? Are the **ports (8000 and 5173) free**?
- Is `frontend/node_modules` missing? Then it runs `npm install` once by itself.

#### How `stop` works

```bash
kill "$pid"
```

`kill` politely asks the program to shut down. The script waits up to 10 seconds. If the server still hasn't stopped, it uses `kill -9`, which forces it. Then it deletes the `.pid` file.

`stop` stops the frontend first and the backend second, because the website depends on the backend (the reverse of `start`).

If you started a server yourself with `python api.py` or `npm run dev`, there is no `.pid` file. In that case the script finds the program using the port (8000 or 5173) with `lsof`, and **only** stops it if it really is `api.py` or Vite. That way it never stops some other program by mistake.

#### Functions and `case` in Bash
The script is organised just like our Python file: one function per job (`start_one()`, `stop_one()`, `status_one()`), and a "menu" at the bottom that picks the function based on your argument:

```bash
case "${1:-}" in
    start) start_all $TARGETS ;;
    stop) stop_all $STOP_ORDER ;;
    restart) stop_all $STOP_ORDER && start_all $TARGETS ;;
    ...
esac
```

- `$1` is the first argument you typed (`start`, `stop`, ...). `$2` is the second one (`backend`, `frontend`, or nothing).
- `$TARGETS` is the list of servers to act on: `backend frontend` by default, or just the one you named.
- `case ... esac` is like a chain of `if` / `elif` in Python. (`esac` is just `case` spelled backwards!)
- `stop_all ... && start_all ...` means "stop, and only if that worked, start."

#### Using different ports
```bash
PORT=8080 FRONTEND_PORT=5174 ./server.sh start
PORT=8080 FRONTEND_PORT=5174 ./server.sh stop
```
`api.py` reads `PORT` with `os.getenv("PORT", "8000")`, the same idea as `CLAUDE_MODEL` in Part 8. The script passes the same port to Vite as `API_PORT`, and `frontend/vite.config.ts` reads it to point its proxy at the backend. Use the same variables for `start`, `stop` and `status`.

> 💡 The `.backend.pid` and `.frontend.pid` files and the `logs/` folder are in `.gitignore`, because they only matter on your own computer.

---

## Part 6: `frontend/`, the website (React)

### 6.1 What is React?
A JavaScript library for building websites. It breaks the screen into small **components** (like Lego blocks):

| Component (file) | What it shows on screen |
|---|---|
| `App.tsx` | The whole page: header, layout and loading data |
| `TopicForm.tsx` | The topic box, the "Generate post" button and example topics |
| `RunView.tsx` | Live progress of the 5 stages (✓, spinner, timer) and stage outputs |
| `FinalPost.tsx` | A LinkedIn-style post preview, "…see more" and the **Copy post** button |
| `History.tsx` | The "Saved reports" list on the side |
| `ReportView.tsx` | The view when you open an old report |
| `Markdown.tsx` | Displays the AI's markdown text (headings, tables) nicely |
| `api.ts` | Functions that talk to the backend |
| `styles.css` | Colours, fonts, layout and dark mode |

**TypeScript (`.tsx`)** is a version of JavaScript with types (like Python's `topic: str`). It catches mistakes earlier.

### 6.2 How does the website update every 2 seconds? (Polling)
```tsx
const timer = setInterval(async () => {
  const latest = await api.getRun(runId);   // ask the backend
  setRun(latest);                           // update the screen
}, 2000);                                   // every 2000 ms = 2 seconds
```
- `setInterval` runs a job over and over.
- `setRun` updates React's **state**. As soon as state changes, React redraws the screen by itself.

### 6.3 How is the final post extracted?
The Scheduler agent writes the final post in its brief inside a **code block** (between \`\`\`), under a "Final Post" heading. The `extractFinalPost` function in `utils.ts` finds that block and pulls it out, and the "Copy post" button copies that text.

### 6.4 Development vs production
- **Development** (`npm run dev`): the website runs at `localhost:5173`. Change the code and you see it right away.
- **Production** (`npm run build`): the website's final files are built into `frontend/dist/`. Then `api.py` serves them itself at `localhost:8000`. One command, the whole app.

---

## Part 7: The whole story of clicking "Generate post"

```
1. You type a topic and click "Generate post"
        │
        ▼
2. TopicForm.tsx → api.ts → POST /api/runs {"topic": "..."}
        │
        ▼
3. api.py: check keys, check topic, is a run already in progress?
        │  creates a run_id and starts a background thread
        ▼
4. Thread: pipeline.run_crew(topic) → crew.kickoff(...)
        │
        ├─▶ Researcher: Google search + reading websites (Claude + Serper)
        ├─▶ Writer: writes the draft
        ├─▶ Critic: score + feedback
        ├─▶ Optimizer: improved version
        └─▶ Scheduler: time, hashtags, final post
        │     (after each stage: on_stage_complete → _emit → api.py's listener)
        ▼
5. Website every 2 seconds: GET /api/runs/{id} → stepper updates (✓ / spinner)
        │
        ▼
6. All done → save_report() → outputs/xxxx.md
        │
        ▼
7. Website: Final Post preview + Copy button + publishing brief 🎉
```

---

## Part 8: Cost and model choice

Every run sends **hundreds of requests** to Claude. That covers the agents' thinking, the internet research and the memory.

| Model | Tokens per run | Approximate cost |
|---|---|---|
| Claude Opus 5.5 | ~2.7 million | ~$13–14 |
| Claude Sonnet 5.5 (currently set) | ~1.45 million | ~$4–5 |

To change the model, change just one line in `.env`:
```dotenv
CLAUDE_MODEL=claude-sonnet-5-5
```
Nothing in the code needs to change, because the code reads the model with `os.getenv("CLAUDE_MODEL", ...)`. **That's the benefit of keeping settings separate from code.**

---

## Part 9: Python concepts used in this project (cheat sheet)

| Concept | Example | Meaning |
|---|---|---|
| Variable | `topic = "AI"` | A box that holds a value |
| String | `"hello"` | Text |
| Integer | `16000` | A whole number |
| List | `["a", "b"]` | A line of items. `list[0]` = the first item |
| Dictionary | `{"name": "Ali"}` | Key → value |
| Function | `def add(a, b): return a + b` | A reusable piece of work |
| Default value | `def f(x="="):` | The value used if no input is given |
| f-string | `f"Hi {name}"` | Putting a variable inside text |
| if / else | `if x > 3: ...` | A condition |
| for loop | `for i in range(3):` | Doing something repeatedly |
| try / except | `try: ... except Exception:` | Catching errors |
| raise | `raise PipelineError(...)` | Throwing an error yourself |
| import | `from crewai import Agent` | Bringing in a tool from a library |
| Class | `class PipelineError(Exception):` | A mould / template |
| Decorator | `@app.get("/api/health")` | A "label" on a function that changes its behaviour |
| Type hint | `topic: str` | Saying what type a value is (only as a help) |
| `__name__ == "__main__"` | at the end of the file | "Run `main()` only if this file was run directly" |

---

## Part 10: Try it yourself (practice ideas)

The best way to learn is to **make small changes yourself**. After each change, run `python linkedin_content_manager.py "some topic"` and see what happens.

**Level 1 (very easy)**
1. Add your own topic to the `EXAMPLES` list in `TopicForm.tsx`.
2. Add "You always write in simple English" to the Writer agent's `backstory`, and see how the post changes.

**Level 2 (a bit harder)**
3. In the writing task, change "150–300 words" to "100–150 words".
4. In `banner()`, use `"*"` instead of `"="`.

**Level 3 (challenge)**
5. Create a **6th agent**, such as a "Hindi Translator" that translates the final post into Hindi. To do this:
   - Create a new `Agent` in `build_agents()`.
   - Create a new `Task` in `build_tasks()` with `context=[optimization_task]`.
   - Add an entry to the `STAGES` list and the `ROLE_TO_STAGE` dictionary.
   - Also add an entry to the `STAGE_INFO` list in the frontend's `RunView.tsx`.

> ⚠️ **Remember:** every run costs real money (~$4–5 on Sonnet). While practising, use short topics and the Sonnet model.

---

## Part 11: Glossary

| Word | Meaning |
|---|---|
| **Agent** | An AI worker with a role, a goal and a backstory |
| **API** | A way for two programs to talk to each other |
| **API key** | The secret password for an online service |
| **Backend** | Server-side code (`api.py`) |
| **Callback** | A function that runs automatically when some work finishes |
| **Crew** | A team of agents and tasks |
| **Embedding** | Turning text into numbers so the computer can work with its "meaning" |
| **Endpoint** | One URL of an API |
| **Frontend** | The part you see in the browser (React) |
| **JSON** | A format for sending data: `{"key": "value"}` |
| **LLM** | Large Language Model, such as Claude |
| **Markdown** | A simple formatting language (`#` heading, `**bold**`) |
| **PID** | Process ID: the number the computer gives every running program |
| **Pipeline** | A line of jobs where one job's output is the next job's input |
| **Polling** | Repeatedly asking "has anything changed?" |
| **Sequential** | One after another |
| **Shell script** | A file of terminal commands (Bash) that runs them for you, like `server.sh` |
| **Thread** | A separate worker running in the background |
| **Token** | A small piece of text (about ¾ of a word). API bills are based on these |
| **Tool** | An agent's extra ability (search, scraping) |
| **Virtual environment** | A project's own "room" that holds its libraries |

---

## What to read next

1. **Python basics:** variables, lists, dictionaries, functions, loops. All of these are in this project.
2. **CrewAI docs:** https://docs.crewai.com
3. **This project's code:** start with `linkedin_content_manager.py`. There are comments above each function.
4. **Steps to run it:** see `README.md`.

Happy learning! 🚀 If anything is unclear, ask about any part by name and I'll explain it in more detail.
