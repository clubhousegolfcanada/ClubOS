#!/bin/bash
# ClubOS System Testing Script
# Tests all major components and endpoints

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

API_BASE="http://localhost:8000"
FRONTEND_BASE="http://localhost:3000"

print_success() { echo -e "${GREEN}✅ $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }
print_info() { echo -e "${YELLOW}ℹ️  $1${NC}"; }
print_test() { echo -e "${BLUE}🧪 $1${NC}"; }

echo "🧪 ClubOS System Testing"
echo "========================"
echo ""

# Test 1: Check if backend is running
print_test "Testing backend health..."
if curl -s "$API_BASE/health" > /dev/null; then
    HEALTH_RESPONSE=$(curl -s "$API_BASE/health")
    print_success "Backend is responding"
    echo "   Response: $HEALTH_RESPONSE"
else
    print_error "Backend is not responding on $API_BASE"
    echo "   Make sure to start the backend first:"
    echo "   ./dev_start.sh  or  ./start_clubos.sh"
    exit 1
fi

echo ""

# Test 2: Database connectivity
print_test "Testing database connectivity..."
DB_TEST=$(curl -s "$API_BASE/health/deep" | grep -o '"database":"[^"]*"' | cut -d'"' -f4)
if [ "$DB_TEST" = "ok" ]; then
    print_success "Database connection OK"
else
    print_error "Database connection failed: $DB_TEST"
fi

echo ""

# Test 3: Equipment endpoint
print_test "Testing equipment endpoint..."
EQUIPMENT_RESPONSE=$(curl -s "$API_BASE/equipment")
EQUIPMENT_COUNT=$(echo "$EQUIPMENT_RESPONSE" | grep -o '"count":[0-9]*' | cut -d':' -f2)
if [ "$EQUIPMENT_COUNT" -gt 0 ]; then
    print_success "Equipment endpoint working ($EQUIPMENT_COUNT items)"
else
    print_error "Equipment endpoint failed or no equipment found"
fi

echo ""

# Test 4: Process task endpoint
print_test "Testing task processing..."
TASK_RESPONSE=$(curl -s -X POST "$API_BASE/process" \
    -H "Content-Type: application/json" \
    -d '{"task": "TrackMan in Bay 3 is not reading ball data correctly", "priority": "high"}')

if echo "$TASK_RESPONSE" | grep -q '"status":"success"'; then
    print_success "Task processing working"
    CONFIDENCE=$(echo "$TASK_RESPONSE" | grep -o '"confidence":[0-9.]*' | cut -d':' -f2)
    CATEGORY=$(echo "$TASK_RESPONSE" | grep -o '"category":"[^"]*"' | cut -d'"' -f4)
    echo "   Confidence: $CONFIDENCE"
    echo "   Category: $CATEGORY"
else
    print_error "Task processing failed"
    echo "   Response: $TASK_RESPONSE"
fi

echo ""

# Test 5: System status endpoint
print_test "Testing system status..."
STATUS_RESPONSE=$(curl -s "$API_BASE/system/status")
if echo "$STATUS_RESPONSE" | grep -q '"status":"operational"'; then
    print_success "System status endpoint working"
    
    # Extract metrics
    ACTIVE_INCIDENTS=$(echo "$STATUS_RESPONSE" | grep -o '"active_incidents":[0-9]*' | cut -d':' -f2)
    TOTAL_EQUIPMENT=$(echo "$STATUS_RESPONSE" | grep -o '"total_equipment":[0-9]*' | cut -d':' -f2)
    
    echo "   Total Equipment: $TOTAL_EQUIPMENT"
    echo "   Active Incidents: $ACTIVE_INCIDENTS"
else
    print_error "System status endpoint failed"
fi

echo ""

# Test 6: Frontend accessibility
print_test "Testing frontend accessibility..."
if curl -s "$FRONTEND_BASE" > /dev/null 2>&1; then
    print_success "Frontend is accessible at $FRONTEND_BASE"
elif curl -s "http://localhost" > /dev/null 2>&1; then
    print_success "Frontend is accessible at http://localhost (Nginx)"
    FRONTEND_BASE="http://localhost"
else
    print_error "Frontend is not accessible"
    echo "   Try: cd frontend && python3 -m http.server 3000"
fi

echo ""

# Test 7: Test ticket creation
print_test "Testing ticket creation..."
TICKET_REQUEST='{
    "task_result": {
        "task": "Test ticket for system validation",
        "recommendation": ["Verify system is working", "Complete testing"]
    },
    "form_data": {
        "category": "general",
        "priority": "low",
        "generate_ticket": true,
        "notify_enabled": false
    }
}'

TICKET_RESPONSE=$(curl -s -X POST "$API_BASE/tickets" \
    -H "Content-Type: application/json" \
    -d "$TICKET_REQUEST")

if echo "$TICKET_RESPONSE" | grep -q '"status":"success"'; then
    print_success "Ticket creation working"
    TICKET_ID=$(echo "$TICKET_RESPONSE" | grep -o '"id":"[^"]*"' | cut -d'"' -f4)
    echo "   Created ticket: $TICKET_ID"
else
    print_error "Ticket creation failed"
    echo "   Response: $TICKET_RESPONSE"
fi

echo ""

# Test 8: Get all tickets
print_test "Testing ticket retrieval..."
TICKETS_RESPONSE=$(curl -s "$API_BASE/tickets")
if echo "$TICKETS_RESPONSE" | grep -q '"tickets"'; then
    TICKET_COUNT=$(echo "$TICKETS_RESPONSE" | grep -o '"id":"TKT-[^"]*"' | wc -l)
    print_success "Ticket retrieval working ($TICKET_COUNT tickets)"
else
    print_error "Ticket retrieval failed"
fi

echo ""

# Test 9: Analytics endpoint
print_test "Testing analytics endpoint..."
ANALYTICS_RESPONSE=$(curl -s "$API_BASE/analytics/summary")
if echo "$ANALYTICS_RESPONSE" | grep -q '"summary"'; then
    print_success "Analytics endpoint working"
    TOTAL_INCIDENTS=$(echo "$ANALYTICS_RESPONSE" | grep -o '"total_incidents":[0-9]*' | cut -d':' -f2)
    echo "   Total Incidents: $TOTAL_INCIDENTS"
else
    print_error "Analytics endpoint failed"
fi

echo ""

# Test 10: Environment variables check
print_test "Checking environment configuration..."
ENV_ISSUES=0

if [ ! -f ".env" ]; then
    print_error "Missing .env file"
    ENV_ISSUES=$((ENV_ISSUES + 1))
else
    if grep -q "sk-your-openai-key-here" .env; then
        print_error "OpenAI API key not configured in .env"
        ENV_ISSUES=$((ENV_ISSUES + 1))
    fi
    
    if grep -q "your-email@gmail.com" .env; then
        print_error "Email credentials not configured in .env"
        ENV_ISSUES=$((ENV_ISSUES + 1))
    fi
fi

if [ $ENV_ISSUES -eq 0 ]; then
    print_success "Environment configuration looks good"
else
    print_error "$ENV_ISSUES environment configuration issues found"
fi

echo ""

# Test 11: File structure validation
print_test "Validating file structure..."
STRUCTURE_ISSUES=0

required_files=(
    "backend/main.py"
    "backend/engine_foundation.py"
    "backend/database.py"
    "backend/schemas.py"
    "backend/knowledge_base.py"
    "backend/health.py"
    "backend/bootstrap.py"
    "frontend/index.html"
    ".env"
)

for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        print_error "Missing required file: $file"
        STRUCTURE_ISSUES=$((STRUCTURE_ISSUES + 1))
    fi
done

if [ $STRUCTURE_ISSUES -eq 0 ]; then
    print_success "File structure validation passed"
else
    print_error "$STRUCTURE_ISSUES file structure issues found"
fi

echo ""

# Summary
echo "=================================="
echo "🎯 Test Summary"
echo "=================================="

TOTAL_TESTS=11
PASSED_TESTS=0

# Count successful tests (this is simplified - in reality you'd track each test)
if curl -s "$API_BASE/health" > /dev/null; then ((PASSED_TESTS++)); fi
if [ "$DB_TEST" = "ok" ]; then ((PASSED_TESTS++)); fi
if [ "$EQUIPMENT_COUNT" -gt 0 ]; then ((PASSED_TESTS++)); fi
if echo "$TASK_RESPONSE" | grep -q '"status":"success"'; then ((PASSED_TESTS++)); fi
if echo "$STATUS_RESPONSE" | grep -q '"status":"operational"'; then ((PASSED_TESTS++)); fi
if curl -s "$FRONTEND_BASE" > /dev/null 2>&1 || curl -s "http://localhost" > /dev/null 2>&1; then ((PASSED_TESTS++)); fi
if echo "$TICKET_RESPONSE" | grep -q '"status":"success"'; then ((PASSED_TESTS++)); fi
if echo "$TICKETS_RESPONSE" | grep -q '"tickets"'; then ((PASSED_TESTS++)); fi
if echo "$ANALYTICS_RESPONSE" | grep -q '"summary"'; then ((PASSED_TESTS++)); fi
if [ $ENV_ISSUES -eq 0 ]; then ((PASSED_TESTS++)); fi
if [ $STRUCTURE_ISSUES -eq 0 ]; then ((PASSED_TESTS++)); fi

echo "Tests Passed: $PASSED_TESTS/$TOTAL_TESTS"

if [ $PASSED_TESTS -eq $TOTAL_TESTS ]; then
    print_success "All tests passed! ClubOS is ready for use."
    echo ""
    echo "🚀 Quick Start Guide:"
    echo "1. Open $FRONTEND_BASE in your browser"
    echo "2. Navigate to 'TASK PROCESSOR' tab" 
    echo "3. Enter test task: 'Projector in Bay 2 showing black screen'"
    echo "4. Click 'PROCESS REQUEST'"
    echo "5. Check 'TICKET ENGINE' tab for generated tickets"
    echo ""
    echo "📧 To enable email notifications:"
    echo "1. Edit .env with your Gmail credentials"
    echo "2. Update contact info in backend/ticket_system.py"
    echo "3. Restart the system"
else
    print_error "Some tests failed. Please fix the issues above."
    echo ""
    echo "🔧 Common fixes:"
    echo "- Make sure backend is running: ./dev_start.sh"
    echo "- Check database is running: sudo systemctl status postgresql"
    echo "- Verify .env configuration: nano .env"
    echo "- Check logs: ./logs_clubos.sh"
fi

echo ""
echo "📋 For detailed logs and troubleshooting:"
echo "   Backend logs: ./logs_clubos.sh"
echo "   System status: curl $API_BASE/system/status | jq"
echo "   Health check: curl $API_BASE/health/deep | jq"
