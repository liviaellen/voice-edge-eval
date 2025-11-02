# Testing Guide

Quick guide to test the Emotion AI Platform

## Prerequisites

Before testing, you need:
- Hume AI API key from [hume.ai](https://hume.ai)
- (Optional) Omi credentials for Audio Edge testing

## Step 1: Setup Environment

```bash
cd /Users/liviaellen/Desktop/project/emotion_ai

# Copy environment template
cp .env.example .env

# Edit .env file
nano .env
```

Add your credentials:
```bash
# Required
HUME_API_KEY=your_actual_hume_api_key

# Optional (for Audio Edge)
OMI_APP_ID=your_omi_app_id
OMI_API_KEY=your_omi_api_key
```

## Step 2: Start the Platform

### Option A: Docker (Recommended)

```bash
# Start all services
docker-compose up -d

# Watch logs
docker-compose logs -f
```

### Option B: Local Development

**Terminal 1 - Backend:**
```bash
cd backend
pip install -r requirements.txt
python main.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm install
npm start
```

## Step 3: Verify Services

Check that everything is running:

```bash
# Backend health check
curl http://localhost:8080/health

# Expected response:
# {"status":"healthy","service":"emotion-ai-platform","version":"2.0.0"}

# Frontend (open in browser)
open http://localhost:3000
```

## Step 4: Test the APIs

### Test 1: Text Analytics (Easiest)

No audio file needed - just test with text:

```bash
curl -X POST "http://localhost:8080/audio-analytics/analyze-text?user_id=test_user" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "I am feeling really happy and excited today! This is amazing!"
  }'
```

**Expected Response:**
```json
{
  "status": "success",
  "user_id": "test_user",
  "emotion_analysis": {
    "success": true,
    "predictions": [
      {
        "emotions": [...],
        "top_3_emotions": [
          {"name": "Joy", "score": 0.85},
          {"name": "Excitement", "score": 0.72},
          ...
        ]
      }
    ]
  }
}
```

### Test 2: Audio Analytics with Sample Audio

First, create a sample audio file or download one:

```bash
# Option 1: Use existing audio file
# Make sure it's in WAV format, 16000Hz sample rate

# Option 2: Generate test audio with ffmpeg (if installed)
ffmpeg -f lavfi -i "sine=frequency=1000:duration=2" -ar 16000 test_audio.wav

# Test the endpoint
curl -X POST "http://localhost:8080/audio-analytics/analyze?sample_rate=16000&user_id=test_session" \
  -H "Content-Type: application/octet-stream" \
  --data-binary "@test_audio.wav"
```

**Expected Response:**
```json
{
  "status": "success",
  "analysis_id": "test_session_20241102_...",
  "user_id": "test_session",
  "audio_metadata": {
    "sample_rate": 16000,
    "data_size_bytes": 64000
  },
  "emotion_analysis": {
    "success": true,
    "total_predictions": 1
  },
  "analytics": {
    "rizz_score": 75.0,
    "rizz_status": "😐 Neutral Energy"
  }
}
```

### Test 3: Audio Edge (Omi Endpoint)

**Only if you have Omi credentials:**

```bash
curl -X POST "http://localhost:8080/audio-edge?sample_rate=16000&uid=test_user&send_notification=false" \
  -H "Content-Type: application/octet-stream" \
  --data-binary "@test_audio.wav"
```

### Test 4: Dashboard API

```bash
# Get statistics
curl http://localhost:8080/dashboard/stats

# Get emotion configuration
curl http://localhost:8080/dashboard/emotion-config
```

## Step 5: Test the Web Dashboard

1. **Open Dashboard**
   ```bash
   open http://localhost:3000
   ```

2. **Navigate Pages**
   - Dashboard: http://localhost:3000/
   - Analytics: http://localhost:3000/analytics
   - Configuration: http://localhost:3000/config

3. **Test Features**
   - ✅ View real-time statistics
   - ✅ Check Rizz Score meter
   - ✅ View emotion distribution
   - ✅ Configure emotion tracking
   - ✅ Reset statistics

## Step 6: Interactive API Testing

Open Swagger UI for interactive testing:

```bash
open http://localhost:8080/api/docs
```

**Try these endpoints:**
1. `/audio-analytics/analyze-text` - POST with JSON body
2. `/dashboard/stats` - GET current stats
3. `/dashboard/emotion-config` - GET/POST configuration

## Common Test Scenarios

### Scenario 1: Full Analytics Flow

```bash
# 1. Send text for analysis
curl -X POST "http://localhost:8080/audio-analytics/analyze-text?user_id=user1" \
  -H "Content-Type: application/json" \
  -d '{"text": "I love this! This is absolutely wonderful and exciting!"}'

# 2. Check stats
curl http://localhost:8080/dashboard/stats

# 3. View in dashboard
open http://localhost:3000
```

### Scenario 2: Multiple Requests

```bash
# Send multiple requests to see analytics build up
for i in {1..5}; do
  curl -X POST "http://localhost:8080/audio-analytics/analyze-text?user_id=user$i" \
    -H "Content-Type: application/json" \
    -d "{\"text\": \"Test message $i with different emotions\"}"
done

# Check updated stats
curl http://localhost:8080/dashboard/stats
```

### Scenario 3: Configuration Testing

```bash
# Update emotion config
curl -X POST "http://localhost:8080/dashboard/emotion-config" \
  -H "Content-Type: application/json" \
  -d '{
    "notification_enabled": true,
    "emotion_thresholds": {
      "Joy": 0,
      "Sadness": 0
    }
  }'

# Verify update
curl http://localhost:8080/dashboard/emotion-config
```

## Troubleshooting

### Issue: "HUME_API_KEY environment variable not set"

```bash
# Check if .env file exists
cat .env

# Verify environment variable is loaded
docker-compose exec backend python -c "import os; print(os.getenv('HUME_API_KEY'))"
```

**Fix:** Make sure `.env` file has `HUME_API_KEY=your_actual_key`

### Issue: "503 Hume AI not configured"

```bash
# Restart services after adding API key
docker-compose restart

# Or for local development, restart the backend
```

### Issue: Frontend can't connect to backend

```bash
# Check if backend is running
curl http://localhost:8080/health

# Check Docker logs
docker-compose logs backend

# Verify ports
lsof -i :8080  # Backend
lsof -i :3000  # Frontend
```

### Issue: Audio file fails to analyze

**Common causes:**
- Audio file is not in WAV format
- Sample rate doesn't match the query parameter
- Audio file is corrupted

**Fix:**
```bash
# Convert audio to correct format
ffmpeg -i your_audio.mp3 -ar 16000 -ac 1 -f wav output.wav

# Then test with correct sample rate
curl -X POST "http://localhost:8080/audio-analytics/analyze?sample_rate=16000&user_id=test" \
  --data-binary "@output.wav"
```

## Expected Behavior

### ✅ Successful Test Indicators

1. **Backend:**
   - Server starts on port 8080
   - Health check returns `{"status":"healthy"}`
   - API docs accessible at `/api/docs`
   - No errors in logs

2. **Frontend:**
   - Loads at http://localhost:3000
   - Dashboard shows "Online" status
   - Navigation works between pages
   - Can view statistics

3. **Text Analytics:**
   - Returns emotion predictions
   - Shows top 3 emotions
   - Updates dashboard statistics

4. **Audio Analytics:**
   - Accepts WAV files
   - Returns analysis results
   - Increments request counter

## Performance Testing

### Test Response Times

```bash
# Time a text analysis request
time curl -X POST "http://localhost:8080/audio-analytics/analyze-text?user_id=perf_test" \
  -H "Content-Type: application/json" \
  -d '{"text": "Testing performance"}'

# Expected: < 2 seconds
```

### Load Testing (Optional)

```bash
# Install apache bench
brew install apache-bench  # macOS
# or: sudo apt install apache2-utils  # Linux

# Run 100 requests
ab -n 100 -c 10 http://localhost:8080/health
```

## Clean Up After Testing

```bash
# Stop services
docker-compose down

# Remove volumes (optional - clears all data)
docker-compose down -v

# Or for local development
# Just Ctrl+C in the terminal windows
```

## Next Steps

After successful testing:
1. ✅ Configure emotion tracking in dashboard
2. ✅ Integrate with your application
3. ✅ Set up Omi device (for Audio Edge)
4. ✅ Configure GCS for audio archival (optional)

## Quick Reference

```bash
# Start
docker-compose up -d

# View logs
docker-compose logs -f backend

# Test health
curl http://localhost:8080/health

# Test text analysis
curl -X POST "http://localhost:8080/audio-analytics/analyze-text?user_id=test" \
  -H "Content-Type: application/json" \
  -d '{"text": "I am happy!"}'

# Open dashboard
open http://localhost:3000

# Stop
docker-compose down
```

## Need Help?

- Check logs: `docker-compose logs -f`
- API docs: http://localhost:8080/api/docs
- Verify .env file has correct API keys
- Ensure ports 3000 and 8080 are available
