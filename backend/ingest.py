import scraper
import processor
import vector_db
import hashlib

def ingest_data():
    print("Starting data ingestion...")
    
    # 1. Initialize Pinecone
    vector_db.init_pinecone()
    
    # 2. Scrape News
    print("Scraping news...")
    articles = scraper.scrape_all_news()
    print(f"Found {len(articles)} articles.")
    
    vectors = []
    
    for article in articles:
        print(f"Processing: {article['title']}")
        
        # Use full text if available, otherwise fallback to summary
        content_to_process = article.get('full_text') or article['summary']
        
        # Combine title and content for better context
        text_to_process = f"{article['title']}\n{content_to_process}"
        
        # 3. Summarize
        # We want a Traditional Chinese summary of the FULL text.
        summary_zh = processor.summarize_text(text_to_process)
        
        # 4. Generate Embedding
        # We embed the Chinese summary AND the English content (or just the content).
        # To make it searchable by both, we can embed the summary or the full text.
        # Given the user wants "full info", let's embed the full text (truncated if necessary by the model).
        # However, for better RAG performance on questions, embedding the specific chunks is better.
        # But for this simple app, embedding the summary + title is often enough for retrieval, 
        # while storing the full text in metadata allows the LLM to read it later.
        # Let's embed the Chinese summary to support Chinese queries better, 
        # OR embed the original text. The user asked to "input full info".
        # Let's try to embed the text_to_process (truncated to avoid errors).
        # Note: text-embedding-004 has a limit. Let's stick to embedding the summary for now 
        # BUT store the full text. Or maybe embed the first 1000 chars of full text.
        # Let's embed the Chinese summary as it's the primary language for interaction.
        embedding = processor.generate_embedding(summary_zh)
        
        if not embedding:
            print("Skipping due to embedding failure.")
            continue
            
        # Create a unique ID (hash of the link)
        doc_id = hashlib.md5(article['link'].encode()).hexdigest()
        
        metadata = {
            "title": article['title'],
            "link": article['link'],
            "summary": summary_zh, # Store the Chinese summary
            "full_text": content_to_process, # Store the FULL text
            "source": article['source'],
            "published": article['published'],
            "original_summary": article['summary']
        }
        
        vectors.append((doc_id, embedding, metadata))
        
    # 5. Upsert to Pinecone
    if vectors:
        print(f"Upserting {len(vectors)} vectors to Pinecone...")
        vector_db.upsert_vectors(vectors)
        print("Ingestion complete.")
        
        # 6. Save to local JSON for the Feed (and debugging)
        import json
        with open("articles.json", "w", encoding="utf-8") as f:
            # We want to save the metadata which contains the summary and full text
            articles_data = [v[2] for v in vectors]
            json.dump(articles_data, f, ensure_ascii=False, indent=2)
        print("Saved articles to articles.json")
    else:
        print("No vectors to upsert.")

if __name__ == "__main__":
    ingest_data()
