import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
import os # Import os for path handling

# Define a path for ChromaDB to store its data
# It's good practice to put this in a specific directory
CHROMA_DB_PATH = "./chroma_data"
os.makedirs(CHROMA_DB_PATH, exist_ok=True) # Ensure the directory exists

# Initialize ChromaDB client with a persistent path
chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)

embedding_fn = SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")

collection = chroma_client.get_or_create_collection(
    name="server_knowledge",
    embedding_function=embedding_fn
)

def add_knowledge(doc_id: str, content: str, metadata: dict = None):
    if metadata is None:
        metadata = {}
    if not metadata:
        # You might want to allow empty metadata if 'type' is not always present,
        # but for now, your current add_knowledge requires it.
        # For 'user_teach', you explicitly set it, so this should be fine.
        raise ValueError("Metadata must be a non-empty dictionary")
    try:
        collection.add(documents=[content], ids=[doc_id], metadatas=[metadata])
        print(f"Added knowledge: ID={doc_id}, Content='{content[:50]}...', Metadata={metadata}")
    except Exception as e:
        print(f"Error adding knowledge '{doc_id}': {e}")


def query_knowledge(query: str, n_results: int = 5, where: dict = None):
    try:
        results = collection.query(
            query_texts=[query],
            n_results=n_results,
            where=where,
            include=['documents', 'metadatas', 'distances'] # Include distances for debugging
        )
        print(f"\n--- ChromaDB Query Results for '{query}' ---")
        print(f"  Documents: {results['documents']}")
        print(f"  Metadatas: {results['metadatas']}")
        print(f"  Distances (lower is better): {results['distances']}") # Lower is better, typically < 0.5-0.6 for good matches
        print(f"---------------------------------------------------\n")


        return results['documents'][0] if results['documents'] else []
    except Exception as e:
        print(f"Error querying knowledge: {e}")
        return []

def list_all_knowledge():
    try:
        # For listing all knowledge, you might want more detail than just documents
        all_docs = collection.get(include=['documents', 'metadatas'])
        print("\n--- All Knowledge in ChromaDB ---")
        for i in range(len(all_docs['ids'])):
            print(f"ID: {all_docs['ids'][i]}")
            print(f"  Content: {all_docs['documents'][i][:100]}...") # Print first 100 chars
            print(f"  Metadata: {all_docs['metadatas'][i]}")
            print("-" * 20)
        print("----------------------------------\n")
        return all_docs
    except Exception as e:
        print(f"Error listing knowledge: {e}")
        return None
    
    
    