import vector_db
import os
from dotenv import load_dotenv

load_dotenv()

print(f"API Key: {os.getenv('PINECONE_API_KEY')[:5]}...")
print(f"Index Name: {os.getenv('PINECONE_INDEX_NAME')}")

print("Attempting to fetch recent vectors...")
vectors = vector_db.fetch_recent_vectors(limit=5)
print(f"Found {len(vectors)} vectors.")
if vectors:
    print("First vector title:", vectors[0]['title'])
else:
    print("No vectors found with current query method.")
