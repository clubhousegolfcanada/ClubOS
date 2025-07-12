#!/usr/bin/env bash
set -e

# 1. Prune stale references in README.md
for module in unified_models.py version_manager.py monitoring.py webhooks.py; do
  grep -q "$module" README.md && sed -i "/$module/d" README.md
done

# Insert fresh Modules list (replace any existing under “## Modules”)
# Remove old Modules section if present
if grep -q "^## Modules" README.md; then
  # delete from Modules header to next empty line
  sed -i '/^## Modules/,$ {/^$/q;d}' README.md
fi
cat << 'EOF' >> README.md

## Modules
- `main.py`            – FastAPI app entrypoint  
- `engine.py`          – OperationalEngine core logic  
- `knowledge_base.py`  – equipment & emergency data  
- `database.py`        – SQLAlchemy models & session  
- `frontend/`          – static HTML/CSS/JS  
- `scripts/setup.sh`   – install & env-bootstrap script
EOF

# 2. Update setup.sh to use .env.example
sed -i 's|cp env.py .env|cp .env.example .env|g' scripts/setup.sh

# 3. Remove hard-coded env.py
if [ -f env.py ]; then
  git rm env.py
fi

# 4. Create .env.example
cat > .env.example << 'EOF'
# Copy this file to .env and fill in your secrets:

OPENAI_API_KEY=your_openai_key_here
DATABASE_URL=postgresql://user:password@localhost:5432/clubos
EOF

# 5. Ignore real .env
grep -q "^.env\$" .gitignore || echo ".env" >> .gitignore

# 6. Install and pin python-dotenv
pip install python-dotenv
grep -q "^python-dotenv" requirements.txt || echo "python-dotenv>=0.19.0" >> requirements.txt

# 7. Load dotenv in main.py
if ! grep -q "load_dotenv" main.py; then
  sed -i "1ifrom dotenv import load_dotenv\nload_dotenv()\n" main.py
fi

# 8. Commit all changes
git add README.md scripts/setup.sh .env.example .gitignore requirements.txt main.py
git commit -m "chore(env): phase 1 – docs aligned & dotenv wired"

echo "Phase 1 applied. Docs pruned, .env workflow in place, and dotenv loading configured."