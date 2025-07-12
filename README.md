# ClubOS – Mission Control

Central nervous system for Clubhouse 24/7 Golf operations.  
Modular backend + UI for task processing, ticket generation, SOP logic, and operational intelligence.

---

## 📦 Folder Structure

```
backend/
    main.py
    engine_foundation.py
    ticket-system-implementation.py
    knowledge_base.py
    database.py
    requirements.txt
frontend/
    index.html
.env.example
README.md
```

---

## 🚀 Setup Instructions

1. **Clone the repo**  
   ```bash
   git clone https://github.com/clubhousegolfcanada/ClubOS.git
   cd ClubOS
   ```

2. **Create a `.env` file** (based on `.env.example`)

3. **Install dependencies**  
   ```bash
   pip install -r backend/requirements.txt
   ```

4. **Run FastAPI backend**  
   ```bash
   uvicorn backend.main:app --reload
   ```

5. **Open frontend**  
   Open `frontend/index.html` in your browser

---

## 🧱 Tech Stack

- FastAPI (Python)
- SQLAlchemy (PostgreSQL)
- OpenAI API
- Custom HTML/CSS/JS UI
- Modular logic system with tone, escalation, SOPs

---

## 🛠 Dev Notes

- Avoid editing `.env.example` directly
- Keep Claude/ChatGPT versions synced to this repo
- Use commit messages like: `feature: add escalation handling`

