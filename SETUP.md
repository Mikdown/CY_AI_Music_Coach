# 🎸 Guitar Coach AI - Complete Setup Guide

## Architecture Overview

This project consists of:
- **Backend**: FastAPI server with multi-agent orchestration (Python)
- **Frontend**: React SPA with Vite (TypeScript/React)

## Prerequisites

- Python 3.8+
- Node.js 16+ and npm
- GitHub Token (for OpenAI/GitHub Models API)
- Tavily API Key (for research tools) — optional for basic setup

## Backend Setup

### 1. Install Backend Dependencies

```bash
# Navigate to project root
cd /Users/miked/CY_AI_Music_Coach

# Install API dependencies
pip install -r api/requirements.txt
```

### 2. Environment Configuration

Create a `.env` file in the project root:

```env
GITHUB_TOKEN=your_github_token_here
TAVILY_API_KEY=your_tavily_api_key_here (optional)
```

**Get your tokens:**
- **GitHub Token**: [https://github.com/settings/tokens](https://github.com/settings/tokens) (create a Personal Access Token)
- **Tavily API Key**: [https://app.tavily.com/](https://app.tavily.com/) (optional, only needed for research features)

### 3. Verify Assets

Ensure these files exist in `assets/`:
- `scales.csv` — Guitar scales knowledge base
- `scale_types.csv` — Scale type definitions

Ensure these files exist in `templates/`:
- `assessor.json` — Assessment agent prompt
- `researcher.json` — Research agent prompt
- `writer.json` — Writer agent prompt
- `editor.json` — Editor agent prompt

### 4. Start Backend Server

```bash
# From project root
python -m uvicorn api.main:app --reload
```

✅ Backend will start at: **http://localhost:8000**

You should see:
```
Uvicorn running on http://127.0.0.1:8000
Press CTRL+C to quit
```

Verify it's working:
```bash
curl http://localhost:8000/health
# Should return: {"status":"healthy","message":"Guitar Coach API is running"}
```

## Frontend Setup

### 1. Install Frontend Dependencies

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install
```

### 2. Start Development Server

```bash
# From frontend directory
npm run dev
```

✅ Frontend will start at: **http://localhost:5173**

You should see:
```
  VITE v5.0.0  ready in XXX ms

  ➜  Local:   http://localhost:5173/
  ➜  press h to show help
```

## Running the Full Application

### Terminal 1: Start Backend

```bash
cd /Users/miked/CY_AI_Music_Coach
python -m uvicorn api.main:app --reload
```

### Terminal 2: Start Frontend

```bash
cd /Users/miked/CY_AI_Music_Coach/frontend
npm run dev
```

### Access the App

Open your browser and navigate to: **http://localhost:5173**

## Building for Production

### Frontend Build

```bash
cd frontend
npm run build
```

This generates a `dist/` folder with optimized static files.

### Serving Static Files from FastAPI (Optional)

To serve the React build from the FastAPI server:

1. Build frontend: `npm run build`
2. Copy `frontend/dist/` to a static folder in your API
3. Configure FastAPI to serve those files

## Architecture

```
┌─────────────────────────────────────────────────┐
│          React Frontend (5173)                  │
│  Assessment → Plan Display → Refinement Chat    │
└──────────────────┬──────────────────────────────┘
                   │ HTTP/JSON
┌──────────────────▼──────────────────────────────┐
│    FastAPI Backend (8000)                       │
│  • /api/initialize - Start session              │
│  • /api/assess - Submit 5 assessment answers    │
│  • /api/refine - Refine plan via chat           │
│  • /api/session/reset - Clear session           │
└──────────────────┬──────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────┐
│   LangChain Multi-Agent System                  │
│  (Assessor, Researcher, Writer, Editor agents) │
└──────────────────┬──────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────┐
│   OpenAI GPT-4o LLM                             │
│   + Vector Store (scales.csv knowledge base)    │
└─────────────────────────────────────────────────┘
```

## API Endpoints

### POST `/api/initialize`
Start a new session.

**Response:**
```json
{
  "session_id": "uuid-string",
  "phase": "assessment",
  "message": "Session initialized..."
}
```

### POST `/api/assess`
Submit assessment answers and generate practice plan.

**Request:**
```json
{
  "guitar_type": "Electric",
  "skill_level": "Intermediate",
  "genre": "Rock",
  "session_focus": "Technique & Warm-ups",
  "mood": "Energetic"
}
```

**Response:**
```json
{
  "session_id": "uuid-string",
  "phase": "plan",
  "plan": "Your 30-minute practice plan..."
}
```

### POST `/api/refine`
Refine the plan via chat.

**Request:**
```json
{
  "message": "Can you add more focus on finger dexterity?",
  "session_id": "uuid-string"
}
```

**Response:**
```json
{
  "session_id": "uuid-string",
  "phase": "refinement",
  "response": "Revised plan with more dexterity focus..."
}
```

### POST `/api/session/reset`
Clear a session.

**Query Param:** `session_id=uuid-string`

**Response:**
```json
{
  "session_id": "uuid-string",
  "message": "Session reset successfully",
  "phase": "assessment"
}
```

## Troubleshooting

### Backend won't start

**Error:** `ModuleNotFoundError: No module named 'langchain'`

**Solution:**
```bash
pip install -r api/requirements.txt
```

**Error:** `GITHUB_TOKEN not found in environment variables`

**Solution:**
1. Create `.env` file in project root
2. Add: `GITHUB_TOKEN=your_token_here`
3. Restart the server

### Frontend won't start

**Error:** `npm: command not found`

**Solution:** Install Node.js from [https://nodejs.org/](https://nodejs.org/)

**Error:** `EADDRINUSE: address already in use :::5173`

**Solution:** Either kill the process on port 5173 or change the port in `vite.config.ts`

### API calls fail with CORS errors

This is expected in development. The frontend is on port 5173 and backend on 8000, and the API client is configured to bypass CORS during development.

If you see CORS errors, make sure:
1. Backend is running on `http://localhost:8000`
2. Frontend has proxy configured in `vite.config.ts` (already done)

### "Failed to generate practice plan"

**Causes:**
- Backend not running
- Invalid GitHub Token
- API rate limits exceeded

**Solution:**
1. Check backend logs
2. Verify GITHUB_TOKEN is valid
3. Wait a few minutes before retrying

## Development Workflow

### Adding a New Feature

1. **Backend**: Add endpoint in `api/main.py`
2. **Frontend**: Add API call in `services/api.ts`
3. **Frontend**: Add component to interact with the API
4. **Test**: Use Postman or `curl` to test endpoint
5. **Integrate**: Connect component to state management in `App.tsx`

### File Structure

```
CY_AI_Music_Coach/
├── api/                          # Backend (FastAPI)
│   ├── main.py                   # API server and endpoints
│   ├── coaches.py                # Agent initialization and logic
│   ├── models.py                 # Pydantic request/response models
│   ├── requirements.txt           # Backend dependencies
│   └── __init__.py
│
├── frontend/                      # Frontend (React + Vite)
│   ├── src/
│   │   ├── components/           # React components
│   │   │   ├── AssessmentPhase.tsx
│   │   │   ├── PlanDisplay.tsx
│   │   │   └── RefinementChat.tsx
│   │   ├── services/             # API client
│   │   │   └── api.ts
│   │   ├── styles/               # Component styles
│   │   ├── App.tsx               # Main app component
│   │   └── main.tsx              # Entry point
│   ├── index.html
│   ├── package.json
│   ├── vite.config.ts
│   └── tsconfig.json
│
├── templates/                     # Agent prompts (JSON)
│   ├── assessor.json
│   ├── researcher.json
│   ├── writer.json
│   └── editor.json
│
├── assets/                        # Knowledge base
│   ├── scales.csv
│   └── scale_types.csv
│
├── new_coach_app.py              # Original multi-agent workflow (reference)
├── .env                          # Environment variables (not in git)
└── README.md                     # This file
```

## Next Steps (Future Enhancements)

- [ ] Add user authentication
- [ ] Persist sessions to database
- [ ] Add more sophisticated plan refinement
- [ ] Export plans to PDF/markdown
- [ ] Real-time plan modifications
- [ ] Mobile app version
- [ ] Dark mode toggle

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review backend logs at `http://localhost:8000/docs` (FastAPI docs)
3. Check browser console (F12) for frontend errors

## License

MIT
