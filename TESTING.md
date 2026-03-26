# Testing Guide for Guitar Coach AI

## Quick Integration Test

### Prerequisites
- ✅ Backend running at `http://localhost:8000`
- ✅ Frontend running at `http://localhost:5173`
- ✅ `.env` file configured with GITHUB_TOKEN and TAVILY_API_KEY
- ✅ Python dependencies installed
- ✅ Node dependencies installed

## Test Scenarios

### 1. Backend Health Check

```bash
curl http://localhost:8000/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "message": "Guitar Coach API is running"
}
```

---

### 2. Initialize Session

```bash
curl -X POST http://localhost:8000/api/initialize
```

**Expected Response:**
```json
{
  "session_id": "some-uuid",
  "phase": "assessment",
  "message": "Session initialized..."
}
```

Save the `session_id` for the next tests.

---

### 3. Submit Assessment Answers

```bash
curl -X POST http://localhost:8000/api/assess \
  -H "Content-Type: application/json" \
  -d '{
    "guitar_type": "Electric",
    "skill_level": "Intermediate",
    "genre": "Rock",
    "session_focus": "Technique & Warm-ups",
    "mood": "Energetic"
  }'
```

**Expected Response:**
```json
{
  "session_id": "some-uuid",
  "phase": "plan",
  "plan": "Your 30-minute practice plan with specific time allocations..."
}
```

**What's tested:**
- ✅ API request validation (Pydantic models work)
- ✅ LLM integration (OpenAI API call succeeds)
- ✅ Plan generation (coach agent responds)

---

### 4. Refine Plan via Chat

Using the session_id from step 3:

```bash
curl -X POST http://localhost:8000/api/refine \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Can you add more focus on finger dexterity techniques?",
    "session_id": "YOUR_SESSION_ID_HERE"
  }'
```

**Expected Response:**
```json
{
  "session_id": "YOUR_SESSION_ID_HERE",
  "phase": "refinement",
  "response": "Revised plan with enhanced dexterity focus..."
}
```

**What's tested:**
- ✅ Session state persistence
- ✅ Chat refinement logic
- ✅ Plan modification capability

---

### 5. Reset Session

```bash
curl -X POST "http://localhost:8000/api/session/reset?session_id=YOUR_SESSION_ID_HERE"
```

**Expected Response:**
```json
{
  "session_id": "YOUR_SESSION_ID_HERE",
  "message": "Session reset successfully",
  "phase": "assessment"
}
```

**What's tested:**
- ✅ Session cleanup
- ✅ State management

---

## Frontend Integration Test

### Manual Test Flow

1. Open **http://localhost:5173** in browser
2. You should see the first assessment question dropdown
3. **Select an option** for Question 1
   - ✅ Should auto-advance to Question 2 after 300ms
4. **Continue selecting options** for Questions 2-5
5. **On Question 5**, click **"Generate Plan →"**
   - ✅ Should show spinner while generating
   - ✅ Should display the 30-minute practice plan
6. **Click "Refine Plan"**
   - ✅ Should show chat interface
7. **Type a refinement request** and click "Send →"
   - ✅ Should display coaching response
8. **Click "Back to Plan"**
   - ✅ Should return to plan display
9. **Click "🔄 Start New Session"** (floating button)
   - ✅ Should reset to assessment phase

### Performance Checks

- ⏱️ Assessment form response time: **< 500ms**
- ⏱️ Plan generation: **5-15 seconds** (API call)
- ⏱️ Plan refinement: **3-10 seconds** (API call)
- 📱 Layout responsiveness: Test on mobile browser (dev tools)

---

## Error Scenarios

### Backend Error Tests

**Missing GITHUB_TOKEN:**
```bash
# Temporarily unset GITHUB_TOKEN and restart backend
unset GITHUB_TOKEN
python -m uvicorn api.main:app --reload
# Should fail with: ValueError: GITHUB_TOKEN not found
```

**Invalid Session ID:**
```bash
curl -X POST http://localhost:8000/api/refine \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Test",
    "session_id": "invalid-uuid"
  }'
# Should return: {"response": "Session not found..."}
```

### Frontend Error Tests

**Backend Offline:** 
- Stop backend server
- Refresh frontend
- ✅ Should show "Connection Error" banner with helpful message

**Invalid Assessment:**
- Leave a question unanswered and try to submit
- ✅ Should disable "Generate Plan" button

---

## Full End-to-End Test Checklist

- [ ] Backend server starts without errors
- [ ] Frontend server starts without errors
- [ ] Health check endpoint returns 200 OK
- [ ] Initialize session creates new session ID
- [ ] Submit assessment returns valid practice plan
- [ ] Practice plan contains 30-minute structure
- [ ] Refine chat accepts and responds to feedback
- [ ] Session state persists across requests
- [ ] Reset clears session data
- [ ] All UI transitions work smoothly
- [ ] No console errors in browser (F12 → Console)
- [ ] No server errors in terminal logs
- [ ] API responses have correct structure
- [ ] Loading states show spinners
- [ ] Error messages are user-friendly

---

## Debug/Logging

### Backend Logs

The FastAPI server prints request logs:
```
INFO:     127.0.0.1:58423 - "POST /api/assess HTTP/1.1" 200 OK
```

To enable more verbose logging, add to `api/main.py`:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Frontend Logs

Open browser DevTools (**F12**) → **Console** tab to see:
- API requests/responses
- Component lifecycle logs
- JavaScript errors

### Check API Documentation

FastAPI auto-generates interactive API docs:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## Performance Baseline

| Operation | Expected Time | Status |
|-----------|---------------|--------|
| Assessment form render | < 500ms | ✅ |
| Option selection + advance | < 300ms | ✅ |
| Generate plan (API) | 5-15s | ✅ |
| Refine plan (API) | 3-10s | ✅ |
| Session reset | < 100ms | ✅ |

---

## Next Steps After Testing

If all tests pass:
1. ✅ Commit code to Git
2. ✅ Deploy backend to cloud (Heroku, AWS, etc.)
3. ✅ Deploy frontend to static hosting (Vercel, Netlify, etc.)
4. ✅ Update frontend API_BASE_URL for production
5. ✅ Add authentication if needed

If tests fail:
1. Check error messages in terminal logs
2. Review console logs in browser (F12)
3. Check `.env` configuration
4. Verify API keys are valid
5. Ensure ports 8000 and 5173 are available
