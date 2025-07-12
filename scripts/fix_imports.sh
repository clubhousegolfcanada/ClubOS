#!/bin/bash
# ClubOS Import Fixes Script
# Resolves import conflicts and missing dependencies

echo "🔧 Fixing ClubOS Import Issues..."
echo "================================"

# 1. Fix main.py imports
echo "📝 Fixing main.py imports..."

if [ -f "backend/main.py" ]; then
    # Remove conflicting engine import
    sed -i '/from engine import OperationalEngine/d' backend/main.py
    
    # Ensure correct imports are present
    if ! grep -q "from engine_foundation import OperationalEngine" backend/main.py; then
        sed -i '/from fastapi import/i from engine_foundation import OperationalEngine' backend/main.py
    fi
    
    echo "✅ Fixed main.py imports"
else
    echo "❌ backend/main.py not found"
fi

# 2. Create missing ticket_system.py if needed
echo "📝 Checking ticket_system.py..."

if [ ! -f "backend/ticket_system.py" ]; then
    echo "⚠️  Creating missing ticket_system.py..."
    
    cat > backend/ticket_system.py << 'EOF'
"""
ClubOS Ticket System - Simplified Version
Handles basic ticket creation and management
"""

import time
from datetime import datetime
from typing import Dict, List, Optional

# Simplified ticket data structure
class TicketData:
    def __init__(self, task_description: str, category: str = "general", priority: str = "medium"):
        self.id = f"TKT-{int(time.time())}"
        self.description = task_description
        self.category = category
        self.priority = priority
        self.created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.status = "active"

# Simplified ticket engine
class TicketEngine:
    def __init__(self):
        self.tickets = []
    
    def create_ticket(self, task_result: Dict, form_data: Optional[Dict] = None) -> Dict:
        """Create a simple ticket"""
        ticket = TicketData(
            task_description=task_result.get('task', 'No description'),
            category=form_data.get('category', 'general') if form_data else 'general',
            priority=form_data.get('priority', 'medium') if form_data else 'medium'
        )
        
        self.tickets.append(ticket)
        
        return {
            'id': ticket.id,
            'category': ticket.category,
            'priority': ticket.priority,
            'description': ticket.description,
            'created_at': ticket.created_at,
            'status': ticket.status
        }
    
    def get_all_tickets(self) -> List[Dict]:
        """Get all tickets"""
        return [
            {
                'id': t.id,
                'category': t.category,
                'priority': t.priority,
                'description': t.description,
                'created_at': t.created_at,
                'status': t.status
            } for t in self.tickets
        ]
    
    def toggle_ticket_status(self, ticket_id: str) -> bool:
        """Toggle ticket status"""
        for ticket in self.tickets:
            if ticket.id == ticket_id:
                ticket.status = 'inactive' if ticket.status == 'active' else 'active'
                return True
        return False
EOF

    echo "✅ Created simplified ticket_system.py"
else
    echo "✅ ticket_system.py exists"
fi

# 3. Fix database.py model imports
echo "📝 Checking database.py..."

if [ -f "backend/database.py" ]; then
    # Ensure Ticket model is included
    if ! grep -q "class Ticket" backend/database.py; then
        echo "⚠️  Adding Ticket model to database.py..."
        
        cat >> backend/database.py << 'EOF'

class Ticket(Base):
    """Basic Ticket model for database"""
    __tablename__ = "tickets"
    
    id = Column(String(20), primary_key=True)
    task_id = Column(String(50))
    category = Column(String(50))
    priority = Column(String(20))
    description = Column(Text)
    status = Column(String(20), default='active')
    created_at = Column(DateTime, default=datetime.utcnow)
EOF
        echo "✅ Added Ticket model to database.py"
    fi
else
    echo "❌ backend/database.py not found"
fi

# 4. Fix schemas.py
echo "📝 Checking schemas.py..."

if [ ! -f "backend/schemas.py" ]; then
    echo "⚠️  Creating missing schemas.py..."
    
    cat > backend/schemas.py << 'EOF'
"""
ClubOS Pydantic Schemas
Data validation and serialization models
"""

from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime

class TaskRequest(BaseModel):
    task: str
    priority: Optional[str] = "medium"
    location: Optional[str] = None

class TaskResult(BaseModel):
    status: str
    confidence: float
    recommendation: List[str]
    time_estimate: Optional[str] = "Unknown"
    contact_if_fails: Optional[str] = "Manager"

class FormData(BaseModel):
    category: str
    priority: Optional[str] = "medium"
    task_id: Optional[str] = ""
    notify_enabled: Optional[bool] = False
    generate_ticket: Optional[bool] = False
EOF

    echo "✅ Created schemas.py"
else
    echo "✅ schemas.py exists"
fi

# 5. Fix bootstrap.py
echo "📝 Checking bootstrap.py..."

if [ ! -f "backend/bootstrap.py" ]; then
    echo "⚠️  Creating missing bootstrap.py..."
    
    cat > backend/bootstrap.py << 'EOF'
"""
ClubOS Bootstrap
Environment validation and startup checks
"""

import os
import sys

def validate_env():
    """Validate required environment variables"""
    required = ["OPENAI_API_KEY", "DATABASE_URL"]
    missing = [var for var in required if not os.getenv(var)]
    
    if missing:
        print(f"⚠️  Missing environment variables: {', '.join(missing)}")
        print("Please check your .env file")
        # Don't exit in development mode
        return False
    
    return True
EOF

    echo "✅ Created bootstrap.py"
else
    echo "✅ bootstrap.py exists"
fi

# 6. Fix knowledge_base.py contact info
echo "📝 Updating knowledge_base.py..."

if [ -f "backend/knowledge_base.py" ]; then
    # Replace XXX-XXXX placeholders with example numbers
    sed -i 's/XXX-XXXX/555-0123/g' backend/knowledge_base.py
    echo "✅ Updated contact placeholders in knowledge_base.py"
else
    echo "❌ backend/knowledge_base.py not found"
fi

# 7. Add missing dependencies to requirements.txt
echo "📝 Checking requirements.txt..."

if [ -f "backend/requirements.txt" ]; then
    # Check for missing dependencies
    missing_deps=()
    
    if ! grep -q "python-dotenv" backend/requirements.txt; then
        missing_deps+=("python-dotenv==1.0.0")
    fi
    
    if ! grep -q "email-validator" backend/requirements.txt; then
        missing_deps+=("email-validator==2.1.0")
    fi
    
    if [ ${#missing_deps[@]} -gt 0 ]; then
        echo "⚠️  Adding missing dependencies..."
        for dep in "${missing_deps[@]}"; do
            echo "$dep" >> backend/requirements.txt
            echo "   Added: $dep"
        done
    fi
    
    echo "✅ Requirements.txt updated"
else
    echo "❌ backend/requirements.txt not found"
fi

# 8. Create __init__.py files
echo "📝 Creating Python package files..."

touch backend/__init__.py
echo "✅ Created backend/__init__.py"

# 9. Test imports
echo "📝 Testing imports..."

cd backend

# Test basic imports
python3 << 'EOF'
import sys
sys.path.insert(0, '.')

try:
    print("Testing imports...")
    
    # Test basic modules
    import database
    print("✅ database import OK")
    
    import schemas
    print("✅ schemas import OK")
    
    import knowledge_base
    print("✅ knowledge_base import OK")
    
    import bootstrap
    print("✅ bootstrap import OK")
    
    import engine_foundation
    print("✅ engine_foundation import OK")
    
    import ticket_system
    print("✅ ticket_system import OK")
    
    print("✅ All imports successful!")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)
EOF

cd ..

if [ $? -eq 0 ]; then
    echo "✅ Import tests passed"
else
    echo "❌ Import tests failed"
fi

echo ""
echo "🎉 Import fixes complete!"
echo "========================"
echo ""
echo "Next steps:"
echo "1. Run the setup script: ./scripts/setup_fixed.sh"
echo "2. Test the system: ./scripts/test_system.sh"
echo "3. Start development: ./dev_start.sh"
echo ""
echo "If you still have import issues:"
echo "- Check Python path: export PYTHONPATH=$PWD/backend:$PYTHONPATH"
echo "- Activate virtual environment: source venv/bin/activate"
echo "- Install dependencies: pip install -r backend/requirements.txt"
