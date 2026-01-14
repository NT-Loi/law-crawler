from openai import OpenAI
import os
from dotenv import load_dotenv
load_dotenv()
client = OpenAI(
    base_url=os.getenv("URL"),
    api_key=os.getenv("API_KEY"),
)

model_name = os.getenv("CHAT_MODEL")

def chat_with_model(prompt):
    print(f"Sending request to {model_name}...")
    try:
        completion = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2048
        )
        print("\nResponse:")
        print(completion.choices[0].message.content)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    prompt = "Nghĩa vụ quân sự có phải bắt buộc không?"
    chat_with_model(prompt)