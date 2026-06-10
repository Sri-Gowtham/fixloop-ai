import asyncio
import os
import sys

# Remove any existing OPENAI or GEMINI keys to ensure Groq ONLY
os.environ.pop("OPENAI_API_KEY", None)
os.environ.pop("GEMINI_API_KEY", None)

from core.config import settings

# Force the config if they aren't fully stripped
settings.OPENAI_API_KEY = None
settings.GEMINI_API_KEY = None

from services.llm import generate_cluster_labels, generate_investigation, generate_recommendation

async def run_verification():
    print("Verifying Groq LLM Provider...")
    print(f"Provider: {settings.LLM_PROVIDER}")
    print(f"Model: {settings.GROQ_MODEL}")
    
    # 1. Cluster Labels
    print("\n--- Testing generate_cluster_labels ---")
    system_prompt = "You are an assistant. Return a JSON array with one object containing {'title': 'Test', 'summary': 'Test', 'severity': 'medium', 'confidence': 90.0, 'product_area': 'Other'}"
    user_prompt = "Generate test labels."
    cluster_res = await generate_cluster_labels(system_prompt, user_prompt)
    print("Cluster Labels Result:", cluster_res)
    assert "Test" in cluster_res, "Failed to get cluster labels"

    # 2. Investigation
    print("\n--- Testing generate_investigation ---")
    system_prompt_inv = "Return a JSON object with {'root_cause': 'Test Cause', 'confidence': 90.0, 'impact_level': 'high'}"
    user_prompt_inv = "Investigate."
    inv_res = await generate_investigation(system_prompt_inv, user_prompt_inv)
    print("Investigation Result:", inv_res)
    assert "Test Cause" in inv_res, "Failed to get investigation result"

    # 3. Recommendation
    print("\n--- Testing generate_recommendation ---")
    system_prompt_rec = "Return a JSON object with {'title': 'Test Fix', 'priority': 'high', 'engineering_effort': 'low'}"
    user_prompt_rec = "Recommend a fix."
    rec_res = await generate_recommendation(system_prompt_rec, user_prompt_rec)
    print("Recommendation Result:", rec_res)
    assert "Test Fix" in rec_res, "Failed to get recommendation result"

    print("\n✅ All verifications passed using Groq!")

if __name__ == "__main__":
    asyncio.run(run_verification())
