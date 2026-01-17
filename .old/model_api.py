import base64
import torch
import clip
import json
import numpy as np
from openai import OpenAI

# ins_text = "What are the potential issues that might arise during the replacement of the rear facing camera on an iPad Mini 4 LTE?"
ins_text = "How to replace Toshiba Satellite A105-S4011 speakers?"
# ins_text = "What tools are necessary for disassembling the Nokia 2366i motherboard?" # good
# ins_text = "How to replace the Nook HD battery safely?" # good
# ins_text = "How to replace the keyboard on an HP dv5-1125nr?" # good
# -----------------CLIP load--------------------------------------
with torch.no_grad():
    clip_model, preprocess = clip.load("ViT-B/32", device='cuda')
    ins_text_token = clip.tokenize(ins_text).to('cuda')
    ins_text_embed = clip_model.encode_text(ins_text_token)
    ins_text_embed = ins_text_embed / ins_text_embed.norm(dim=-1, keepdim=True)
    print("ins_text_embed_shape:", ins_text_embed.shape)

    database = np.load("/mnt/bit/wxc/projects/zhongche-llm/embeddings/all_embeddings.npz")
    embeddings = database["embeddings"]
    # 转换为 PyTorch 张量
    embeddings_tensor = torch.from_numpy(embeddings).to('cuda')
    # print("embeddings_tensor shape:", embeddings_tensor.shape)
    similarities = torch.einsum("jk,ijk->ij", ins_text_embed, embeddings_tensor)
    # print("similarities shape:", similarities.shape)
    idx = torch.argmax(similarities, dim=0)
    idx_value = idx.item()
    print("Most similar instruction index:", idx_value)

with open("/mnt/bit/wxc/projects/zhongche-llm/data/train_data_all.json", "r", encoding="utf-8") as f:
    data = json.load(f)
    print("Retrievaled data: ", data[idx_value]['instruction'])
# Set OpenAI's API key and API base to use vLLM's API server.
openai_api_key = "EMPTY"
openai_api_base = "http://localhost:8000/v1"
client = OpenAI(
    api_key=openai_api_key,
    base_url=openai_api_base,
)

chat_response = client.chat.completions.create(
    model="/mnt/bit/wxc/projects/zhongche-llm/Qwen2.5-14B-Instruct",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {
            "role": "user",
            "content": [
                {"type": "text", "text": f"{ins_text} Please answer based on the reference document, and translate your answer in Complete Chinese sentence by sentence. Reference Document: {data[idx_value]['output']}"},
            ],
        },
    ],
    max_tokens=50000
)
print("Chat response:", chat_response.choices[0].message.content)