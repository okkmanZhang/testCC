import os
import json
from openai import AzureOpenAI
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

def test_azure_openai_connection():
    """
    Test script to verify connectivity with Azure OpenAI hosted in Sydney.
    This ensures compliance with Australian data residency requirements.
    """
    # Retrieve configuration from environment variables
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")

    # Basic validation of environment variables
    if not all([api_key, endpoint, deployment]):
        print("❌ Error: Missing Azure configuration in .env file.")
        print("Required: AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_DEPLOYMENT_NAME")
        return

    print(f"🚀 Connecting to Azure OpenAI (Australia East)...")
    print(f"Endpoint: {endpoint}")
    print(f"Deployment: {deployment}")

    # Initialize the Azure OpenAI client
    client = AzureOpenAI(
        api_key=api_key,
        api_version=api_version,
        azure_endpoint=endpoint
    )

    try:
        # Testing with a specific Australian Payroll scenario
        response = client.chat.completions.create(
            model=deployment, # In Azure, this must be your Deployment Name
            messages=[
                {
                    "role": "system", 
                    "content": "You are an Australian Payroll Expert. Return JSON only."
                },
                {
                    "role": "user", 
                    "content": "Analyze this task: 'Process the quarterly Superannuation guarantee for all employees'"
                }
            ],
            response_format={"type": "json_object"}
        )

        print("✅ Connection Successful!")
        print("🤖 AI Analysis Result (AU Context):")
        
        # Parse the JSON response
        result = json.loads(response.choices[0].message.content)
        print(json.dumps(result, indent=4))

    except Exception as e:
        print(f"❌ Connection Failed: {str(e)}")
        print("\nTroubleshooting Tips for Azure:")
        print("1. Check if AZURE_OPENAI_ENDPOINT starts with https://")
        print("2. Ensure AZURE_OPENAI_DEPLOYMENT_NAME is the name you gave to the model deployment, not the model name (e.g., 'gpt-4o').")
        print("3. Confirm your API Key is from the 'Keys and Endpoint' tab in Azure Portal.")

if __name__ == "__main__":
    test_azure_openai_connection()