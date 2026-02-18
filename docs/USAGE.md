# Usage Guide

Complete guide to using Closed Claw Assistant v3.0

---

## 🎯 Quick Start Commands

Once installed, interact with Closed Claw via **Telegram** or **local interface**.

### Check Status
```
You: status
Assistant: 🦞 Closed Claw v3.0 Online
          
          🧠 Brain: Sarvam-1 2B Ready
          🎤 Voice: Active
          📞 Calls: Monitoring
          📱 WhatsApp: Connected
          🔐 Security: L1-L4 Active
          
          Memory: 1.4GB / 4GB
          Uptime: 2h 34m
```

---

## 💬 Conversational Commands

### General Queries (L1 - No Auth Required)

**Ask anything:**
```
You: What time is it?
Assistant: It's 2:30 PM on Tuesday, February 18, 2026.

You: What's the weather?
Assistant: I can't access weather data (offline mode), but I can check if you have any weather notifications.

You: Tell me a joke
Assistant: Here's one: Why don't scientists trust atoms? Because they make up everything! 😄
```

**Code-switching (Hinglish/Manglish):**
```
You: Aaj kya plan hai?
Assistant: Aaj aapke calendar mein koi events nahi hain. Free din hai! 😊

You: Majha divas kasa hota?
Assistant: Tumcha divas changla asava, aaj kahi events nahi calendar madhe.
```

---

## 📞 Call Management

### Automatic Call Handling

By default, Closed Claw will:
1. Monitor for incoming calls
2. Wait 20 seconds for you to answer
3. If you don't answer, **automatically pickup**
4. Greet caller with voice
5. Take message or handle query
6. Send you summary via Telegram

### Manual Call Commands

**Check recent calls:**
```
You: Show my recent calls
Assistant: 📞 Recent Calls:
          
          +91-98765-43210 - Missed (2:30 PM)
          Mom - Answered (1:15 PM) - Duration: 5 min
          Unknown - Rejected (11:00 AM)
```

**Pickup call immediately:**
```
You: Pickup this call
Assistant: 🔐 L4 Authorization Required
          
          This will answer the current call immediately.
          
          [Confirm] [Cancel]

You: Confirm
Assistant: ✅ Answering call...
          
          [Call active - monitoring...]
```

**Reject call:**
```
You: Reject this call
Assistant: ❌ Call rejected.
```

### Call Summary Example

After assistant handles a call:
```
📞 Call Summary
From: +91-87654-32109 (Unknown)
Duration: 1 minute 23 seconds
Handled by: Closed Claw

📝 Conversation:
Assistant: "Hello, this is the user's assistant. They're currently busy. May I take a message?"
Caller: "Yes, this is about the delivery. The package arrived."
Assistant: "I'll let them know. Thank you for calling!"
Caller: "Okay, bye."

🎯 Action Items:
• Package has arrived (delivery notification)

[Mark complete] [Call back] [Dismiss]
```

---

## 📱 WhatsApp Integration

### Reading Messages (L2 - PIN Required)

**Read recent messages:**
```
You: Read my WhatsApp messages
Assistant: 🔐 Security Check
          
          This will read your WhatsApp messages.
          Permission Level: L2 (PIN Required)
          
          Please enter your PIN:

You: 1234
Assistant: ✅ PIN Verified
          
          📱 WhatsApp Messages (Last 5):
          
          1. From Mom (2:30 PM):
             "When are you coming home?"
          
          2. From Boss (2:15 PM):
             "Meeting moved to 4 PM"
          
          3. From Unknown (1:45 PM):
             "Call me back"
             [Marked as possible spam]
          
          4. From Wife (1:30 PM):
             "Don't forget milk"
          
          5. From Bank (12:00 PM):
             [FINANCIAL - REDACTED]
```

**Read specific contact:**
```
You: Read messages from Mom
Assistant: 🔐 PIN Required...
          
          📱 Messages from Mom:
          
          • "When are you coming home?" (2:30 PM)
          • "Dinner is ready" (3:15 PM)
          
          [Reply manually] [Mark read] [Back]
```

### Important Message Alerts

Closed Claw automatically forwards important messages:
```
🚨 Important WhatsApp Alert

From: Boss (Priority: High)
Time: 2:15 PM

"URGENT: Client meeting moved to 4 PM today. Need you to present the report."

[Acknowledge] [Set reminder] [Dismiss]
```

### WhatsApp Settings

**Configure monitoring:**
```
You: Configure WhatsApp settings
Assistant: 📱 WhatsApp Configuration:
          
          Current settings:
          • Monitor interval: 5 seconds
          • Important keywords: [urgent, important, emergency, asap]
          • Blocked contacts: None
          • Auto-mark read: Off
          
          What would you like to change?
          
          [Change keywords] [Add blocked contact] [Toggle auto-read]
```

---

## 📅 Calendar Management

### Reading Calendar (L1)

**Check today's schedule:**
```
You: What's my schedule today?
Assistant: 📅 Today's Schedule (Feb 18, 2026):
          
          10:00 AM - Team Standup
          12:30 PM - Lunch with Sarah
          2:00 PM - Dentist Appointment
          4:00 PM - Client Meeting (URGENT)
          6:30 PM - Gym
          
          [Add event] [Share] [Back]
```

**Check tomorrow:**
```
You: What do I have tomorrow?
Assistant: 📅 Tomorrow (Feb 19, 2026):
          
          9:00 AM - Flight to Mumbai
          3:00 PM - Conference Call
          7:00 PM - Dinner with clients
```

### Adding Events (L3 - Confirmation Required)

**Add event:**
```
You: Add meeting with John tomorrow at 3pm
Assistant: 📅 New Event:
          
          Title: Meeting with John
          Date: February 19, 2026
          Time: 3:00 PM - 4:00 PM
          Reminder: 15 minutes before
          
          Permission Level: L3 (Confirmation Required)
          
          [Confirm] [Edit] [Cancel]

You: Confirm
Assistant: ✅ Event added to calendar!
          
          Event ID: EVT-20260218-001
          
          [Add reminder] [Send invite] [Close]
```

**Quick add:**
```
You: Remind me to call Mom at 6pm
Assistant: 📅 Reminder set:
          
          "Call Mom"
          Today at 6:00 PM
          
          [Confirm] [Change time] [Cancel]
```

---

## 📧 SMS Management

### Reading SMS (L2 - PIN Required)

**Check recent SMS:**
```
You: Read my recent messages
Assistant: 🔐 PIN Required...
          
          📱 Recent SMS:
          
          1. From: OTP-Bank
             "Your OTP is 123456. Valid for 5 minutes."
             [FINANCIAL - Content hidden for security]
          
          2. From: Amazon
             "Your order #12345 has been shipped."
             Track: [link]
          
          3. From: Jio
             "Your recharge is due tomorrow."
          
          4. From: Swiggy
             "Your food is arriving in 5 minutes!"
```

**Search SMS:**
```
You: Find OTP messages
Assistant: 🔐 PIN Required...
          
          Found 3 OTP messages:
          
          • Bank OTP: ****** (expired)
          • Amazon OTP: ****** (expired)
          • Paytm OTP: [BLOCKED - Financial SMS]
```

---

## 📁 File Management

### Reading Files (L1)

**Read a file:**
```
You: Read my shopping list
Assistant: 📝 Shopping List:
          
          • Milk
          • Eggs
          • Bread
          • Butter
          • Fruits
          
          [Add item] [Remove item] [Share]
```

### Editing Files (L3 - Confirmation)

**Edit file:**
```
You: Add cheese to shopping list
Assistant: 📝 Edit File:
          
          File: shopping-list.txt
          
          Current content:
          • Milk
          • Eggs
          
          New content:
          • Milk
          • Eggs
          • Cheese
          
          Permission Level: L3 (Confirmation Required)
          
          [Confirm edit] [Cancel]

You: Confirm
Assistant: ✅ File updated successfully!
```

---

## 🔔 Notification Management

### Reading Notifications

**Check recent notifications:**
```
You: Show my notifications
Assistant: 📱 Recent Notifications:
          
          🔴 High Priority:
          • WhatsApp: Boss - "Urgent meeting"
          • Calendar: Meeting in 15 minutes
          
          🟡 Medium Priority:
          • Gmail: 3 new emails
          • Instagram: 5 new likes
          
          🟢 Low Priority:
          • Weather: Rain expected
          • News: Breaking news alert
```

**Clear notifications:**
```
You: Clear all notifications
Assistant: 🧹 Cleared 12 notifications.
          
          [Undo] [Settings]
```

---

## ⚙️ System Commands

### Assistant Control

**Sleep mode (save battery):**
```
You: Go to sleep
Assistant: 💤 Entering sleep mode...
          
          I'll wake up when you message me or a call comes in.
          
          [Wake up] [Settings]
```

**Wake up:**
```
You: Wake up
Assistant: ☀️ Good morning! I'm back online.
          
          While I was sleeping:
          • 3 missed calls
          • 12 WhatsApp messages
          • 1 calendar reminder
          
          [Show details]
```

**Restart:**
```
You: Restart yourself
Assistant: 🔄 Restarting...
          
          [5 seconds later]
          
          ✅ Restarted successfully!
          All systems operational.
```

### Status and Health

**Check system health:**
```
You: System health
Assistant: 🏥 System Health Report:
          
          🧠 AI Brain: Healthy (45ms avg response)
          🎤 Voice: Working
          📞 Call Handler: Active
          📱 WhatsApp: Connected
          💬 Telegram: Online
          
          💾 Memory: 1.4GB / 4GB (Healthy)
          🔋 Battery Impact: Low (2% / hour)
          ⏱️ Uptime: 12h 34m
          
          All systems green! ✅
```

---

## 🔐 Security Commands

### Permission Management

**Check current session:**
```
You: Check my auth status
Assistant: 🔐 Current Session:
          
          User: You
          Auth Level: L4 (Full Access)
          Session Expires: 14 minutes
          Last Activity: 2 minutes ago
          
          [Extend session] [Logout]
```

**Change PIN:**
```
You: Change my PIN
Assistant: 🔐 Change PIN:
          
          Current PIN: ****
          New PIN: [input]
          Confirm PIN: [input]
          
          [Confirm] [Cancel]
```

**View audit log:**
```
You: Show audit log
Assistant: 🔐 Audit Log (Last 10 actions):
          
          [2026-02-18 14:23:01] L2 AUTH_SUCCESS - WhatsApp read
          [2026-02-18 14:20:15] L1 QUERY - Status check
          [2026-02-18 14:15:33] L4 CALL_PICKUP - Answered +91-98765-43210
          [2026-02-18 14:10:22] L3 CALENDAR_ADD - Added meeting
          [2026-02-18 14:05:11] L2 SMS_READ - Read 5 messages
          [2026-02-18 13:58:45] L5 BLOCKED - Banking query detected
          [2026-02-18 13:55:02] L2 AUTH_FAILURE - Wrong PIN (1/3)
          [2026-02-18 13:50:00] L1 SYSTEM - Startup complete
          
          [View full log] [Export] [Clear]
```

---

## 🆘 Help Commands

### General Help

**Get help:**
```
You: help
Assistant: 🦞 Closed Claw Help:
          
          📞 Call Management:
          • "Show recent calls" - View call history
          • "Pickup this call" - Answer current call
          • "Reject this call" - Decline call
          
          📱 WhatsApp:
          • "Read WhatsApp" - Read recent messages
          • "Read messages from [name]" - Specific contact
          • "Configure WhatsApp" - Change settings
          
          📅 Calendar:
          • "What's my schedule?" - Today's events
          • "Add meeting at [time]" - Create event
          • "Remind me to [task]" - Set reminder
          
          📧 SMS:
          • "Read my messages" - Recent SMS
          • "Find OTP" - Search OTP messages
          
          📁 Files:
          • "Read [filename]" - View file
          • "Add [text] to [file]" - Edit file
          
          ⚙️ System:
          • "Status" - Check assistant status
          • "Go to sleep" - Sleep mode
          • "Restart" - Restart assistant
          
          🔐 Security:
          • "Change PIN" - Update PIN
          • "Show audit log" - View activity log
          
          Type 'help [topic]' for detailed help on specific feature.
```

**Feature-specific help:**
```
You: help calls
Assistant: 📞 Call Management Help:
          
          Automatic Handling:
          By default, I monitor incoming calls. If you don't
          answer within 20 seconds, I'll pickup and handle it.
          
          Manual Commands:
          • "Pickup this call" - Answer immediately
          • "Reject this call" - Decline call
          • "Show recent calls" - View history
          
          Voice Handling:
          When I pickup a call, I will:
          1. Greet the caller professionally
          2. Take their message
          3. Never share your confidential info
          4. Send you a summary
          
          Security Level: L4 (Requires confirmation)
```

---

## 💡 Tips and Tricks

### Voice Commands
You can speak to Closed Claw:
```
You: [Voice] "Call Mom"
Assistant: 📞 Calling Mom...
```

### Quick Actions
Use shortcuts for frequent tasks:
```
You: w
Assistant: 📱 WhatsApp messages: [quick summary]

You: c
Assistant: 📅 Calendar: [today's events]

You: s
Assistant: 🦞 Status: [quick status]
```

### Context Awareness
Closed Claw remembers context:
```
You: Remind me to call John
Assistant: ✅ Reminder set for "Call John"

You: When?
Assistant: You didn't specify a time. When should I remind you?

You: Tomorrow at 5pm
Assistant: ✅ Updated: Remind "Call John" tomorrow at 5:00 PM
```

### Code-Switching
Mix languages naturally:
```
You: Kal office jana hai kya?
Assistant: Haan, aapka calendar mein kal office meeting hai 10 baje.

You: Mala nantar call karaycha hota
Assistant: Okay, mein nantar call karayla remind karto.
```

---

## ⚠️ Important Notes

### What Closed Claw CANNOT Do

❌ **Banking/Payments**:
   - Cannot access banking apps
   - Cannot read financial SMS content
   - Cannot make UPI payments
   - Cannot check bank balance

❌ **Sending Messages**:
   - Cannot send WhatsApp messages (read-only)
   - Cannot send SMS without confirmation
   - Cannot post to social media

❌ **System Changes**:
   - Cannot change Android settings
   - Cannot install/uninstall apps
   - Cannot access root functions

### Privacy Guarantees

✅ **Local Processing**: All AI runs on your phone  
✅ **No Cloud Storage**: Your data never leaves device  
✅ **E2E Encryption**: Telegram messages encrypted  
✅ **Audit Trail**: Every action logged for transparency  
✅ **Permission Control**: You control what assistant can do  

---

## 🎓 Advanced Usage

### Custom Commands

Add your own commands in `config/custom_commands.json`:
```json
{
  "commands": {
    "good morning": {
      "action": "sequence",
      "steps": [
        "read calendar",
        "read whatsapp",
        "speak greeting"
      ]
    }
  }
}
```

### Automation Rules

Create if-this-then-that rules:
```
You: Create rule
Assistant: Create automation rule:
          
          Trigger: When [call missed]
          Action: [Send SMS "Will call back"]
          
          [Save] [Test] [Cancel]
```

### Integration with Other Apps

Closed Claw can work with:
- Tasker (Android automation)
- Automate (Flow-based automation)
- IFTTT (Web services)
- Home Assistant (Smart home)

---

## 📞 Support

Need help? Contact us:
- 📧 Email: support@closed-claw.local
- 💬 Telegram: @ClosedClawAssistant
- 🐛 GitHub Issues: [Report Bug](https://github.com/AdityaPagare619/closed-claw-assistant/issues)

---

**Enjoy your personal AI assistant!** 🦞✨
