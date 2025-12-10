from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import torch
import clip
import numpy as np
import json
import os

app = FastAPI()

# Load models and data at startup
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Loading CLIP on {device}...")
try:
    model, preprocess = clip.load("ViT-B/32", device=device)
except Exception as e:
    print(f"Error loading CLIP: {e}")
    model = None

print("Loading embeddings...")
# Use absolute paths as in the user's example
EMBEDDINGS_PATH = "/mnt/bit/wxc/projects/zhongche-llm/embeddings/all_embeddings.npz"
DATA_PATH = "/mnt/bit/wxc/projects/zhongche-llm/data/train_data_all.json"

try:
    database = np.load(EMBEDDINGS_PATH)
    embeddings = database["embeddings"]
    embeddings_tensor = torch.from_numpy(embeddings).to(device)
except Exception as e:
    print(f"Error loading embeddings: {e}")
    embeddings_tensor = None

print("Loading data...")
try:
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
except Exception as e:
    print(f"Error loading data: {e}")
    data = []

class Query(BaseModel):
    text: str

@app.post("/retrieve")
async def retrieve(query: Query):
    if model is None or embeddings_tensor is None:
        raise HTTPException(status_code=503, detail="Model or data not loaded")
        
    try:
        text = query.text
        # Truncate text if too long for CLIP (77 tokens max usually, but let's just pass it)
        text_token = clip.tokenize(text[:77], truncate=True).to(device)
        
        with torch.no_grad():
            text_embed = model.encode_text(text_token)
            text_embed = text_embed / text_embed.norm(dim=-1, keepdim=True)
            
            similarities = torch.einsum("jk,ijk->ij", text_embed, embeddings_tensor)
            idx = torch.argmax(similarities, dim=0)
            idx_value = idx.item()
            
        retrieved_doc = data[idx_value]['output']
        title = data[idx_value].get('instruction', 'Document')
        score = float(similarities[idx_value].item())
        
        return {
            "document": retrieved_doc,
            "title": title,
            "score": score,
            "id": str(idx_value)
        }
    except Exception as e:
        print(f"Error during retrieval: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    print("Starting RAG Service on port 8001...")
    uvicorn.run(app, host="0.0.0.0", port=8001)
