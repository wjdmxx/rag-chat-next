import json
import os
import time
from openai import OpenAI

# Initialize OpenAI client
openai_api_key = "EMPTY"
openai_api_base = "http://localhost:7999/v1"

client = OpenAI(
    api_key=openai_api_key,
    base_url=openai_api_base,
)

model_name = "/mnt/bit/wxc/projects/zhongche-llm/Qwen2.5-14B-Instruct"
input_file = "/mnt/bit/liyuanxi/projects/zhongche/rag-chat-next/repair_questions_100.txt"
output_file = "/mnt/bit/liyuanxi/projects/zhongche/rag-chat-next/repair_questions_output.json"

results = []

# Read questions
print(f"Reading questions from {input_file}...")
try:
    with open(input_file, "r", encoding="utf-8") as f:
        questions = [line.strip() for line in f if line.strip()]
except FileNotFoundError:
    print(f"Error: {input_file} not found.")
    exit(1)

print(f"Found {len(questions)} questions. Starting processing...")

for i, question in enumerate(questions):
    print(f"[{i+1}/{len(questions)}] Processing: {question}")
    start_time = time.time()
    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "user", "content": question}
            ],
            temperature=0.7
        )
        answer = response.choices[0].message.content
        elapsed = time.time() - start_time
        
        results.append({
            "id": i + 1,
            "question": question,
            "answer": answer
        })
        print(f"  -> Completed in {elapsed:.2f}s")
        
    except Exception as e:
        print(f"  -> Error: {e}")
        results.append({
            "id": i + 1,
            "question": question,
            "answer": f"Error: {str(e)}"
        })

    # Save periodically (every 10 questions) to avoid total data loss on crash
    if (i + 1) % 10 == 0:
        print(f"Saving progress to {output_file}...")
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=4)

# Final save
print(f"Finished processing. Saving final results to {output_file}...")
try:
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=4)
    print("Done.")
except Exception as e:
    print(f"Error saving results: {e}")
