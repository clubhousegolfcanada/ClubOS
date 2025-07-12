# Email Notification Setup Guide

## 📧 Setting Up Email Notifications

### Option 1: Gmail Setup (Recommended)

1. **Enable 2-Factor Authentication** on your Gmail account
2. **Generate App Password**:
   - Go to Google Account settings
   - Security → 2-Step Verification → App passwords
   - Generate password for "ClubOS"
   - Copy the 16-character password

3. **Update .env file**:
```bash
# Email Configuration
EMAIL_USER=your-email@gmail.com
EMAIL_PASSWORD=your-16-char-app-password
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
FROM_EMAIL=clubos@yourclubhouse.com
```

### Option 2: Other Email Providers

**Outlook/Hotmail:**
```bash
SMTP_SERVER=smtp-mail.outlook.com
SMTP_PORT=587
```

**Yahoo:**
```bash
SMTP_SERVER=smtp.mail.yahoo.com
SMTP_PORT=587
```

### Option 3: SendGrid (Production Recommended)

1. **Sign up for SendGrid** (free tier: 100 emails/day)
2. **Get API Key** from SendGrid dashboard
3. **Add to requirements.txt**:
```
sendgrid==6.10.0
```

4. **Alternative notification service** (replace in ticket_system.py):
```python
import sendgrid
from sendgrid.helpers.mail import Mail

class SendGridNotificationService:
    def __init__(self):
        self.sg = sendgrid.SendGridAPIClient(api_key=os.getenv('SENDGRID_API_KEY'))
    
    def send_email(self, to_email: str, subject: str, content: str) -> bool:
        message = Mail(
            from_email=os.getenv('FROM_EMAIL', 'clubos@yourclubhouse.com'),
            to_emails=to_email,
            subject=subject,
            html_content=content
        )
        
        try:
            response = self.sg.send(message)
            return True
        except Exception as e:
            print(f"SendGrid email failed: {e}")
            return False
```

## 🗄️ Database Setup

1. **Add new Ticket table**:
```bash
# Run this to add the Ticket table to your existing database
python3 -c "
from database import Base, engine
from ticket_system import Ticket
Base.metadata.create_all(bind=engine)
print('Ticket table created successfully!')
"
```

2. **Verify table creation**:
```bash
# Connect to PostgreSQL and verify
sudo -u postgres psql clubos
\dt  # Should show 'tickets' table
\q
```

## 🔧 Quick Setup Steps

1. **Install dependencies**:
```bash
pip install email-validator
```

2. **Update contact information** in `ticket_system.py`:
```python
CONTACT_ASSIGNMENT = {
    'facilities': {
        'name': 'Nick Thompson',
        'phone': '281-555-0101',
        'email': 'nick@yourclubhouse.com'  # UPDATE THESE
    },
    'equipment': {
        'name': 'Jason Miller',
        'phone': '281-555-0102', 
        'email': 'jason@yourclubhouse.com'  # UPDATE THESE
    },
    # ... etc
}
```

3. **Test email configuration**:
```python
# Run this test script
from ticket_system import NotificationService

service = NotificationService()
test_result = service.send_email(
    "your-email@example.com", 
    "ClubOS Test", 
    "<h1>Email working!</h1>"
)
print(f"Email test result: {test_result}")
```

## 🚀 Testing the Complete System

1. **Start ClubOS**:
```bash
python main.py
```

2. **Open frontend**: http://localhost:8000

3. **Test ticket creation**:
   - Enter task: "TrackMan in Bay 3 not working"
   - Select Category: "EQUIPMENT" 
   - Select Priority: "HIGH"
   - Enable "GENERATE TICKET" and "SEND NOTIFICATION"
   - Click "PROCESS REQUEST"

4. **Verify results**:
   - Check console logs for ticket creation
   - Check email inbox for notification
   - Check "TICKET ENGINE" tab for new ticket
   - Try toggling ticket status

## 🎯 Expected Workflow

1. **Staff submits issue** → Task processed through layers
2. **Ticket auto-created** → Assigned based on category rules
3. **Email notification sent** → Contact receives formatted email
4. **Ticket tracked** → Visible in ClubOS dashboard
5. **Status managed** → Toggle active/inactive when resolved

## 🔍 Troubleshooting

**Email not sending?**
- Check .env file has correct credentials
- Verify Gmail app password (not regular password)
- Check console logs for error messages

**Ticket not creating?**
- Check database connection
- Verify Ticket table exists
- Check API endpoint responses in browser dev tools

**Frontend not updating?**
- Refresh browser cache (Ctrl+Shift+R)
- Check browser console for JavaScript errors
- Verify API endpoints are responding

## 📋 Contact Assignment Rules

| Category | Assigned To | Use For |
|----------|-------------|---------|
| FACILITIES | Nick | HVAC, electrical, building issues |
| EQUIPMENT | Jason | TrackMan, projectors, simulators |
| GENERAL | Manager | Staff questions, general issues |
| EMERGENCY | Mike | Power outages, safety issues |

The system automatically assigns tickets based on these rules and sends notifications to the appropriate contact!