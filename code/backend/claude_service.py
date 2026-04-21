import os
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

# 初始化客户端
client = Anthropic(api_key=os.getenv(ANTHROPIC_API_KEY))

def analyze_task_with_claude(user_input: str):
    # 针对澳洲薪资市场的 System Prompt
    system_msg = """
    You are an expert Australian Payroll Assistant. 
    Analyze the user's input and return a JSON object.
    
    Categories: [Super, PAYG, Compliance, Leave, General]
    Priority: [High, Medium, Low]
    
    Constraint: If the task relates to 'Single Touch Payroll (STP)' or 'Tax Deadline', 
    set priority to High. Use Australian English.
    """

    try:
        message = client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=1000,
            temperature=0, # 财务任务需要 0 随机性，保证稳定性
            system=system_msg,
            messages=[
                {
                    "role": "user", 
                    "content": f"Parse this task: {user_input}. Return ONLY JSON."
                }
            ]
        )
        
        # Claude 返回的是 Text 块，我们需要解析它
        import json
        return json.loads(message.content[0].text)
    except Exception as e:
        print(f"Claude API Error: {e}")
        return None