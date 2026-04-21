import os
from anthropic import Anthropic
from dotenv import load_dotenv

# 加载配置
load_dotenv()

def test_claude_connection():
    api_key = os.getenv("ANTHROPIC_API_KEY")
    
    if not api_key:
        print("❌ 错误: 未在 .env 文件中找到 ANTHROPIC_API_KEY")
        return

    print(f"🚀 正在尝试连接 Anthropic (API Key 前缀: {api_key[:8]}...)")
    
    client = Anthropic(api_key=api_key)

    try:
        # 发送一个针对澳洲薪资逻辑的测试指令
        message = client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=300,
            system="You are an expert Australian Payroll consultant. Return JSON only.",
            messages=[
                {
                    "role": "user", 
                    "content": "Parse this task: 'Pay superannuation for Q1 before the deadline'"
                }
            ]
        )
        print("✅ 连接成功！")
        print("🤖 Claude 的分析结果:")
        print(message.content[0].text)
        
    except Exception as e:
        print(f"❌ 连接失败: {str(e)}")

if __name__ == "__main__":
    test_claude_connection()