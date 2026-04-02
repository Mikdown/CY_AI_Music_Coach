# CY_AI_Music_Coach

An AI-powered guitar practice coaching application that helps musicians design and complete personalized 30-minute practice sessions using LangChain, OpenAI embeddings, and GitHub Models.

## Features

- 🎸 **AI Guitar Coach**: Conversational AI coach that adapts to your skill level and musical goals
- 📚 **Knowledge Base**: Vector store with comprehensive scale data for intelligent responses
- 💬 **Multi-turn Conversations**: Maintains context across multiple exchanges for natural dialogue
- 🌐 **Web Interface**: Professional Streamlit UI for easy access
- ⚡ **Semantic Search**: Uses OpenAI embeddings to find relevant scale information

## Architecture

### API Layer (api/coaches.py)

The backend API module that powers the AI coaching experience with FastAPI integration.

#### Key Components

**Initialization** (`initialize_agents_and_vector_store()`)
- **LLM Provider**: OpenAI GPT-4o via GitHub Models (`https://models.github.ai/inference`)
- **Embeddings**: OpenAI text-embedding-3-small for semantic understanding
- **Vector Store**: In-memory vectorstore for knowledge retrieval during conversations
- **Text Splitter**: RecursiveCharacterTextSplitter with 2000-character chunks and 50-character overlap
- **Tavily Integration**: MCP (Model Context Protocol) client for web research capabilities
- **YouTube Integration**: Custom YouTube search tool for video recommendations

#### Core Functions

**`initialize_agents_and_vector_store()`** (async)
- Validates required API keys (GITHUB_TOKEN, TAVILY_API_KEY)
- Initializes LLM with GitHub Models
- Sets up vector store with CSV scale data
- Loads PDF documents from assets directory
- Initializes Tavily MCP client for research capabilities
- Creates specialized agents: assessor, researcher, writer, editor
- Returns dictionary with all initialized components

**`generate_practice_plan()`** (async)
- Generates personalized 30-minute practice plans based on assessment answers
- Uses YouTube tool to find relevant learning videos
- Maintains session state for practice tracking
- Args: assessment answers (guitar type, skill level, genre, focus, mood)
- Returns: Formatted practice plan with video recommendations

**`refine_plan()`** (async)
- Refines practice plans based on user feedback
- Maintains conversation history for context
- Args: refinement request message, session ID
- Returns: Updated practice plan with specific time allocations

**`get_youtube_recommendations()`**
- Searches YouTube for relevant guitar learning content
- Filters results by skill level and genre
- Returns formatted video recommendations with links

**`create_youtube_tool()`**
- Wraps YouTube search functionality as a LangChain tool
- Enables agents to autonomously search for videos during plan generation

**`load_and_store_CSV()`**
- Loads guitar scale data from CSV files into vector store
- Chunks documents for optimal semantic search
- Supports multiple CSV files (scales.csv, scale_types.csv)

#### Configuration

**Environment Variables** (`.env`)
- `GITHUB_TOKEN`: Required for LLM and embeddings API access

**Knowledge Base**
- Primary data source: `assets/scales.csv`
- Contains guitar scale definitions, notes, and signatures
- Loaded during application startup

## File Structure

```
CY_AI_Music_Coach/
├── api/
│   ├── main.py               # FastAPI application server
│   ├── coaches.py            # Core coaching agents and functions
│   ├── models.py             # Pydantic data models
│   └── requirements.txt       # API dependencies
├── frontend/                 # Vite/React TypeScript frontend
│   ├── src/
│   │   ├── components/       # React components
│   │   ├── services/         # API client services
│   │   └── styles/           # Component styling
│   └── vite.config.ts        # Vite configuration
├── templates/                # Agent system prompts (JSON)
│   ├── assessor.json
│   ├── researcher.json
│   ├── writer.json
│   └── editor.json
├── assets/
│   ├── scales.csv            # Guitar scale knowledge base
│   ├── scale_types.csv       # Scale type definitions
│   └── scrape_scales.py      # Web scraper for scale data
├── start.sh                  # Main startup script (API + frontend)
├── run_streamlit.sh          # Legacy Streamlit interface launcher
├── .env                      # Environment variables (API keys)
├── requirements.txt          # Root Python dependencies
└── README.md                 # This file
```

## Required Dependencies

- `langchain`: LLM framework and vector store
- `langchain-openai`: OpenAI API integration
- `python-dotenv`: Environment variable management
- `pandas`: Data processing (CSV handling)
- `streamlit`: Web interface (for streamlit_app.py)

## Usage

### Quick Start

The easiest way to start the complete application (API server + frontend) is:

```bash
# Make sure you're in the project directory
cd /Users/miked/CY_AI_Music_Coach

# Run the startup script
./start.sh
```

This starts:
- **FastAPI server** on `http://localhost:8000` (API endpoints)
- **Frontend application** with Vite dev server
- All components with proper async initialization

### Manual Setup

**For API server only:**
```bash
# Activate virtual environment
source .venv/bin/activate

# Start FastAPI server
uvicorn api.main:app --reload
```

**For CLI testing:**
```bash
# Test PDF loading and component initialization
python test_pdf_loading.py
```

## How It Works

1. **Knowledge Loading**: Application starts by loading guitar scale data from CSV
2. **AI Coach Setup**: GPT-4o model initialized with coach persona
3. **User Interaction**: Accepts natural language questions about practice, technique, or scales
4. **Context Preservation**: Full conversation history maintained for coherent multi-turn dialogue
5. **Dynamic Response**: AI generates personalized coaching advice based on conversation context and knowledge base

## Example Interaction

```
🎸 Welcome to Guitar Coach AI! 🎸
Let's create your perfect 30-minute practice session.

🎸 You: Simply answer the 5 questions provided by the UI.
```