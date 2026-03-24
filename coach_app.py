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
    
    # Conversation loop with step tracking
    print("💬 Type 'exit' or 'quit' to end the conversation.\n")
    
    conversation_history = [SystemMessage(content=coach_prompt)]
    
    # Track conversation step (1-5 for assessment questions)
    current_step = 1
    user_responses = {}
    
    questions = [
        "What guitar are you using today — acoustic or electric?",
        "What's your current guitar level — beginner, intermediate, or advanced?",
        "Which musical style or genre are you feeling today? Rock, blues, jazz, metal, pop, funk, or something else?",
        "What kind of session structure would you like today: Technique & warm-ups, Chords & rhythm, Scales & soloing, Song learning, or Mixed routine?",
        "What key or mood appeals to you right now — mellow, energetic, moody, or should I suggest one?"
    ]
    
    while True:
        # If we haven't completed all 5 questions, ask the current step
        if current_step <= 5:
            if current_step == 1:
                # First turn - greeting + question 1
                print(f"🎵 Coach: Let's create your perfect 30-minute practice session!\n")
                print(f"🎸 Coach: {questions[0]}\n")
            else:
                # Ask the current question
                print(f"🎸 Coach: {questions[current_step - 1]}\n")
        else:
            # All questions answered - now get the AI to create the practice plan
            print("🎵 Coach: Now let me create your personalized 30-minute practice plan...\n")
        
        # Get user input
        user_query = input("🎸 You: ")
        
        # Check for exit commands
        if user_query.lower() in ['exit', 'quit', 'bye', 'goodbye']:
            print("\n🎸 Thanks for practicing with Guitar Coach AI! Keep up the great work! 🎵\n")
            break
        
        if not user_query.strip():
            print("⚠️  Please enter a response.\n")
            continue
        
        print()
        
        # Store response if in question phase
        if current_step <= 5:
            user_responses[f"question_{current_step}"] = user_query
            
            # Check for out-of-context responses during assessment
            # Simple heuristic: check if response is very short or contains certain keywords
            is_likely_out_of_context = False
            out_of_context_keywords = [
                "let's focus", "let's talk", "tell me", "explain", "how do",
                "what about", "why", "when", "where", "show me", "help me"
            ]
            
            # Check if response seems off-topic
            response_lower = user_query.lower()
            if any(keyword in response_lower for keyword in out_of_context_keywords):
                # This might be out of context - ask them to focus on the current question
                print(f"🎵 Coach: I appreciate that! 🎸 Let's focus on creating your practice plan first.\n")
                print(f"We're on question {current_step} of 5: {questions[current_step - 1]}\n")
                # Don't increment step, ask the question again
                continue
            
            # Move to next step
            current_step += 1
        
        # Add user message to conversation history for post-assessment phase
        if current_step > 5:
            conversation_history.append(HumanMessage(content=user_query))
        
        # If all questions answered, generate the practice plan (only on first move to step 6)
        if current_step > 5 and len(user_responses) == 5:
            # Create a structured plan prompt on the first iteration
            guitar_type = user_responses.get('question_1', 'Not provided')
            skill_level = user_responses.get('question_2', 'Not provided')
            genre = user_responses.get('question_3', 'Not provided')
            focus = user_responses.get('question_4', 'Not provided')
            mood = user_responses.get('question_5', 'Not provided')
            
            plan_prompt = f"""YOU MUST CREATE A 30-MINUTE PRACTICE SESSION WITH EXPLICIT TIME LIMITS FOR EACH SECTION.

User Preferences:
- Guitar Type: {guitar_type}
- Skill Level: {skill_level}
- Genre/Style: {genre}
- Session Focus: {focus}
- Key/Mood: {mood}

MANDATORY FORMAT REQUIREMENTS - READ CAREFULLY:
1. EVERY SINGLE EXERCISE must have a time slot in the format: START:TIME–END:TIME
2. Times must use this exact format: M:SS–M:SS (examples: 0:00–5:00, 5:00–15:00, 25:00–30:00)
3. ALL time slots MUST add up to exactly 30 minutes
4. Do NOT skip time designations
5. Do NOT use ranges like "5-10 minutes" - use exact time slots only

REQUIRED OUTPUT STRUCTURE - FOLLOW THIS EXACTLY:
🎸 30-Minute {guitar_type} Guitar Practice Session
Level: {skill_level} | Genre: {genre} | Mood: {mood}

Time Slot | Exercise Name | Duration | Description
0:00–5:00 | [Exercise Name] | 5 min | [Specific details tailored to {guitar_type}]
5:00–15:00 | [Exercise Name] | 10 min | [Specific details tailored to {guitar_type}]
15:00–25:00 | [Exercise Name] | 10 min | [Specific details tailored to {guitar_type}]
25:00–30:00 | [Exercise Name] | 5 min | [Specific details tailored to {guitar_type}]

EXAMPLE OF CORRECT FORMAT:
🎸 30-Minute Electric Guitar Practice Session
Level: Intermediate | Genre: Rock | Mood: Energetic

0:00–5:00 | Finger Warm-up | 5 min | Light stretching and finger independence drills
5:00–15:00 | Power Chord Progression | 10 min | E5-A5-D5 progression at 90 BPM with distortion
15:00–25:00 | Pentatonic Scale Work | 10 min | A minor pentatonic bending and phrasing exercises
25:00–30:00 | Cool Down & Reflection | 5 min | Clean tone improvisation, review what worked

NOW CREATE THE PLAN FOR THIS USER WITH EXACT TIME SLOTS. EVERY EXERCISE MUST HAVE A TIME DESIGNATION."""
            
            # Replace the user query with the plan prompt for proper generation
            conversation_history[-1] = HumanMessage(content=plan_prompt)
            
            # Mark that we've generated the plan prompt
            user_responses["plan_requested"] = True
            
            try:
                response = llm.invoke(conversation_history)
                print(f"🎵 Coach: {response.content}\n")
                conversation_history.append(response)
            except Exception as e:
                print(f"❌ Error: {e}\n")
        
        # For follow-up questions after plan is generated
        elif current_step > 5 and "plan_requested" in user_responses:
            try:
                response = llm.invoke(conversation_history)
                print(f"🎵 Coach: {response.content}\n")
                conversation_history.append(response)
            except Exception as e:
                print(f"❌ Error: {e}\n")


if __name__ == "__main__":
    main()
