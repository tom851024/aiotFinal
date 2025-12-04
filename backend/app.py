from flask import Flask, jsonify, request
from flask_cors import CORS
import json
import os
import processor
import vector_db
import google.generativeai as genai

app = Flask(__name__, static_folder="../frontend_simple", static_url_path="/")
CORS(app)

@app.route('/')
def index():
    return app.send_static_file('index.html')

# Load articles from JSON - REMOVED for Vercel
# ARTICLES_FILE = "articles.json"

@app.route('/api/briefing', methods=['GET'])
def get_briefing():
    """Generates and returns a daily briefing."""
    # Fetch recent articles directly from Pinecone
    articles = vector_db.fetch_recent_vectors(limit=20)
    
    if articles:
        # Generate briefing from the articles
        # In a real app, we might cache this result
        briefing = processor.generate_daily_briefing(articles)
        return jsonify(briefing)
    else:
        return jsonify({"categories": []})

@app.route('/api/chat', methods=['POST'])
def chat():
    """
    Handles chat requests using RAG.
    """
    data = request.json
    user_message = data.get('message')
    
    if not user_message:
        return jsonify({"error": "Message is required"}), 400
    
    print(f"User query: {user_message}")
    
    # 1. Generate embedding
    query_embedding = processor.generate_embedding(user_message)
    
    if not query_embedding:
        return jsonify({"response": "Sorry, I couldn't process your request."})
    
    # 2. Query Pinecone
    results = vector_db.query_vectors(query_embedding, top_k=3)
    
    context_text = ""
    if results and results.matches:
        for match in results.matches:
            meta = match.metadata
            # Use full_text if available for better answers
            content = meta.get('full_text') or meta.get('summary')
            context_text += f"Title: {meta.get('title')}\nContent: {content}\nSource: {meta.get('source')}\n\n"
    
    print("Context found:", context_text[:100] + "...")
    
    # 3. Answer Question using processor
    try:
        print("Calling processor.answer_question...")
        response_text = processor.answer_question(context_text, user_message)
        print("Answer generated successfully.")
        return jsonify({"response": response_text})
    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"response": "Sorry, I encountered an error generating the response."})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
