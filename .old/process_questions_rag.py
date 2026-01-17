import json
import requests
import time
from openai import OpenAI

# Configuration
RAG_SERVICE_URL = "http://127.0.0.1:8001/retrieve"
LLM_API_BASE = "http://localhost:8000/v1" 
LLM_API_KEY = "EMPTY"
MODEL_NAME = "/mnt/bit/wxc/projects/zhongche-llm/Qwen2.5-14B-Instruct"
INPUT_FILE = "/mnt/bit/liyuanxi/projects/zhongche/rag-chat-next/repair_questions_100.txt"
OUTPUT_FILE = "/mnt/bit/liyuanxi/projects/zhongche/rag-chat-next/repair_questions_rag_output.json"

client = OpenAI(api_key=LLM_API_KEY, base_url=LLM_API_BASE)

def get_rag_context(text):
    try:
        response = requests.post(RAG_SERVICE_URL, json={"text": text})
        if response.status_code == 200:
            return response.json()
        else:
            print(f"RAG Error {response.status_code}: {response.text}")
            return None
    except Exception as e:
        print(f"RAG Connection Error: {e}")
        return None

def process_questions():
    results = []
    
    print(f"Reading questions from {INPUT_FILE}...")
    try:
        with open(INPUT_FILE, "r", encoding="utf-8") as f:
            questions = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"Error: {INPUT_FILE} not found.")
        return

    print(f"Found {len(questions)} questions. Starting processing...")

    for i, question in enumerate(questions):
        print(f"[{i+1}/{len(questions)}] Processing: {question}")
        start_time = time.time()
        
        # 1. Call RAG Service
        rag_data = get_rag_context(question)
        reference_doc = rag_data.get("document", "") if rag_data else ""
        
        # 2. Construct Prompt (Matching route.ts)
        if reference_doc:
            prompt_content = f"""{question} Please answer based on the reference document, and translate your answer in Complete Chinese sentence by sentence.
请严格按照以下格式回答，并根据提问内容回答。如提问使用了什么工具，则只回答工具部分。如提问如何维修，请将工具和维修步骤均回答。工具和步骤数量根据参考文档中的信息确定。
回答格式：工具部分：每个工具之间使用顿号连接，不要出现json的格式。步骤部分，使用阿拉伯数字，如第1步。每行一个步骤。见下。
以下是需要的工具。
工具：{{工具1}}、{{工具2}}、{{工具3}}……
以下是具体实施步骤。
步骤：
- 第1步：{{步骤1}}
- 第2步：{{步骤2}}
……

Reference Document: {reference_doc}"""
        else:
            prompt_content = question
            print("  -> Warning: No reference document found.")

        # 3. Call LLM
        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt_content}
                ],
                max_tokens=50000, # Adjusted from 50000 to a more reasonable limit for output, or keep high if needed
                temperature=0.7
            )
            answer = response.choices[0].message.content
            elapsed = time.time() - start_time
            
            results.append({
                "id": i + 1,
                "question": question,
                "rag_doc": reference_doc,
                "answer": answer
            })
            print(f"  -> Completed in {elapsed:.2f}s")
            
        except Exception as e:
            print(f"  -> LLM Error: {e}")
            results.append({
                "id": i + 1,
                "question": question,
                "rag_doc": reference_doc,
                "answer": f"Error: {str(e)}"
            })

        # Save periodically
        if (i + 1) % 10 == 0:
            print(f"Saving progress to {OUTPUT_FILE}...")
            with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                json.dump(results, f, ensure_ascii=False, indent=4)

    # Final save
    print(f"Finished processing. Saving final results to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=4)
    print("Done.")

if __name__ == "__main__":
    process_questions()
