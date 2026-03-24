# CY_AI_Music_Coach

An AI-powered guitar practice coaching application that helps musicians design and complete personalized 30-minute practice sessions using LangChain, OpenAI embeddings, and GitHub Models.

## Features

- 🎸 **AI Guitar Coach**: Conversational AI coach that adapts to your skill level and musical goals
- 📚 **Knowledge Base**: Vector store with comprehensive scale data for intelligent responses
- 💬 **Multi-turn Conversations**: Maintains context across multiple exchanges for natural dialogue
- 🌐 **Web Interface**: Professional Streamlit UI for easy access
- ⚡ **Semantic Search**: Uses OpenAI embeddings to find relevant scale information

## Architecture

### Coach App (coach_app.py)

The main CLI application that powers the AI coaching experience.

#### Key Components

**Initialization**
- **LLM Provider**: OpenAI GPT-4o via GitHub Models (`https://models.github.ai/inference`)
- **Embeddings**: OpenAI text-embedding-3-small for semantic understanding
- **Vector Store**: In-memory vectorstore for knowledge retrieval during conversations
- **Text Splitter**: RecursiveCharacterTextSplitter with 2000-character chunks and 50-character overlap for optimal processing

#### Core Functions

**`load_coach_prompt()`**
- Loads the Guitar Coach AI system prompt from `assets/coach_prompt.json`
- Falls back to a default prompt if file is not found
- Returns a string containing the system role and behavioral guidelines

**`get_default_coach_prompt()`**
- Provides a fallback system prompt
- Used when `coach_prompt.json` is unavailable
- Defines the coach as a warm, knowledgeable guitar instructor focused on 30-minute practice sessions

**`load_and_store_documents(vector_store, file_path)`**
- Loads scale data from CSV files into the vector store
- Reads CSV rows and converts them to Document objects
- Chunks documents into optimal sizes for semantic search
- Adds metadata including filename, creation timestamp, and source information

**`load_document_with_chunks(vector_store, file_path, chunks)`**
- Stores pre-chunked documents in the vector store
- Adds detailed metadata tracking for each chunk (index, filename, timestamp)
- Returns count of successfully stored chunks

**`main()`**
- Entry point for the CLI application
- Validates environment variables (GITHUB_TOKEN required)
- Initializes all components (LLM, embeddings, vector store)
- Loads knowledge base from `assets/scales.csv`
- Implements conversation loop with:
  - `SystemMessage`: Contains the coach prompt for consistent persona
  - `HumanMessage`: User queries
  - `AIMessage`: Coach responses
- Maintains full conversation history for context awareness
- Exits on commands: `exit`, `quit`, `bye`, `goodbye`

#### Conversation Flow

1. **Initialization**: Coach prompt loaded and system message established
2. **User Input**: Reads guitar practice question or topic
3. **Semantic Context**: Vector store can provide relevant scale information (when queried)
4. **LLM Processing**: OpenAI processes full conversation history for contextual response
5. **History Management**: Both user message and AI response added to conversation history
6. **Output**: Coach response displayed with emoji formatting

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
├── coach_app.py              # Main CLI application
├── streamlit_app.py          # Web UI interface
├── assets/
│   ├── scales.csv           # Guitar scale knowledge base
│   ├── coach_prompt.json    # AI coach system prompt
│   └── scrape_scales.py     # Web scraper for scale data
├── .env                      # Environment variables (API keys)
├── requirements.txt          # Python dependencies
└── README.md                # This file
```

## Required Dependencies

- `langchain`: LLM framework and vector store
- `langchain-openai`: OpenAI API integration
- `python-dotenv`: Environment variable management
- `pandas`: Data processing (CSV handling)
- `streamlit`: Web interface (for streamlit_app.py)

## Usage

### CLI Mode

```bash
# Activate virtual environment
source .venv/bin/activate

# Run the CLI coach
python coach_app.py
```

### Web Interface

```bash
# Run the Streamlit app
./run_streamlit.sh
# or
streamlit run streamlit_app.py
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

🎸 You: I'm a beginner and want to learn major scales
🎵 Coach: Great choice! Major scales are fundamental...
[Conversation continues with context preserved]
```