ClubOS Mission Control v2.0

command layer for Clubhouse 24/7 Golf — built for autonomous facility infrastructure, not just operations. 

⸻

SYSTEM OVERVIEW

Layer	Description
ClubCore	Core engine — task parsing, routing, DB logic
ClubOps	SOP processor — muscle memory logic
SignalOS	Strategic simulation engine (for recursion, testing, fallback chains)
Clubhost	Tone enforcement (dry, sharp, human-clone wrapper)
CapabilityFrontier	Guardrails — escalate on fail, alert on hallucination
Ticket Engine	Issue tracker — logs all post-processed output, failure states, and actionables
Drive Search	Google Drive vector-backed retrieval layer for SOPs and documents
UI Layer	HTML/JS-based Command Center — one-click task injection and monitoring


⸻

FILE STRUCTURE

.
├── backend/
│   ├── main.py                   # FastAPI entrypoint
│   ├── engine_foundation.py      # Routing logic (ClubCore)
│   ├── database.py               # DB models + session mgmt (SQLAlchemy)
│   ├── schemas.py                # Pydantic validation
│   ├── bootstrap.py              # Startup routines (indexing, auth)
│   ├── health.py                 # API heartbeat
│   ├── ticket-system-implementation.py  # Ticket logging + escalation logic
│   ├── knowledge_base.py         # Embedded knowledge for classification
├── frontend/
│   └── index.html                # ClubOS UI (Command Console, Dashboard, Ticket Engine)
├── scripts/                      # Placeholder for CLI tools or setup
├── logs/                         # Log files, system snapshots
├── requirements.txt              # Python dependencies


⸻

API ENDPOINTS

Method	Endpoint	Description
GET	/health	Heartbeat ping for frontend check
POST	/process	Main request intake — routes to appropriate engine layers
POST	/ticket	Manual ticket creation
GET	/sop/search	(Planned) Google Drive vector search endpoint


⸻

SETUP
	1.	Install deps

pip install -r requirements.txt


	2.	Run server

uvicorn backend.main:app --reload


	3.	Access UI
Open frontend/index.html in browser (runs entirely client-side, uses API at localhost/api)

⸻

TECH STACK

Component	Use
FastAPI	Backend + routing
SQLAlchemy	Task + Ticket DB
OpenAI API	Prompt execution
Google Drive (planned)	SOP + document search
Pydantic	Validation
HTML/JS	Command Console UI


⸻

LLM LOGIC LAYERS

Each processed request can trigger any or all of these:
	1.	CapabilityFrontier: Should the LLM even handle this?
	2.	ClubOps: Is this procedural? Route to SOP.
	3.	SignalOS: Need strategic simulation?
	4.	Clubhost: Reformat output into house tone.
	5.	TicketEngine: Log output, trigger escalation if failure/conflict detected.

⸻

 COMMAND CENTER

In the frontend UI, available commands:

install           → Bay install protocol logic
rewrite           → Force tone layer
simulate          → Run strategy simulation
ad                → Brand-compliant promo gen
cleaner_sop       → Standard cleaning routine v2.0

Toggle flags: simulate, escalate, generate ticket, use LLM, Drive search.

⸻

 TO ADD NEXT
	•	 Google Drive vector index
	•	 Auth + role logic
	•	 Inline document preview on SOP search
	•	 Mobile-friendly dashboard
	•	Auto-escalation to email/sms

