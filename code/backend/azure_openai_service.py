import os
import json
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()

class AIService:
    """
    Handles task analysis using Azure OpenAI (Sydney).
    Ensures payroll logic adheres to Australian standards.
    """
    def __init__(self):
        self.client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        )
        self.deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")

    def analyze_task(self, user_input: str):
        system_prompt = """
        You are an Australian Payroll Expert. 
        Categorise the task and determine priority.
        Categories: [Super, PAYG, Compliance, Leave, General]
        Priorities: [High, Medium, Low]
        
        Note: Set High priority for STP, Super, or ATO deadlines.
        Return ONLY a JSON object.
        """
        try:
            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_input}
                ],
                response_format={"type": "json_object"}
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"AI Service Error: {e}")
            return None