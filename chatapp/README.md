# 💬 ChatApp — Full-Stack Real-Time Chat with Video Calling

A full-stack Django chat application built for your college project. Features real-time messaging via WebSockets, OTP email verification, file/image sharing, and peer-to-peer video/voice calling via PeerJS.

---

## ✨ Features

| Feature | Technology |
|---|---|
| User Registration & Login | Django Auth |
| Email OTP Verification | django.core.mail |
| Real-Time Text Chat | Django Channels (WebSockets) |
| Typing Indicators | WebSockets |
| Online/Offline Status | WebSockets |
| Image & File Sharing | Django FileField |
| Video & Voice Calls | PeerJS (WebRTC) |
| User Search | Django ORM |
| Profile with Avatar | Pillow |
| Polished Dark UI | Bootstrap 5 + Custom CSS |

---

## 🚀 Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Run migrations
```bash
python manage.py migrate
```

### 3. Create a superuser (optional, for admin)
```bash
python manage.py createsuperuser
```

### 4. Start the server
```bash
# Development
python manage.py runserver

# Production (ASGI with Daphne - required for WebSockets)
daphne -b 0.0.0.0 -p 8000 config.asgi:application
```

### 5. Open in browser
```
http://localhost:8000
```

---

## 📁 Project Structure

```
chatapp/
├── config/
│   ├── settings.py       # All settings
│   ├── urls.py           # Root URL routing
│   └── asgi.py           # ASGI config (WebSocket support)
├── accounts/
│   ├── models.py         # Custom User model with OTP
│   ├── views.py          # Auth views (register/login/OTP/profile)
│   ├── forms.py          # Crispy forms
│   └── urls.py
├── chat/
│   ├── models.py         # Room and Message models
│   ├── consumers.py      # WebSocket consumers (real-time logic)
│   ├── views.py          # Chat views (home/room/search/upload)
│   ├── routing.py        # WebSocket URL routing
│   └── urls.py
├── templates/
│   ├── base.html         # Base template with CSS variables
│   ├── accounts/         # Auth templates
│   └── chat/             # Chat templates (home, room, search)
├── static/               # CSS/JS/images
├── media/                # User uploads
├── requirements.txt
├── .env.example          # Copy to .env for production
└── run.sh                # Production start script
```

---

## ⚙️ Configuration

### Email (OTP)
In `config/settings.py`, the default uses `console` backend (OTP prints to terminal).

For real email via Gmail:
```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
```
Enable "App Passwords" in your Gmail account for `EMAIL_HOST_PASSWORD`.

### Redis (for production multi-server deployments)
Install: `pip install channels-redis redis`

In `settings.py`:
```python
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {'hosts': [('127.0.0.1', 6379)]},
    }
}
```

---

## 🎥 Video Calling

PeerJS handles WebRTC peer-to-peer video/voice calling. Each user's Django User ID is used as their PeerJS peer ID.

**How it works:**
1. User A clicks "Video Call" → gets camera/mic access → calls `peer.call(otherUserId, stream)`
2. PeerJS signals User B via its cloud server
3. User B sees the incoming call banner → clicks Answer
4. Both streams connect directly between browsers (P2P)

**For production**, run your own PeerJS server:
```bash
npm install -g peer
peerjs --port 9000
```
Then update the `new Peer(...)` call in `room.html` to point to your server.

---

## 🚢 Free Deployment (Render.com)

1. Push code to GitHub
2. Create a new **Web Service** on [render.com](https://render.com)
3. Set **Build Command**: `pip install -r requirements.txt`
4. Set **Start Command**: `daphne -b 0.0.0.0 -p $PORT config.asgi:application`
5. Add environment variables: `SECRET_KEY`, `DEBUG=False`, email settings
6. Add a free **PostgreSQL** database from Render dashboard
7. Update `DATABASES` in settings to use `dj-database-url`

---

## 🗓️ Development Roadmap (Suggested)

- **Week 1** ✅ Auth + OTP + Profile
- **Week 2** ✅ Text chat (WebSockets) + Typing indicators + Online status
- **Week 3** ✅ Image/file sharing + User search
- **Week 4** ✅ PeerJS video/voice calling
- **Bonus**: Group chats, message reactions, read receipts, push notifications

---

## 🔐 Security Checklist (Before Submission/Deployment)

- [ ] Change `SECRET_KEY` to a random 50+ char string
- [ ] Set `DEBUG = False`
- [ ] Move secrets to environment variables (never hardcode)
- [ ] Use HTTPS in production
- [ ] Set `ALLOWED_HOSTS` to your actual domain
