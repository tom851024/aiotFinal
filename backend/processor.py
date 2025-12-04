import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)

# Configuration for Gemini
GENERATION_CONFIG = {
    "temperature": 0.9,
    "top_p": 1,
    "top_k": 1,
    "max_output_tokens": 8192,
}

SAFETY_SETTINGS = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
]

model = genai.GenerativeModel(model_name="gemini-flash-latest",
                              generation_config=GENERATION_CONFIG,
                              safety_settings=SAFETY_SETTINGS)

def summarize_text(text):
    """Summarizes the given text using Gemini."""
    if not text:
        return "No content to summarize."
    
    prompt = f"""
    Summarize the following news article in Traditional Chinese using bullet points.
    Output ONLY the bullet points. Do NOT include any introductory text, headers, or phrases like "Here is the summary".
    
    Article Content:
    {text}
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Error summarizing text: {e}")
        return "Error generating summary."

def generate_embedding(text):
    """Generates embeddings for the given text using Gemini."""
    if not text:
        return []
    
    try:
        # Use embedding-001 model
        result = genai.embed_content(
            model="models/text-embedding-004",
            content=text,
            task_type="retrieval_document",
            title="News Article"
        )
        return result['embedding']
    except Exception as e:
        print(f"Error generating embedding: {e}")
        return []


def generate_daily_briefing(articles):
    """Generates a daily briefing from a list of articles."""
    if not articles:
        return {"categories": []}
    
    # Use the Chinese summaries we already generated to save context window
    articles_content = ""
    for i, art in enumerate(articles[:10]): # Process up to 10 articles to avoid token limits
        articles_content += f"ID: {i}\nTitle: {art.get('title')}\nSummary: {art.get('summary')}\n\n"
        
    prompt = f"""
    You are a professional news editor.
    Analyze the following news summaries and generate a "Daily Briefing" in Traditional Chinese.
    
    Group the news into relevant categories (e.g., Politics, Technology, World, Economy, etc.).
    For each news item, provide:
    1. A translated Traditional Chinese Title.
    2. A one-sentence key takeaway (very concise).
    
    Output the result as a valid JSON object with the following structure:
    {{
        "categories": [
            {{
                "name": "Category Name",
                "articles": [
                    {{
                        "original_title": "Original Title",
                        "zh_title": "Chinese Title",
                        "takeaway": "One sentence summary."
                    }}
                ]
            }}
        ]
    }}
    
    Ensure the JSON is valid and strictly follows the format.
    
    News Summaries:
    {articles_content}
    """
    
    try:
        response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
        text = response.text.strip()
        
        # Remove markdown code blocks if present
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
            
        import json
        return json.loads(text)
    except Exception as e:
        print(f"Error generating briefing: {e}")
        # Print the raw text for debugging
        try:
            print(f"Raw response: {response.text}")
        except:
            pass
        return {"categories": []}

def answer_question(context, question):
    """Answers a question based on the provided context."""
    prompt = f"""
    You are a helpful AI news assistant.
    Answer the user's question based ONLY on the provided context.
    If the answer is not in the context, say "I cannot find the answer in the provided news."
    
    Context:
    {context}
    
    Question:
    {question}
    
    Answer in Traditional Chinese.
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Error answering question: {e}")
        return "Sorry, I encountered an error while processing your request."
