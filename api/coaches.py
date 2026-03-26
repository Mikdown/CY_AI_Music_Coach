"""Extracted and refactored agent wrapper functions from new_coach_app.py"""

import os
import sys
import json
from datetime import datetime
from typing import List, Dict
import asyncio
from dotenv import load_dotenv

from langchain.agents import create_agent
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.tools import tool

# Import YouTube search API
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'assets'))
from youtube_search_API import (
    initialize_youtube_client,
    search_by_assessment_answers,
    format_search_results
)

# Global session storage (in-memory; replace with database for production)
sessions: Dict[str, Dict] = {}


def load_and_store_CSV(vector_store, file_path):
    """Load documents from a CSV file and store them in the vector store."""
    import csv
    
    try:
        documents = []
        file_name = os.path.basename(file_path)
        
        # Initialize text splitter
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=2000,
            chunk_overlap=50,
            separators=["\n\n", "\n", " ", ""]
        )
        
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
        
        if documents:
            split_docs = text_splitter.split_documents(documents)
            vector_store.add_documents(split_docs)
            print(f"✅ Loaded {len(documents)} documents from {file_name}")
        
    except FileNotFoundError:
        print(f"❌ File not found: {file_path}")
    except Exception as e:
        print(f"❌ Error loading {file_path}: {e}")


def create_retrieval_tool(vector_store):
    """Create a retrieval tool from the vector store for the researcher agent."""
    @tool
    def search_music_knowledge_base(query: str) -> str:
        """
        Search the music knowledge base for scale and music theory information.
        
        Args:
            query: The search query about music scales or theory
            
        Returns:
            Relevant documents from the music knowledge base
        """
        try:
            results = vector_store.similarity_search(query, k=5)
            
            if not results:
                return "No relevant documents found in the music knowledge base."
            
            formatted_results = []
            for i, doc in enumerate(results, 1):
                formatted_results.append(f"\n--- Document {i} ---")
                formatted_results.append(f"Content: {doc.page_content}")
                if doc.metadata:
                    formatted_results.append(f"Source: {doc.metadata.get('fileName', 'Unknown')}")
            
            return "\n".join(formatted_results)
        except Exception as e:
            return f"Error searching knowledge base: {str(e)}"
    
    return search_music_knowledge_base


def initialize_agents_and_vector_store():
    """
    Initialize LLM, vector store, and all agents.
    Returns a dictionary with all initialized components.
    """
    load_dotenv()
    
    # Check for required API keys
    if not os.getenv("GITHUB_TOKEN"):
        raise ValueError("GITHUB_TOKEN not found in environment variables")
    
    if not os.getenv("TAVILY_API_KEY"):
        raise ValueError("TAVILY_API_KEY not found in environment variables")
    
    # Initialize LLM
    llm = ChatOpenAI(
        model="openai/gpt-4o",
        temperature=0.7,
        base_url="https://models.github.ai/inference",
        api_key=os.getenv("GITHUB_TOKEN")
    )
    
    # Load prompts from JSON templates
    templates = {}
    template_files = ["assessor.json", "researcher.json", "writer.json", "editor.json"]
    
    for template_file in template_files:
        template_path = os.path.join("templates", template_file)
        try:
            with open(template_path, "r") as f:
                data = json.load(f)
                templates[template_file.replace(".json", "")] = data.get("template", "You are a helpful assistant.")
        except FileNotFoundError:
            print(f"⚠️  Template not found: {template_path}")
            templates[template_file.replace(".json", "")] = "You are a helpful assistant."
    
    # Initialize vector store
    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-small",
        api_key=os.getenv("GITHUB_TOKEN"),
        base_url="https://models.github.ai/inference"
    )
    vector_store = InMemoryVectorStore(embedding=embeddings)
    
    # Load CSV knowledge base
    load_and_store_CSV(vector_store, "assets/scales.csv")
    load_and_store_CSV(vector_store, "assets/scale_types.csv")
    
    # Create agents
    assessor_agent = create_agent(
        llm,
        tools=[],
        system_prompt=templates.get("assessor", "You are a helpful assistant.")
    )
    
    researcher_agent = create_agent(
        llm,
        tools=[],  # Tools will be added dynamically
        system_prompt=templates.get("researcher", "You are a helpful assistant.")
    )
    
    writer_agent = create_agent(
        llm,
        tools=[],
        system_prompt=templates.get("writer", "You are a helpful assistant.")
    )
    
    editor_agent = create_agent(
        llm,
        tools=[],
        system_prompt=templates.get("editor", "You are a helpful assistant.")
    )
    
    return {
        "llm": llm,
        "vector_store": vector_store,
        "assessor_agent": assessor_agent,
        "researcher_agent": researcher_agent,
        "writer_agent": writer_agent,
        "editor_agent": editor_agent,
        "retrieval_tool": create_retrieval_tool(vector_store)
    }


async def generate_practice_plan(
    assessment_answers: Dict[str, str],
    session_id: str,
    components: Dict
) -> str:
    """
    Generate a 30-minute practice plan based on assessment answers.
    
    Args:
        assessment_answers: Dict with keys: guitar_type, skill_level, genre, session_focus, mood
        session_id: Unique session identifier
        components: Dict containing llm, agents, and vector store
        
    Returns:
        Generated practice plan as a string
    """
    llm = components["llm"]
    coach_template_path = "templates/coach.json"
    
    try:
        with open(coach_template_path, "r") as f:
            coach_data = json.load(f)
            coach_prompt = coach_data.get("template", "You are a helpful guitar coach.")
    except FileNotFoundError:
        coach_prompt = "You are a helpful guitar coach. Create a 30-minute practice plan with specific time allocations."
    
    # Format assessment summary
    assessment_summary = f"""Assessment Results:
- Guitar Type: {assessment_answers.get('guitar_type', 'Not specified')}
- Skill Level: {assessment_answers.get('skill_level', 'Not specified')}
- Genre: {assessment_answers.get('genre', 'Not specified')}
- Session Focus: {assessment_answers.get('session_focus', 'Not specified')}
- Mood: {assessment_answers.get('mood', 'Not specified')}

Based on these answers, create a personalized 30-minute guitar practice plan."""
    
    # Create coach instance with plan-generation purpose
    coach_agent = create_agent(
        llm,
        tools=[],
        system_prompt=coach_prompt
    )
    
    # Invoke the agent to generate the plan
    message = HumanMessage(content=assessment_summary)
    response = await coach_agent.ainvoke({"messages": [message]})
    
    # Extract the generated plan from the response
    plan = response["messages"][-1].content if response["messages"] else "Failed to generate plan"
    
    # Store in session
    sessions[session_id] = {
        "assessment_answers": assessment_answers,
        "generated_plan": plan,
        "conversation_history": [
            {"role": "user", "content": assessment_summary},
            {"role": "assistant", "content": plan}
        ]
    }
    
    return plan


async def refine_plan(
    message: str,
    session_id: str,
    components: Dict
) -> Dict[str, str]:
    """
    Refine the practice plan based on user feedback via chat.
    
    Args:
        message: User's refinement request
        session_id: Unique session identifier
        components: Dict containing llm and agents
        
    Returns:
        Dict with "response" and optionally "updated_plan"
    """
    if session_id not in sessions:
        return {"response": "Session not found. Please start a new assessment."}
    
    llm = components["llm"]
    session = sessions[session_id]
    current_plan = session.get("generated_plan", "")
    conversation_history = session.get("conversation_history", [])
    
    # Build messages for refinement
    messages = []
    for msg in conversation_history:
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["content"]))
        else:
            messages.append(AIMessage(content=msg["content"]))
    
    # Add the refinement request
    messages.append(HumanMessage(content=f"Original plan:\n{current_plan}\n\nUser refinement request: {message}"))
    
    # Create a refiner agent
    refiner_prompt = """You are a helpful guitar practice plan refiner. 
    The user has asked you to modify their 30-minute practice plan.
    Provide the refined plan with specific time allocations (must sum to 30 minutes).
    Be concise and practical."""
    
    refiner_agent = create_agent(
        llm,
        tools=[],
        system_prompt=refiner_prompt
    )
    
    # Invoke the refiner agent
    response = await refiner_agent.ainvoke({"messages": messages})
    refined_plan = response["messages"][-1].content if response["messages"] else "Failed to refine plan"
    
    # Update session
    session["generated_plan"] = refined_plan
    session["conversation_history"].append(
        {"role": "user", "content": message}
    )
    session["conversation_history"].append(
        {"role": "assistant", "content": refined_plan}
    )
    
    return {
        "response": refined_plan,
        "updated_plan": refined_plan
    }


def reset_session(session_id: str) -> bool:
    """Reset/clear a session."""
    if session_id in sessions:
        del sessions[session_id]
        return True
    return False


def get_youtube_recommendations(
    assessment_answers: Dict[str, str],
    youtube_client = None
) -> Dict[str, any]:
    """
    Get YouTube video recommendations based on the 5 assessment answers.
    
    Args:
        assessment_answers: Dict with keys:
            - guitar_type: Type of guitar (e.g., "acoustic", "electric")
            - skill_level: Skill level (e.g., "beginner", "intermediate", "advanced")
            - genre: Music genre (e.g., "blues", "rock", "jazz")
            - session_focus: Session focus area (e.g., "finger dexterity", "chord transitions")
            - mood: Mood preference (e.g., "energetic", "relaxed", "focused")
        youtube_client: YouTube API client (optional, will be initialized if not provided)
        
    Returns:
        Dict with two keys:
            - "success": Boolean indicating if videos were found
            - "videos": Formatted string with video links grouped by assessment category
            - "raw_results": Raw video data organized by assessment key (if available)
    """
    # Initialize YouTube client if not provided
    if youtube_client is None:
        youtube_client = initialize_youtube_client()
    
    if not youtube_client:
        return {
            "success": False,
            "videos": "YouTube API not configured. Please set YOUTUBE_API_KEY in your environment.",
            "raw_results": {}
        }
    
    try:
        # Search for videos based on assessment answers
        search_results = search_by_assessment_answers(
            assessment_answers=assessment_answers,
            youtube_client=youtube_client,
            videos_per_topic=3
        )
        
        # Check if any videos were found
        has_videos = any(len(videos) > 0 for videos in search_results.values())
        
        if not has_videos:
            return {
                "success": False,
                "videos": "No YouTube videos found for your assessment. Try searching manually on YouTube.",
                "raw_results": search_results
            }
        
        # Format results for display
        formatted_videos = format_search_results(search_results)
        
        return {
            "success": True,
            "videos": formatted_videos,
            "raw_results": search_results
        }
        
    except Exception as e:
        return {
            "success": False,
            "videos": f"Error fetching YouTube videos: {str(e)}",
            "raw_results": {}
        }

