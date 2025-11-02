# Emotion AI Platform

> A comprehensive emotion analysis platform with dual APIs: Audio Edge for Omi devices and Audio Analytics for stream insights

## 🌟 Overview

The Emotion AI Platform is a refactored version of audio-sentiment-profiling, designed with a modern architecture and interactive dashboard for stream analytics.

### Key Features

- **Dual API Architecture**
  - **Audio Edge** (`/audio-edge`): Original functionality for Omi devices with notifications
  - **Audio Analytics** (`/audio-analytics`): Stream endpoint without notifications for pure analytics

- **Modern Tech Stack**
  - **Backend**: FastAPI with modular architecture
  - **Frontend**: React dashboard with real-time analytics
  - **AI**: Hume AI for emotion detection (speech prosody & language models)
  - **Deployment**: Docker Compose for easy deployment

- **Advanced Features**
  - Real-time emotion detection from audio and text
  - Automatic audio chunking for files >5 seconds
  - Rizz Score tracking (emotional health metric)
  - Emotion statistics and trends
  - Optional Google Cloud Storage integration
  - Background tasks for cleanup and memory creation

## 📁 Project Structure

```
emotion_ai/
├── backend/                    # FastAPI Backend
│   ├── api/                   # API route modules
│   │   ├── audio_edge.py     # Original /audio for Omi (with notifications)
│   │   ├── audio_analytics.py # Stream analytics (no notifications)
│   │   └── dashboard.py      # Dashboard & config endpoints
│   ├── core/                  # Core functionality
│   ├── models/                # Pydantic models
│   ├── services/              # Business logic
│   └── main.py               # FastAPI application
├── frontend/                  # React Dashboard
│   ├── src/pages/            # Dashboard, Analytics, Configuration
│   └── nginx.conf            # API reverse proxy
├── docker-compose.yml        # Multi-service deployment
└── .env.example             # Environment variables template
```

## 🚀 Quick Start

### Prerequisites

- **Docker & Docker Compose** (recommended) OR
- **Python 3.11+** and **Node.js 18+** (for local development)
- **Hume AI API key** - Get free key at [hume.ai](https://hume.ai)
- **Omi credentials** (optional, only for Audio Edge endpoint)

---

### Option 1: Docker Compose (Easiest - Recommended)

```bash
# 1. Navigate to project
cd emotion_ai

# 2. Create environment file
cp .env.example .env

# 3. Edit .env and add your Hume API key
nano .env  # or use any text editor
# Add: HUME_API_KEY=your_actual_api_key_here

# 4. Start all services (backend + frontend)
docker-compose up -d

# 5. View logs (optional)
docker-compose logs -f

# 6. Access the platform
# ✓ Frontend Dashboard: http://localhost:3000
# ✓ Backend API: http://localhost:8080
# ✓ API Docs: http://localhost:8080/api/docs
```

**Stop services:**
```bash
docker-compose down
```

---

### Option 2: Local Development (Backend + Frontend Separate)

#### Step 1: Setup Environment

```bash
cd emotion_ai

# Create .env file
cp .env.example .env

# Edit .env and add your credentials
nano .env
```

**Add to .env:**
```bash
# Required
HUME_API_KEY=your_actual_hume_api_key_here

# Optional (for Audio Edge)
OMI_APP_ID=your_omi_app_id
OMI_API_KEY=your_omi_api_key
```

#### Step 2: Run Backend

**Terminal 1:**
```bash
cd backend

# Install Python dependencies
pip install -r requirements.txt

# Start backend server
python main.py
```

**Expected output:**
```
🚀 Emotion AI Platform Starting...
   - Hume AI: ✓ Configured
   - GCS: ✗ Not configured
   - Omi: ✗ Not configured
✓ Emotion AI Platform Ready!
INFO:     Uvicorn running on http://0.0.0.0:8080
```

**Backend is now running at:** http://localhost:8080

#### Step 3: Run Frontend

**Terminal 2 (new terminal):**
```bash
cd frontend

# Install Node dependencies (first time only)
npm install

# Start development server
npm start
```

**Expected output:**
```
Compiled successfully!

You can now view emotion-ai-dashboard in the browser.

  Local:            http://localhost:3000
  On Your Network:  http://192.168.1.x:3000
```

**Frontend is now running at:** http://localhost:3000

---

### Verify Everything Works

**Test backend:**
```bash
curl http://localhost:8080/health
# Should return: {"status":"healthy","service":"emotion-ai-platform","version":"2.0.0"}
```

**Test emotion analysis:**
```bash
curl -X POST "http://localhost:8080/audio-analytics/analyze-text?user_id=test" \
  -H "Content-Type: application/json" \
  -d '{"text": "I am feeling amazing today!"}'
```

**Open dashboard:**
```bash
open http://localhost:3000
```

---

### Common Issues & Solutions

**Issue: "HUME_API_KEY environment variable not set"**
- Make sure `.env` file exists in the project root
- Verify `HUME_API_KEY` is set correctly
- Restart the backend server

**Issue: Backend won't start - Port 8080 already in use**
```bash
# Find what's using port 8080
lsof -i :8080

# Kill the process
kill -9 <PID>
```

**Issue: Frontend can't connect to backend**
- Make sure backend is running on port 8080
- Check `curl http://localhost:8080/health`
- Verify no CORS errors in browser console

**Issue: `pip install` fails**
```bash
# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Mac/Linux
# or: venv\Scripts\activate  # On Windows

# Then install dependencies
pip install -r requirements.txt
```

## 🔌 API Endpoints

### Audio Edge API (Omi Integration)

**Endpoint:** `POST /audio-edge`

The original `/audio` endpoint functionality, now at `/audio-edge`:
- Receives audio from Omi devices
- Analyzes emotions with Hume AI
- Sends notifications to Omi users based on emotion triggers
- Tracks analytics for the dashboard

**Example:**
```bash
curl -X POST "http://localhost:8080/audio-edge?sample_rate=16000&uid=user123" \
  -H "Content-Type: application/octet-stream" \
  --data-binary "@audio.wav"
```

### Audio Analytics API (Stream)

**1. Stream Analysis (Binary)**

`POST /audio-analytics/analyze`

Stream endpoint for raw audio data:
```bash
curl -X POST "http://localhost:8080/audio-analytics/analyze?sample_rate=16000&user_id=session_abc" \
  -H "Content-Type: application/octet-stream" \
  --data-binary "@audio.wav"
```

**2. File Upload** 🆕

`POST /audio-analytics/upload`

Upload audio files (WAV, MP3, M4A):
```bash
curl -X POST "http://localhost:8080/audio-analytics/upload?user_id=user123" \
  -F "file=@recording.wav"
```

**3. Real-Time WebSocket** 🆕

`WS /audio-analytics/stream`

Real-time audio streaming with live analysis:
```javascript
const ws = new WebSocket('ws://localhost:8080/audio-analytics/stream');

ws.onopen = () => {
  // Send metadata
  ws.send(JSON.stringify({
    type: 'metadata',
    user_id: 'user123',
    sample_rate: 16000
  }));

  // Stream audio chunks
  ws.send(audioChunkBuffer);

  // Request analysis
  ws.send(JSON.stringify({ type: 'analyze' }));
};
```

**4. Text Analytics**

`POST /audio-analytics/analyze-text`

Analyze emotion from text:
```bash
curl -X POST "http://localhost:8080/audio-analytics/analyze-text?user_id=session_abc" \
  -H "Content-Type: application/json" \
  -d '{"text": "I am feeling really happy and excited today!"}'
```

### Dashboard Endpoints

- `GET /dashboard/stats` - Get comprehensive statistics
- `GET /dashboard/config` - Get system configuration
- `GET /dashboard/emotion-config` - Get emotion notification settings
- `POST /dashboard/emotion-config` - Update emotion settings
- `POST /dashboard/stats/reset` - Reset all statistics
- `GET /health` - Health check

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# Required
HUME_API_KEY=your_hume_api_key_here

# Required for Audio Edge (Omi)
OMI_APP_ID=your_omi_app_id_here
OMI_API_KEY=your_omi_api_key_here

# Optional - GCS
GCS_BUCKET_NAME=your_bucket_name
GOOGLE_APPLICATION_CREDENTIALS_JSON=base64_encoded_json
```

### Emotion Notification Configuration

Edit `emotion_config.json` or use the web dashboard at http://localhost:3000/config

```json
{
  "notification_enabled": true,
  "emotion_thresholds": {
    "Anger": 0,
    "Sadness": 0
  }
}
```

**Note:** Empty `emotion_thresholds` {} means notify for ALL emotions.

## 📊 Dashboard Features

The modern React dashboard provides:

1. **Dashboard Overview** - Real-time statistics, configuration status, Rizz Score meter
2. **🎤 Live Analysis** 🆕 - Record audio or upload files for instant emotion analysis
   - Real-time audio recording from microphone
   - Drag & drop file upload
   - Beautiful emotion visualizations
   - Circular Rizz Score display
3. **Analytics Page** - Emotion distribution charts and statistics
4. **Configuration Page** - Emotion tracking settings

## 🔄 Migration from audio-sentiment-profiling

1. **Audio Edge endpoint** maintains backward compatibility
2. Update Omi device configuration to use `/audio-edge` instead of `/audio`
3. For stream analytics, use `/audio-analytics/analyze`

## 📝 API Documentation

Interactive API documentation:
- Swagger UI: http://localhost:8080/api/docs
- ReDoc: http://localhost:8080/api/redoc

## Common Commands

```bash
# Stop services
docker-compose down

# View logs
docker-compose logs -f backend

# Rebuild
docker-compose build
docker-compose up -d
```

## 📜 License

Same license as the original audio-sentiment-profiling project.

## 🙏 Acknowledgments

- Built on [audio-sentiment-profiling](../audio-sentiment-profiling)
- Powered by [Hume AI](https://hume.ai)
- Integrated with [Omi](https://omi.me)

---

**Developer:** Livia Ellen
**Version:** 2.0.0
