import streamlit as st
import os
import json
from datetime import datetime
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
import csv

# Page configuration
st.set_page_config(
    page_title="🎸 Guitar Coach AI",
    page_icon="🎸",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional styling
st.markdown("""
    <style>
        /* Main app background */
        .main {
            background-color: #f8f9fa;
            color: #1a1a1a;
        }
        
        /* General text styling */
        body, .stApp {
            color: #1a1a1a;
        }
        
        /* Markdown text */
        .stMarkdown {
            color: #1a1a1a;
        }
        
        /* Lists and bullets */
        ul, ol, li {
            color: #1a1a1a !important;
        }
        
        /* Stmetric cards */
        .stMetric {
            background-color: white;
            border-radius: 10px;
            padding: 1rem;
        }
        
        /* Chat messages */
        .stChatMessage {
            background-color: #f0f2f6;
            border-radius: 10px;
            padding: 1rem;
            margin: 0.5rem 0;
        }
        
        /* User messages */
        .stChatMessage[class*="user"] {
            background-color: #e3f2fd;
        }
        
        /* Assistant messages */
        .stChatMessage[class*="assistant"] {
            background-color: #f3e5f5;
        }
        
        /* Text styling */
        .stChatMessage p {
            color: #1a1a1a;
        }
        
        /* List items styling */
        .stChatMessage ul,
        .stChatMessage ol,
        .stChatMessage li {
            color: #1a1a1a !important;
        }
        
        /* Links in chat */
        .stChatMessage a {
            color: #667eea;
            text-decoration: underline;
        }
        
        /* Header styling */
        .header-title {
            color: #667eea;
            text-align: center;
            font-size: 2.5rem;
            font-weight: bold;
            margin-bottom: 1rem;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
        }
        
        /* Info box */
        .info-box {
            background-color: #e3f2fd;
            border-left: 5px solid #667eea;
            padding: 1rem;
            border-radius: 5px;
            color: #1a1a1a;
            margin: 1rem 0;
        }
        
        /* Input styling */
        .stTextInput > div > div > input {
            color: #1a1a1a;
            background-color: white;
        }
        
        /* Button styling */
        .stButton > button {
            background-color: #667eea;
            color: white;
            border-radius: 5px;
            padding: 0.5rem 1rem;
        }
        
        /* Button styling */
        .stButton > button {
            background-color: #667eea;
            color: white;
            border-radius: 5px;
            padding: 0.5rem 1rem;
        }
        
        .stButton > button:hover {
            background-color: #764ba2;
        }
        
        /* Sidebar styling */
        [data-testid="stSidebar"] {
            background-color: #f8f9fa;
        }
        
        /* Sidebar text */
        [data-testid="stSidebar"] * {
            color: #1a1a1a !important;
        }
        
        /* Sidebar headings */
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3,
        [data-testid="stSidebar"] p {
            color: #1a1a1a !important;
        }
        
        /* Sidebar markdown */
        [data-testid="stSidebar"] .stMarkdown {
            color: #1a1a1a !important;
        }
        
        /* Sidebar divider */
        [data-testid="stSidebar"] hr {
            border-color: #667eea;
        }
    </style>
""", unsafe_allow_html=True)

# Load environment variables
load_dotenv()

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "llm" not in st.session_state:
    st.session_state.llm = None
if "coach_prompt" not in st.session_state:
    st.session_state.coach_prompt = None
if "initialized" not in st.session_state:
    st.session_state.initialized = False


def load_coach_prompt():
    """Load the Guitar Coach AI system prompt from coach_prompt.json."""
    try:
        assets_dir = os.path.join(os.path.dirname(__file__), "assets")
        prompt_file = os.path.join(assets_dir, "coach_prompt.json")
        
        if not os.path.exists(prompt_file):
            return get_default_coach_prompt()
        
        with open(prompt_file, 'r', encoding='utf-8') as f:
            prompt_data = json.load(f)
        
        system_prompt = prompt_data.get("system_role", "")
        return system_prompt if system_prompt else get_default_coach_prompt()
        
    except Exception:
        return get_default_coach_prompt()


def get_default_coach_prompt():
    """Return default coach prompt."""
    return (
        "You are Guitar Coach AI, a warm, knowledgeable guitar instructor who helps players "
        "design and complete focused 30-minute practice sessions. You adapt naturally to each user's "
        "level, style, and goals, while keeping language friendly, motivating, and conversational. "
        "Guide users through creating personalized practice plans with practical exercises, tips, and encouragement."
    )


def initialize_llm():
    """Initialize the LLM and load the coach prompt."""
    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        st.error("❌ Error: GITHUB_TOKEN not found in environment variables.")
        st.info("""
            📝 **Setup Instructions:**
            1. Create or update your .env file in the project root directory
            2. Add your GitHub token: `GITHUB_TOKEN=your_github_token_here`
            3. Get a token from: https://github.com/settings/tokens
        """)
        return False
    
    try:
        llm = ChatOpenAI(
            model="openai/gpt-4o",
            temperature=0,
            base_url="https://models.github.ai/inference",
            api_key=github_token
        )
        
        coach_prompt = load_coach_prompt()
        st.session_state.llm = llm
        st.session_state.coach_prompt = coach_prompt
        st.session_state.messages = [SystemMessage(content=coach_prompt)]
        st.session_state.initialized = True
        return True
        
    except Exception as e:
        st.error(f"❌ Error initializing LLM: {e}")
        return False


def load_and_store_documents(file_path):
    """Load documents from CSV file (for knowledge base)."""
    try:
        documents = []
        file_name = os.path.basename(file_path)
        
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                page_content = ", ".join([f"{k}: {v}" for k, v in row.items()])
                metadata = {
                    "fileName": file_name,
                    "createdAt": datetime.now().isoformat(),
                    "source": file_path
                }
                metadata.update(row)
                
                doc = Document(
                    page_content=page_content,
                    metadata=metadata
                )
                documents.append(doc)
        
        return documents if documents else []
        
    except FileNotFoundError:
        return []
    except Exception:
        return []


# Header
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.markdown('<div class="header-title">🎸 Guitar Coach AI</div>', unsafe_allow_html=True)

st.markdown('<div class="info-box">Your personalized AI guitar practice coach - Master your instrument with focused, tailored sessions!</div>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("## ⚙️ Settings")
    
    if st.button("🔄 Reset Conversation"):
        st.session_state.messages = [SystemMessage(content=st.session_state.coach_prompt)]
        st.rerun()
    
    st.markdown("---")
    st.markdown("## 📖 About")
    st.markdown("""
        **Guitar Coach AI** helps you create and complete personalized 30-minute guitar practice sessions.
        
        Just tell the coach:
        - Your skill level
        - Your musical style
        - Your practice goals
        
        Get a custom practice plan with timing, exercises, and tips!
    """)
    
    st.markdown("---")
    st.markdown("## 🎵 Features")
    st.markdown("""
        ✅ Personalized practice plans
        ✅ Technique guidance
        ✅ Genre-specific exercises
        ✅ Progress tracking
        ✅ Motivation & encouragement
    """)

# Main content
if not st.session_state.initialized:
    st.info("🔄 Initializing Guitar Coach AI...")
    if initialize_llm():
        st.success("✅ Guitar Coach AI is ready!")
        st.rerun()
    else:
        st.stop()

# Display chat messages
for message in st.session_state.messages[1:]:  # Skip system message
    if isinstance(message, HumanMessage):
        with st.chat_message("user", avatar="🎸"):
            st.write(message.content)
    else:
        with st.chat_message("assistant", avatar="🤖"):
            st.write(message.content)

# Show example prompts if no messages (first interaction only)
if len(st.session_state.messages) == 1:  # Only system message
    st.markdown("### 💡 **Try asking me:**")
    
    example_prompts = [
        "I don't know what to practice today, please help!",
        "I need some motivation to practice today.",
        "I'm a beginner looking to learn major scales.",
        "What's the best way to warm up before practice?",
        "Can you create a 30-minute practice plan for me?"
    ]
    
    cols = st.columns(2)
    for idx, prompt in enumerate(example_prompts):
        col = cols[idx % 2]
        with col:
            if st.button(f"📝 {prompt}", key=f"example_{idx}"):
                st.session_state.example_prompt = prompt
                st.rerun()

# Handle example prompt click
if "example_prompt" in st.session_state and st.session_state.example_prompt:
    user_input = st.session_state.example_prompt
    del st.session_state.example_prompt
else:
    user_input = None

# Chat input
chat_input = st.chat_input("Ask your Guitar Coach...", key="user_input")
if chat_input:
    user_input = chat_input

if user_input:
    # Add user message to display
    with st.chat_message("user", avatar="🎸"):
        st.write(user_input)
    
    # Add user message to history
    st.session_state.messages.append(HumanMessage(content=user_input))
    
    # Get AI response
    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner("🎵 Coach is thinking..."):
            try:
                response = st.session_state.llm.invoke(st.session_state.messages)
                st.write(response.content)
                
                # Add response to history
                st.session_state.messages.append(response)
                
            except Exception as e:
                st.error(f"❌ Error: {e}")

# Footer
st.markdown("---")
st.markdown("""
    <div style='text-align: center; color: gray; font-size: 0.9rem;'>
        🎸 Guitar Coach AI | Powered by LangChain & GitHub Models
    </div>
""", unsafe_allow_html=True)
