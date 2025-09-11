import os
from dotenv import load_dotenv
import httpx
from typing import List, Dict
import json

load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Simple in-memory storage for demo purposes
documents = []

def process_document_upload(file):
    """Process uploaded document and store content"""
    try:
        # Read file content
        content = file.file.read().decode('utf-8')
        
        # Store document
        documents.append({
            'content': content,
            'filename': file.filename,
            'chunks': [content[i:i+1000] for i in range(0, len(content), 800)]
        })
        
        return len(documents[-1]['chunks'])
    except Exception as e:
        print(f"Error processing document: {e}")
        return 0

async def process_query(query: str):
    """Process query using simple similarity search"""
    if not documents:
        return {"answer": "No documents uploaded yet. Please upload some documents first.", "sources": []}
    
    # Simple keyword-based search for demo
    relevant_chunks = []
    for doc in documents:
        for chunk in doc['chunks']:
            if any(word.lower() in chunk.lower() for word in query.lower().split()):
                relevant_chunks.append({
                    'content': chunk,
                    'source': doc['filename']
                })
    
    if not relevant_chunks:
        return {"answer": "No relevant information found in the uploaded documents.", "sources": []}
    
    # Use OpenRouter to generate answer
    context = "\n\n".join([chunk['content'] for chunk in relevant_chunks[:3]])
    
    try:
        # Using a free model from OpenRouter
        response = httpx.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "http://localhost:8000",
                "X-Title": "RAG Chatbot"
            },
            json={
                "model": "meta-llama/llama-3.2-3b-instruct:free",
                "messages": [
                    {"role": "system", "content": "You are a helpful sales assistant for Ripped Up Nutrition. Keep responses SHORT and CONCISE (2-3 sentences max). Focus on key points only. Be enthusiastic but brief."},
                    {"role": "user", "content": f"Context: {context}\n\nQuestion: {query}\n\nKeep your response SHORT and to the point."}
                ],
                "max_tokens": 150
            },
            timeout=30.0
        )
        
        if response.status_code == 200:
            result = response.json()
            answer = result["choices"][0]["message"]["content"]
            sources = [{"source": chunk['source']} for chunk in relevant_chunks[:3]]
            return {"answer": answer, "sources": sources}
        else:
            return {"answer": f"Error from OpenRouter API: {response.status_code} - {response.text}", "sources": []}
            
    except Exception as e:
        return {"answer": f"Error processing query: {str(e)}", "sources": []}
