import os
from pinecone import Pinecone, ServerlessSpec
from dotenv import load_dotenv
import time

load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "news-index")

pc = Pinecone(api_key=PINECONE_API_KEY)

def init_pinecone():
    """Initializes Pinecone index if it doesn't exist."""
    existing_indexes = [index.name for index in pc.list_indexes()]
    
    if PINECONE_INDEX_NAME not in existing_indexes:
        print(f"Creating index: {PINECONE_INDEX_NAME}")
        try:
            pc.create_index(
                name=PINECONE_INDEX_NAME,
                dimension=768, # Dimension for text-embedding-004
                metric="cosine",
                spec=ServerlessSpec(
                    cloud="aws",
                    region="us-east-1"
                )
            )
            # Wait for index to be ready
            while not pc.describe_index(PINECONE_INDEX_NAME).status['ready']:
                time.sleep(1)
            print("Index created successfully.")
        except Exception as e:
            print(f"Error creating index: {e}")
    else:
        print(f"Index {PINECONE_INDEX_NAME} already exists.")

def get_index():
    return pc.Index(PINECONE_INDEX_NAME)

def upsert_vectors(vectors):
    """
    Upserts vectors to Pinecone.
    vectors: List of tuples (id, embedding, metadata)
    """
    index = get_index()
    try:
        # Upsert in batches of 100
        batch_size = 100
        for i in range(0, len(vectors), batch_size):
            batch = vectors[i:i+batch_size]
            index.upsert(vectors=batch)
        print(f"Upserted {len(vectors)} vectors.")
    except Exception as e:
        print(f"Error upserting vectors: {e}")

def query_vectors(query_embedding, top_k=5):
    """
    Queries Pinecone for similar vectors.
    """
    index = get_index()
    try:
        results = index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True
        )
        return results
    except Exception as e:
        print(f"Error querying vectors: {e}")
        return None

def fetch_recent_vectors(limit=20):
    """
    Fetches 'recent' vectors. 
    Since Pinecone doesn't support 'list all' efficiently, we query with a dummy vector.
    """
    index = get_index()
    try:
        # Create a dummy vector of zeros
        dummy_vector = [0.0] * 768
        
        results = index.query(
            vector=dummy_vector,
            top_k=limit,
            include_metadata=True
        )
        
        articles = []
        if results and results.matches:
            for match in results.matches:
                # Reconstruct article object from metadata
                meta = match.metadata
                articles.append({
                    "title": meta.get('title'),
                    "link": meta.get('link'),
                    "summary": meta.get('summary'),
                    "full_text": meta.get('full_text'),
                    "source": meta.get('source'),
                    "published": meta.get('published')
                })
        return articles
    except Exception as e:
        print(f"Error fetching recent vectors: {e}")
        return []

if __name__ == "__main__":
    init_pinecone()
