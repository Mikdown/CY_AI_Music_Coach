import os
import json
from datetime import datetime
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Load environment variables from .env file
load_dotenv()


def load_and_store_documents(vector_store, file_path):
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


def load_document_with_chunks(vector_store, file_path, chunks):
    """
    Load pre-chunked documents into the vector store with metadata tracking.
    
    Args:
        vector_store: The InMemoryVectorStore instance
        file_path: Path to the source file
        chunks: List of LangChain Document objects (chunks)
    
    Returns:
        int: Total number of chunks stored
    """
    try:
        if not chunks:
            print(f"⚠️  No chunks provided for {file_path}")
            return 0
        
        file_name = os.path.basename(file_path)
        total_chunks = len(chunks)
        stored_count = 0
        
        for index, chunk in enumerate(chunks, start=1):
            # Update metadata for each chunk
            chunk.metadata["fileName"] = f"{file_name} (Chunk {index}/{total_chunks})"
            chunk.metadata["createdAt"] = datetime.now().isoformat()
            chunk.metadata["chunkIndex"] = index
            
            # Add chunk to vector store
            try:
                vector_store.add_documents([chunk])
                stored_count += 1
                print(f"  📌 Chunk {index}/{total_chunks} stored")
            except Exception as chunk_error:
                print(f"  ❌ Failed to store chunk {index}: {chunk_error}")
        
        if stored_count > 0:
            print(f"✅ Successfully stored {stored_count}/{total_chunks} chunks from {file_name}\n")
        
        return stored_count
        
    except Exception as e:
        print(f"❌ Error processing chunks for {file_path}: {e}")
        return 0


# def read_scales_from_sqlite(db_path, vector_store, text_splitter):
#     """
#     Read scale data from SQLite database and load into vector store.
#     
#     Args:
#         db_path: Path to the SQLite database file
#         vector_store: The InMemoryVectorStore instance
#         text_splitter: RecursiveCharacterTextSplitter instance for chunking
#     
#     Returns:
#         int: Total number of chunks stored
#     """
#     try:
#         if not os.path.exists(db_path):
#             print(f"❌ Database file not found: {db_path}")
#             return 0
#         
#         connection = sqlite3.connect(db_path)
#         connection.row_factory = sqlite3.Row  # Return rows as dictionaries
#         cursor = connection.cursor()
#         
#         # Get all table names
#         cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
#         tables = cursor.fetchall()
#         
#         if not tables:
#             print(f"⚠️  No tables found in {db_path}")
#             connection.close()
#             return 0
#         
#         total_chunks_stored = 0
#         
#         # Process each table
#         for table_info in tables:
#             table_name = table_info[0]
#             
#             # Skip SQLite internal tables
#             if table_name.startswith("sqlite_"):
#                 continue
#             
#             print(f"📚 Reading from table: {table_name}")
#             
#             try:
#                 cursor.execute(f"SELECT * FROM {table_name}")
#                 rows = cursor.fetchall()
#                 
#                 if not rows:
#                     print(f"  ⚠️  Table '{table_name}' is empty\n")
#                     continue
#                 
#                 documents = []
#                 
#                 # Convert rows to documents
#                 for row in rows:
#                     row_dict = dict(row)
#                     # Create page content from all columns
#                     page_content = ", ".join([f"{k}: {v}" for k, v in row_dict.items()])
#                     
#                     # Create metadata
#                     metadata = {
#                         "source": "sqlite",
#                         "database": os.path.basename(db_path),
#                         "table": table_name,
#                         "createdAt": datetime.now().isoformat(),
#                     }
#                     # Add all columns as metadata
#                     metadata.update(row_dict)
#                     
#                     # Create document
#                     doc = Document(
#                         page_content=page_content,
#                         metadata=metadata
#                     )
#                     documents.append(doc)
#                 
#                 if documents:
#                     # Split documents into chunks
#                     split_docs = text_splitter.split_documents(documents)
#                     
#                     # Load chunks into vector store
#                     chunks_stored = load_document_with_chunks(
#                         vector_store,
#                         f"{table_name}.db",
#                         split_docs
#                     )
#                     total_chunks_stored += chunks_stored
#                 
#             except sqlite3.Error as table_error:
#                 print(f"  ❌ Error reading table '{table_name}': {table_error}\n")
#                 continue
#         
#         connection.close()
#         
#         if total_chunks_stored > 0:
#             print(f"✅ Successfully loaded {total_chunks_stored} total chunks from SQLite database\n")
#         
#         return total_chunks_stored
#         
#     except sqlite3.Error as e:
#         print(f"❌ SQLite connection error: {e}")
#         return 0
#     except Exception as e:
#         print(f"❌ Error reading from SQLite database: {e}")
#         return 0


def load_coach_prompt():
    """
    Load the Guitar Coach AI system prompt from coach_prompt.json.
    
    Returns:
        str: The system prompt text, or default prompt if file not found
    """
    try:
        assets_dir = os.path.join(os.path.dirname(__file__), "assets")
        prompt_file = os.path.join(assets_dir, "coach_prompt.json")
        
        if not os.path.exists(prompt_file):
            print(f"⚠️  Coach prompt file not found at {prompt_file}")
            return get_default_coach_prompt()
        
        with open(prompt_file, 'r', encoding='utf-8') as f:
            prompt_data = json.load(f)
        
        # Extract the system role from the JSON
        system_prompt = prompt_data.get("system_role", "")
        if not system_prompt:
            print("⚠️  No 'system_role' field found in coach_prompt.json")
            return get_default_coach_prompt()
        
        print("✅ Loaded coach prompt from JSON\n")
        return system_prompt
        
    except json.JSONDecodeError as e:
        print(f"❌ Error parsing coach_prompt.json: {e}")
        return get_default_coach_prompt()
    except Exception as e:
        print(f"❌ Error loading coach prompt: {e}")
        return get_default_coach_prompt()


def get_default_coach_prompt():
    """
    Return a default coach prompt if the JSON file is not available.
    
    Returns:
        str: Default system prompt
    """
    return (
        "You are Guitar Coach AI, a warm, knowledgeable guitar instructor who helps players "
        "design and complete focused 30-minute practice sessions. You adapt naturally to each user's "
        "level, style, and goals, while keeping language friendly, motivating, and conversational. "
        "Guide users through creating personalized practice plans with practical exercises, tips, and encouragement."
    )


def main():
    """Main function to start the Guitar Coach AI application."""
    print("🎸 Welcome to Guitar Coach AI! 🎸")
    print("Let's create your perfect 30-minute practice session.\n")
    
    # Check for required environment variables
    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        print("❌ Error: GITHUB_TOKEN not found in environment variables.")
        print("\n📝 Setup Instructions:")
        print("1. Create or update your .env file in the project root directory")
        print("2. Add your GitHub token:")
        print("   GITHUB_TOKEN=your_github_token_here")
        print("3. Get a token from: https://github.com/settings/tokens")
        print("\n🔐 Token Permissions Needed:")
        print("   - repo (full control of private repositories)")
        print("   - gist (create gists)")
        print("\nOnce configured, run the application again.\n")
        return
    
    print("✅ Environment configured successfully!\n")
    
    # Initialize ChatOpenAI with GitHub Models
    llm = ChatOpenAI(
        model="openai/gpt-4o",
        temperature=0,
        base_url="https://models.github.ai/inference",
        api_key=github_token
    )
    print("🤖 AI Coach initialized and ready!\n")
    
    # Initialize OpenAI Embeddings for semantic search
    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-small",
        base_url="https://models.inference.ai.azure.com",
        api_key=os.getenv("GITHUB_TOKEN")
    )
    print("🔍 Embeddings model initialized!\n")
    
    # Create in-memory vector store for knowledge storage
    vector_store = InMemoryVectorStore(embeddings)
    print("📚 Vector store created!\n")
    
    # Initialize text splitter for chunking
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=2000,
        chunk_overlap=50,
        separators=["\n\n", "\n", " ", ""]
    )
    print("✂️ Text splitter initialized!\n")
    
    # Load documents from CSV file
    assetts_dir = os.path.join(os.path.dirname(__file__), "assets")
    scales_file = os.path.join(assetts_dir, "scales.csv")
    
    print("📖 Loading knowledge base...\n")
    load_and_store_documents(vector_store, scales_file)
    
    # Load documents from SQLite database
    db_path = os.path.join(os.path.dirname(__file__), "ai_music.db")
    # if os.path.exists(db_path):
    #     print("📖 Loading from SQLite database...\n")
    #     read_scales_from_sqlite(db_path, vector_store, text_splitter)
    # else:
    #     print(f"❌ Error: SQLite database not found at {db_path}")
    #     print("   Please create or place 'ai_music.db' in the project root directory.\n")
    
    # Load the coach prompt
    coach_prompt = load_coach_prompt()
    
    # Conversation loop
    print("💬 Type 'exit' or 'quit' to end the conversation.\n")
    
    conversation_history = [SystemMessage(content=coach_prompt)]
    
    while True:
        # Get user input for the guitar coach
        user_query = input("🎸 You: ")
        
        # Check for exit commands
        if user_query.lower() in ['exit', 'quit', 'bye', 'goodbye']:
            print("\n🎸 Thanks for practicing with Guitar Coach AI! Keep up the great work! 🎵\n")
            break
        
        if not user_query.strip():
            print("⚠️  Please enter a question or comment.\n")
            continue
        
        print()
        
        # Add user message to conversation history
        conversation_history.append(HumanMessage(content=user_query))
        
        # Invoke the LLM with full conversation history
        response = llm.invoke(conversation_history)
        
        # Add AI response to conversation history
        conversation_history.append(response)
        
        # Print the response
        print(f"🎵 Coach: {response.content}\n")


if __name__ == "__main__":
    main()
