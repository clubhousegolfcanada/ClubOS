
# 🛠️ CLUBOS 3.0 – DEV TODO (MVP IMPLEMENTATION)

## 🧱 BACKEND (API + DB)

- [ ] **Set up FastAPI or Flask backend**
  - Expose `/ticket` (POST), `/tickets` (GET), `/ask` (POST), `/drive-search` (POST)

- [ ] **Define Ticket database model**
  - Fields: `id`, `title`, `description`, `status`, `created_at`

- [ ] **Connect database**
  - Use SQLite (or Postgres), SQLAlchemy or equivalent ORM
  - Hook `/ticket` and `/tickets` to DB read/write

- [ ] **LLM integration**
  - Connect to OpenAI via API key from `.env`
  - Endpoint: `/ask` — return clean text result

- [ ] **Google Drive integration (stub OK)**
  - Service account setup OR mock response
  - Endpoint: `/drive-search` — return file name + link

- [ ] **Add CORS config**
  - Allow frontend JS to call backend locally

---

## 🎨 FRONTEND (HTML + JS)

- [ ] **Wire ticket creation form**
  - Submit to `/ticket`
  - Show success message on submit

- [ ] **Display ticket list**
  - On load: call `/tickets`, render entries
  - Show fallback if empty

- [ ] **Create LLM input box**
  - Submit to `/ask`
  - Display response in a result block

- [ ] **Add Drive search input**
  - Submit to `/drive-search`
  - Render mocked result list

---

## ⚙️ SYSTEM + ENV

- [ ] **Add `.env` support**
  - Store API key, DB path, secret values

- [ ] **Run script or launch doc**
  - `run_backend.sh` or `main.py` to boot server
  - Open `index.html` locally in browser

- [ ] **Final Testing**
  - Test each action from UI
  - Console errors cleaned
  - All endpoints return expected output
