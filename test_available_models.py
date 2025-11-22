"""Test which models are available with your API keys"""
import asyncio
import os
from dotenv import load_dotenv
from openai import AsyncOpenAI
from groq import AsyncGroq

load_dotenv()

async def test_openai_models():
    """Test OpenAI models"""
    print("🔍 Testing OpenAI Models...")
    print("-" * 50)
    
    client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    openai_models = [
        "gpt-4-turbo-preview",
        "gpt-4",
        "gpt-3.5-turbo",
        "gpt-4o-mini",
    ]
    
    for model in openai_models:
        try:
            response = await client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=10
            )
            print(f"✅ {model}: WORKS")
        except Exception as e:
            error_msg = str(e)
            if "quota" in error_msg.lower():
                print(f"❌ {model}: NO CREDITS (quota exceeded)")
            elif "does not exist" in error_msg.lower():
                print(f"❌ {model}: NOT AVAILABLE")
            else:
                print(f"❌ {model}: {error_msg[:50]}")
    print()

async def test_groq_models():
    """Test Groq models"""
    print("🔍 Testing Groq Models...")
    print("-" * 50)
    
    client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))
    
    groq_models = [
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
        "llama-3.1-70b-versatile",  # Deprecated
        "gemma2-9b-it",
        "mixtral-8x7b-32768",
    ]
    
    for model in groq_models:
        try:
            response = await client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=10
            )
            print(f"✅ {model}: WORKS")
        except Exception as e:
            error_msg = str(e)
            if "decommissioned" in error_msg.lower():
                print(f"❌ {model}: DEPRECATED")
            elif "does not exist" in error_msg.lower():
                print(f"❌ {model}: NOT AVAILABLE")
            else:
                print(f"❌ {model}: {error_msg[:50]}")
    print()

async def main():
    print("\n" + "="*50)
    print("  MODEL AVAILABILITY TEST")
    print("="*50 + "\n")
    
    await test_openai_models()
    await test_groq_models()
    
    print("="*50)
    print("\n💡 Recommendation:")
    print("   - If OpenAI models show 'NO CREDITS', add billing:")
    print("     https://platform.openai.com/settings/organization/billing")
    print("   - Use working Groq models (they're FREE!)")
    print("   - Update config/settings.py with working models only")
    print("="*50 + "\n")

if __name__ == "__main__":
    asyncio.run(main())