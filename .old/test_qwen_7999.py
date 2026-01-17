from openai import OpenAI

# Initialize OpenAI client
openai_api_key = "EMPTY"
openai_api_base = "http://localhost:7999/v1"

client = OpenAI(
    api_key=openai_api_key,
    base_url=openai_api_base,
)

model_name = "/mnt/bit/wxc/projects/zhongche-llm/Qwen2.5-14B-Instruct"
question = "如何更换HP dv5-1125nr的键盘？"

print(f"Sending question: {question}")

try:
    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "user", "content": question}
        ],
        temperature=0.7
    )
    answer = response.choices[0].message.content
    print("\nAnswer:")
    print(answer)
except Exception as e:
    print(f"Error: {e}")
