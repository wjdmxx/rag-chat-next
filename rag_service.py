from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import torch
import numpy as np
import json
from openai import AsyncOpenAI
from sentence_transformers import SentenceTransformer

app = FastAPI()

# 配置参数（来自 rag-v2.py）
MODEL_PATH = '/mnt/bit/wxc/projects/zhongche-llm/bge-m3'
RERANK_MODEL = "/mnt/bit/wxc/projects/zhongche-llm/Qwen3-Reranker-8B"
VECTOR_THRESHOLD = 0.40      # 粗排门槛
COLBERT_THRESHOLD = 0.80     # ColBERT 强校验门槛
RERANK_THRESHOLD = 0.85      # 精排得分门槛
COLBERT_GAP_THRESHOLD = 0.04 # ColBERT 区分度门槛

# 翻译用的客户端 (8001 - 原7999)
translation_client = AsyncOpenAI(
    api_key="EMPTY",
    base_url="http://localhost:8001/v1",
)

# Reranker 客户端 (8002)
from openai import OpenAI
reranker_client = OpenAI(base_url="http://localhost:8002/v1", api_key="none")

# 数据路径
EMBEDDINGS_PATH = "/mnt/bit/wxc/projects/zhongche-llm/embeddings/all_embeddings_bgem3.npz"
DATA_PATH = "/mnt/bit/wxc/projects/zhongche-llm/data/train_data_all.json"

# 加载模型
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Loading BGE-M3 on {device}...")
try:
    bgem3_model = SentenceTransformer(MODEL_PATH)
except Exception as e:
    print(f"Error loading BGE-M3: {e}")
    bgem3_model = None

# 加载嵌入向量
print("Loading embeddings...")
try:
    database = np.load(EMBEDDINGS_PATH)
    embeddings = database["key_b"]
    embeddings_tensor = torch.from_numpy(embeddings).to(device)
except Exception as e:
    print(f"Error loading embeddings: {e}")
    embeddings_tensor = None

# 加载数据
print("Loading data...")
try:
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
except Exception as e:
    print(f"Error loading data: {e}")
    data = []

def colbert_verify(query, document, model):
    """基于逐 Token Embedding 手动归一化的细粒度交互校验"""
    with torch.no_grad():
        q_reps = model.encode(query, output_value='token_embeddings', convert_to_tensor=True)
        d_reps = model.encode(document, output_value='token_embeddings', convert_to_tensor=True)
        
        # 手动 L2 归一化
        q_reps = torch.nn.functional.normalize(q_reps, p=2, dim=-1)
        d_reps = torch.nn.functional.normalize(d_reps, p=2, dim=-1)
        
        # 计算 MaxSim
        sim_matrix = torch.matmul(q_reps, d_reps.T) 
        max_sim_per_token, _ = torch.max(sim_matrix, dim=1)
        return torch.mean(max_sim_per_token).item()

def industrial_filter(query, raw_answers, raw_indices, vector_values, model):
    """三关过滤逻辑（来自 rag-v2.py）"""
    # --- 第一关：粗排向量检查 ---
    max_vector_score = vector_values[0].item() 
    if max_vector_score < VECTOR_THRESHOLD:
        return None, None, "第一关未通过：语义相关度太低。"

    # --- 第二关：ColBERT 区分度校验 ---
    c_score_top1 = colbert_verify(query, raw_answers[0], model)
    c_score_top2 = colbert_verify(query, raw_answers[1], model)
    c_gap = c_score_top1 - c_score_top2
    
    print(f"ColBERT 校验: Top1={c_score_top1:.4f}, Gap={c_gap:.4f}")

    if c_score_top1 < COLBERT_THRESHOLD:
        return None, None, f"第二关未通过：词级匹配度不足 ({c_score_top1:.4f})。"

    # --- 第三关：Reranker 逻辑 ---
    refined_query = (
        "Task: Rigorously evaluate the semantic match between the User Query and the Document.\n"
        f"User Query: {query}"
    )

    try:
        response = reranker_client.post(
            "/rerank",
            body={
                "model": RERANK_MODEL,
                "query": refined_query,
                "documents": raw_answers,
                "top_n": 5, 
            },
            cast_to=list
        )
        rerank_map = {res['index']: res['relevance_score'] for res in response['results']}
        top1_original_score = rerank_map.get(0, 0) 
        
    except Exception as e:
        return None, None, f"精排服务异常: {str(e)}"

    print(f"精排对原 Top1 的打分: {top1_original_score:.4f}")

    # 逻辑判定
    if c_gap >= COLBERT_GAP_THRESHOLD:
        if top1_original_score >= RERANK_THRESHOLD:
            return raw_answers[0], raw_indices[0], "匹配成功（ColBERT 高置信度确认）"
        else:
            return None, None, f"精排否定了 ColBERT 的结果 (Score: {top1_original_score:.4f})"
    
    # 如果 ColBERT 觉得 Top 1 和 Top 2 差不多 (Gap 小)
    top1_res = response['results'][0]
    if top1_res['relevance_score'] >= 0.95:
        return raw_answers[top1_res['index']], raw_indices[top1_res['index']], "匹配成功（精排高分放行）"

    return None, None, f"区分度不足：ColBERT Gap ({c_gap:.4f}) 过小。"

class Query(BaseModel):
    text: str

@app.post("/retrieve")
async def retrieve(query: Query):
    if bgem3_model is None or embeddings_tensor is None:
        raise HTTPException(status_code=503, detail="Model or data not loaded")
        
    try:
        text = query.text
        
        # 检测中文并翻译
        if any('\u4e00' <= char <= '\u9fff' for char in text):
            print(f"Detected Chinese input: {text}")
            try:
                response = await translation_client.chat.completions.create(
                    model="/mnt/bit/wxc/projects/zhongche-llm/Qwen2.5-14B-Instruct",
                    messages=[
                        {"role": "system", "content": "你是一个翻译助手。请将用户输入的中文翻译成英文。只返回英文翻译，不要包含其他内容。"},
                        {"role": "user", "content": text}
                    ],
                    temperature=0.1
                )
                translated_text = response.choices[0].message.content.strip()
                print(f"Translated to: {translated_text}")
                text = translated_text
            except Exception as e:
                print(f"Translation failed: {e}")
                # 如果翻译失败，继续使用原始文本

        # 粗排部分
        with torch.no_grad():
            ins_text_embed = bgem3_model.encode(sentences=text, convert_to_tensor=True, normalize_embeddings=True).unsqueeze(0)
            
            similarities = torch.einsum("jk,ijk->ij", ins_text_embed, embeddings_tensor.unsqueeze(1))
            values, indices = torch.topk(similarities.flatten(), k=5)
            
            raw_answers = []
            raw_indices = []
            for idx in indices.tolist():
                raw_indices.append(idx)
                raw_answers.append(data[idx]['instruction'])

        # 运行三关过滤
        final_context, final_idx, status_msg = industrial_filter(text, raw_answers, raw_indices, values, bgem3_model)
        
        print(f"Filter result: context={'Found' if final_context else 'None'}, status={status_msg}")
        
        if final_context:
            # 找到匹配内容
            return {
                "document": data[final_idx]['output'],
                "title": data[final_idx].get('instruction', 'Document'),
                "score": float(values[0].item()),
                "id": str(final_idx),
                "matched": True,
                "status": status_msg
            }
        else:
            # 未找到匹配内容
            return {
                "document": "",
                "title": "",
                "score": float(values[0].item()) if len(values) > 0 else 0.0,
                "id": "",
                "matched": False,
                "status": status_msg
            }
            
    except Exception as e:
        print(f"Error during retrieval: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    print("Starting RAG Service on port 8003...")
    uvicorn.run(app, host="0.0.0.0", port=8003)
