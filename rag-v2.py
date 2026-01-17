import torch
import json
import numpy as np
from openai import OpenAI
from sentence_transformers import SentenceTransformer

# 1. 配置参数
MODEL_PATH = '/mnt/bit/wxc/projects/zhongche-llm/bge-m3'
RERANK_MODEL = "/mnt/bit/wxc/projects/zhongche-llm/Qwen3-Reranker-8B"
VECTOR_THRESHOLD = 0.40      # 粗排门槛
COLBERT_THRESHOLD = 0.80     # ColBERT 强校验门槛
RERANK_THRESHOLD = 0.85      # 精排得分门槛
COLBERT_GAP_THRESHOLD = 0.04 # ColBERT 区分度门槛 (0.04~0.05 通常足够拉开差距)

# 2. 初始化模型与客户端
bgem3_model = SentenceTransformer(MODEL_PATH)
reranker_client = OpenAI(base_url="http://localhost:8002/v1", api_key="none")

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
        return None, -9999, f"第二关未通过：词级匹配度不足 ({c_score_top1:.4f})。"

    # --- 第三关：Reranker 逻辑 ---
    refined_query = (
        "Task: Rigorously evaluate the semantic match between the User Query and the Document.\n"
        f"User Query: {query}"
    )

    try:
        # 【核心修改】我们只送 Top1 进去让 Reranker 确认，或者强制取 Reranker 结果中 index 为 0 的项
        response = reranker_client.post(
            "/rerank",
            body={
                "model": RERANK_MODEL,
                "query": refined_query,
                "documents": raw_answers, # 还是送入全部，但我们要逻辑控制
                "top_n": 5, 
            },
            cast_to=list
        )
        # 获取 Reranker 的结果字典，以 index 为 key
        rerank_map = {res['index']: res['relevance_score'] for res in response['results']}
        
        # 拿到 Reranker 给原先粗排 Top 1 打的分数
        top1_original_score = rerank_map.get(0, 0) 
        
    except Exception as e:
        return None, None, f"精排服务异常: {str(e)}"

    print(f"精排对原 Top1 的打分: {top1_original_score:.4f}")

    # 逻辑判定：
    # 如果 ColBERT 觉得 Top 1 已经很完美了（高分且有 Gap），
    # 只要精排分数不离谱（达到阈值），我们就坚持选原 Top 1。
    if c_gap >= COLBERT_GAP_THRESHOLD:
        if top1_original_score >= RERANK_THRESHOLD:
            return raw_answers[0], raw_indices[0], "匹配成功（ColBERT 高置信度确认）"
        else:
            return None, None, f"精排否定了 ColBERT 的结果 (Score: {top1_original_score:.4f})"
    
    # 如果 ColBERT 觉得 Top 1 和 Top 2 差不多 (Gap 小)
    # 这种情况下再参考精排的 Top 1
    top1_res = response['results'][0]
    if top1_res['relevance_score'] >= 0.95: # 只有精排给出极高分才放行
        return raw_answers[top1_res['index']], raw_indices[top1_res['index']], "匹配成功（精排高分放行）"

    return None, None, f"区分度不足：ColBERT Gap ({c_gap:.4f}) 过小。"

# --- 执行流程 ---
# 正向示例——模型给出准确回答
# ins_text = "How to replace Toshiba Satellite A105-S4011 speakers?"
# ins_text = "What tools are necessary for disassembling the Nokia 2366i motherboard?" # good
# ins_text = "How to replace the Nook HD battery safely?" # good
ins_text = "How to replace the keyboard on an HP dv5-1125nr?" # good

# 反向示例——模型给出拒绝回答
# ins_text = "How to repair the NVIDIA H100 GPU?"
# ins_text = "What are the steps to replace the screen of HuaWei Mate 60 Pro?"
# ins_text = "What are the steps to repair the keyboard of the HONOR MagicBook art 14?"

with torch.no_grad():
    # 粗排部分
    ins_text_embed = bgem3_model.encode(sentences=ins_text, convert_to_tensor=True, normalize_embeddings=True).unsqueeze(0)
    database = np.load("embeddings/all_embeddings_bgem3.npz")
    embeddings_tensor = torch.from_numpy(database["key_b"]).to(ins_text_embed.device).unsqueeze(1)
    
    similarities = torch.einsum("jk,ijk->ij", ins_text_embed, embeddings_tensor)
    values, indices = torch.topk(similarities.flatten(), k=5)
    
    raw_answers = []
    raw_indices = []
    with open("data/train_data_all.json", "r", encoding="utf-8") as f:
        data = json.load(f)
        for idx in indices.tolist():
            raw_indices.append(idx)
            raw_answers.append(data[idx]['instruction'])

# 运行过滤
final_context, final_idx, status_msg = industrial_filter(ins_text, raw_answers, raw_indices, values, bgem3_model)

openai_api_key = "EMPTY"
openai_api_base = "http://localhost:8000/v1"
client = OpenAI(
    api_key=openai_api_key,
    base_url=openai_api_base,
)

if final_context:
    print(f"\n✅ 最终选定内容: {final_context}")
    print('final index:', final_idx)
    print(data[final_idx])
    chat_response = client.chat.completions.create(
    model="/mnt/bit/wxc/projects/zhongche-llm/Qwen2.5-14B-Instruct",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {
            "role": "user",
            "content": [
                {"type": "text", "text": f"""
                    请根据以下参考文档生成回答：
                    1. 参考文档风格和结构为示例。
                    2. 输出回答时，请遵循参考文档的格式和步骤编号。
                    3. 所有工具名称请翻译为中文。
                    4. 回答每一句话都翻译成中文（中英文逐句对应）。
                    5. 避免重复句子或冗余说明，若某些安全或注意事项在多个步骤重复，可仅说明一次并在后续步骤引用。
                    7. 限制输出内容的长度，应在800字以内。
                    6. 生成内容的主题为：{ins_text}

                    参考文档：
                    {data[final_idx]['output']}
                    """}
                ],
            },
        ],
        max_tokens=50000
    )
    print("Ground Truth: ", final_context)
    print("User instruction: ", ins_text)
    print("Chat response:", chat_response.choices[0].message.content)
else:
    print(f"\n❌ 拒答原因: {status_msg}")
    chat_response = client.chat.completions.create(
        model='/mnt/bit/wxc/projects/zhongche-llm/Qwen2.5-14B-Instruct',
        messages=[
            {'role': 'system', 'content': 'You are a helpful assistant.'},
            {
                'role': 'user',
                'content': [
                    {'type': 'text', 'text': f"""
                        用户提问{ins_text}。 请结合用户的提问内容生成一段文字，意思是非常抱歉，当前用户的提问内容超出了我的知识范围，无法给出准确的恢复。除了这句话外不要生成任何其它内容。
                    """}
                ],
            },
        ]
    )
    print("User instruction: ", ins_text)
    print("Chat response:", chat_response.choices[0].message.content)