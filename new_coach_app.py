import os
import asyncio
import json
from datetime import datetime
from typing import TypedDict, Annotated, Literal
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, START
from langgraph.graph.message import add_messages
from langgraph.types import Command
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.tools import tool

# 1. Define shared state
class State(TypedDict):
    messages: Annotated[list, add_messages]

# Global variable for the researcher agent (will be set in main)
researcher_agent = None
writer_agent = None
editor_agent = None

def load_and_store_CSV(vector_store, file_path):
    """
    Load documents from a CSV file and store them in the vector store.
    
    Args:
        vector_store: The InMemoryVectorStore instance
        file_path: Path to the CSV file
    """
    import csv
    
    try:
        documents = []
        file_name = os.path.basename(file_path)
        
        # Initialize text splitter for chunking content
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=2000,
            chunk_overlap=50,
            separators=["\n\n", "\n", " ", ""]
        )
        
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Create document content from the row
                page_content = ", ".join([f"{k}: {v}" for k, v in row.items()])
                
                # Create metadata
                metadata = {
                    "fileName": file_name,
                    "createdAt": datetime.now().isoformat(),
                    "source": file_path
                }
                # Add CSV columns as metadata
                metadata.update(row)
                
                # Create document
                doc = Document(
                    page_content=page_content,
                    metadata=metadata
                )
                documents.append(doc)
        
        if documents:
            # Split documents into chunks
            split_docs = text_splitter.split_documents(documents)
            vector_store.add_documents(split_docs)
            print(f"✅ Loaded {len(documents)} documents ({len(split_docs)} chunks) from {file_name}")
        
    except FileNotFoundError:
        print(f"❌ File not found: {file_path}")
    except Exception as e:
        print(f"❌ Error loading {file_path}: {e}")

def load_and_store_PDF(vector_store, file_path):
    """
    Load documents from a PDF file and store them in the vector store.
    
    Args:
        vector_store: The InMemoryVectorStore instance
        file_path: Path to the PDF file
    """
    try:
        documents = []
        file_name = os.path.basename(file_path)
        
        # Initialize text splitter for chunking content
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=2000,
            chunk_overlap=50,
            separators=["\n\n", "\n", " ", ""]
        )
        
        # Load PDF using PyPDFLoader
        loader = PyPDFLoader(file_path)
        pages = loader.load()
        
        # Process each page
        for page_num, page in enumerate(pages):
            # Create metadata
            metadata = {
                "fileName": file_name,
                "pageNumber": page_num + 1,
                "createdAt": datetime.now().isoformat(),
                "source": file_path
            }
            
            # Add page metadata from the loader
            if hasattr(page, 'metadata'):
                metadata.update(page.metadata)
            
            # Create document with page content
            doc = Document(
                page_content=page.page_content,
                metadata=metadata
            )
            documents.append(doc)
        
        if documents:
            # Split documents into chunks
            split_docs = text_splitter.split_documents(documents)
            vector_store.add_documents(split_docs)
            print(f"✅ Loaded {len(documents)} pages ({len(split_docs)} chunks) from {file_name}")
        
    except FileNotFoundError:
        print(f"❌ File not found: {file_path}")
    except Exception as e:
        print(f"❌ Error loading {file_path}: {e}")

def create_retrieval_tool(vector_store):
    """
    Create a retrieval tool from the vector store for the researcher agent to query.
    
    Args:
        vector_store: The InMemoryVectorStore instance
        
    Returns:
        A tool function that can be used by the agent
    """
    @tool
    def search_music_knowledge_base(query: str) -> str:
        """
        Search the music knowledge base (scales and music theory documents) for information.
        Use this tool to find information about scales, scale types, and other music theory concepts.
        
        Args:
            query: The search query about music scales or theory
            
        Returns:
            Relevant documents from the music knowledge base
        """
        try:
            # Search the vector store for similar documents
            results = vector_store.similarity_search(query, k=5)
            
            if not results:
                return "No relevant documents found in the music knowledge base."
            
            # Format the results
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

async def researcher_node(state: State) -> Command[Literal["writer", "__end__"]]:
    """Research node that hands off to writer."""
    print("\n" + "="*50)
    print("RESEARCHER NODE")
    print("="*50)
    
    # Get the researcher agent from the closure
    response = await researcher_agent.ainvoke({"messages": state["messages"]})
    
    # Debug: Print search results and tool usage
    print("\n--- Research Results ---")
    for msg in response["messages"]:
        # Check for tool calls (AI messages with tool_calls)
        if hasattr(msg, 'tool_calls') and msg.tool_calls:
            for tool_call in msg.tool_calls:
                print(f"\nTool Called: {tool_call.get('name', 'Unknown')}")
                print(f"Arguments: {tool_call.get('args', {})}")
        
        # Check for tool responses (ToolMessage)
        if msg.type == "tool":
            print(f"\nTool Response from: {getattr(msg, 'name', 'Unknown Tool')}")
            content_preview = str(msg.content)[:500] + "..." if len(str(msg.content)) > 500 else str(msg.content)
            print(f"Content: {content_preview}")
        
        # Print AI responses (but not tool calls)
        if msg.type == "ai" and not hasattr(msg, 'tool_calls'):
            print(f"\nResearcher Response:")
            print(f"{msg.content}")
    
    print("\n" + "="*50 + "\n")
    
    # Native handoff: explicitly tell the graph to move to 'writer'
    return Command(
        update={"messages": response["messages"]},
        goto="writer"
    )

async def writer_node(state: State) -> Command[Literal["editor", "__end__"]]:
    """Writer node that hands off to editor."""
    print("\n" + "="*50)
    print("WRITER NODE")
    print("="*50)
    
    response = await writer_agent.ainvoke({"messages": state["messages"]})
    
    # Print the written content
    final_message = response["messages"][-1]
    print(f"\nWriter Output:")
    print(f"{final_message.content}")
    print("\n" + "="*50 + "\n")
    
    # Native handoff: explicitly tell the graph to move to 'editor'
    return Command(
        update={"messages": response["messages"]},
        goto="editor"
    )

async def editor_node(state: State) -> Command[Literal["writer", "__end__"]]:
    """Editor node that can hand back to writer or end."""
    print("\n" + "="*50)
    print("EDITOR NODE")
    print("="*50)
    
    response = await editor_agent.ainvoke({"messages": state["messages"]})
    
    # Debug: Print editor feedback
    final_message = response["messages"][-1]
    print(f"\nEditor Feedback:")
    print(f"{final_message.content}")
    
    # Example logic: if editor finds an error, hand back to writer
    if "REVISE" in str(final_message.content):
        print("\n⚠️  Editor requested REVISION - routing back to writer")
        print("="*50 + "\n")
        return Command(
            update={"messages": response["messages"]},
            goto="writer"
        )
    
    print("\n✓ Editor approved - workflow complete")
    print("="*50 + "\n")
    
    return Command(
        update={"messages": response["messages"]},
        goto="__end__"
    )

async def main():
    """Run the multi-agent content creation workflow."""
    global researcher_agent, writer_agent, editor_agent
    
    # Load environment variables
    load_dotenv()
    
    # Check for required API keys
    if not os.getenv("GITHUB_TOKEN"):
        print("Error: GITHUB_TOKEN not found.")
        print("Add GITHUB_TOKEN=your-token to a .env file")
        return
    
    if not os.getenv("TAVILY_API_KEY"):
        print("Error: TAVILY_API_KEY not found.")
        print("Add TAVILY_API_KEY=your-key to a .env file")
        print("Get your API key from: https://app.tavily.com/")
        return
    
    # Initialize LLM
    llm = ChatOpenAI(
        model="openai/gpt-4o",
        temperature=0.7,
        base_url="https://models.github.ai/inference",
        api_key=os.getenv("GITHUB_TOKEN")
    )
    
    print("\nOrchestration setup complete!")

    #Load prompts from local filesystem
    with open("templates/researcher.json", "r") as f:
        researcher_data = json.load(f)
        researcher_prompt = researcher_data.get("template", "You are a helpful research assistant.")
    
    with open("templates/writer.json", "r") as f:
        writer_data = json.load(f)
        writer_prompt = writer_data.get("template", "You are a helpful writing assistant.")
    
    with open("templates/editor.json", "r") as f:
        editor_data = json.load(f)
        editor_prompt = editor_data.get("template", "You are a helpful editing assistant.")
    
    # Initialize vector store for music knowledge base
    print("\n📚 Loading music knowledge base...")
    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-small",
        api_key=os.getenv("GITHUB_TOKEN"),
        base_url="https://models.github.ai/inference"
    )
    vector_store = InMemoryVectorStore(embedding=embeddings)
    
    # Load CSV files into the vector store
    load_and_store_CSV(vector_store, "assets/scales.csv")
    load_and_store_CSV(vector_store, "assets/scale_types.csv")
    
    # Load PDF files into the vector store
    # Add your PDF file paths here as needed
    import glob
    pdf_files = glob.glob("assets/*.pdf")
    for pdf_file in pdf_files:
        load_and_store_PDF(vector_store, pdf_file)
    
    # Get Tavily API key from environment
    tavily_api_key = os.getenv("TAVILY_API_KEY")
    
    # Create MCP client for Tavily
    research_client = MultiServerMCPClient({
        "tavily": {
            "transport": "streamable_http",
            "url": f"https://mcp.tavily.com/mcp/?tavilyApiKey={tavily_api_key}",
        }
    })

    # Get tools from the client (await because it's async)
    researcher_tools = await research_client.get_tools()
    
    print(f"Research tools: {[tool.name for tool in researcher_tools]}")
    
    # Create and add the vector store retrieval tool
    retrieval_tool = create_retrieval_tool(vector_store)
    researcher_tools.append(retrieval_tool)
    
    print(f"Added knowledge base retrieval tool")

    # Create agents using create_agent (new API)
    researcher_agent = create_agent(
        llm, 
        tools=researcher_tools, 
        system_prompt=researcher_prompt
    )

    # Writer and editor don't need tools
    writer_agent = create_agent(
        llm, 
        tools=[],
        system_prompt=writer_prompt
    )

    editor_agent = create_agent(
        llm, 
        tools=[], 
        system_prompt=editor_prompt
    )
    # Build the Graph without manual edges (Edgeless Handoff)
    builder = StateGraph(State)
    builder.add_node("researcher", researcher_node)
    builder.add_node("writer", writer_node)
    builder.add_node("editor", editor_node
    )
    
    # Set the entry point
    builder.add_edge(START, "researcher")
    graph = builder.compile()
    
    # Run the workflow
    print("\n" + "="*50)
    print("Starting Multi-Agent Content Creation Workflow")
    print("="*50 + "\n")
    
    user_input = input("Enter the topic that you would like to research:")
    initial_message = HumanMessage(content=user_input)
    result = await graph.ainvoke({"messages": [initial_message]})
    
    print("\n" + "="*50)
    print("Workflow Complete")
    print("="*50 + "\n")
    print("Final Output:")
    print(result["messages"][-1].content if result["messages"] else "No output")

if __name__ == "__main__":
    asyncio.run(main())