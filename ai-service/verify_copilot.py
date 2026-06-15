import asyncio
import os
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_copilot_endpoint():
    print("Testing POST /ai/copilot")
    response = client.post(
        "/ai/copilot",
        json={"cluster_id": "test-cluster-id", "message": "What is the root cause?"}
    )
    print("Response Status:", response.status_code)
    try:
        print("Response Body:", response.json())
    except Exception as e:
        print("Failed to parse JSON:", e, response.text)

if __name__ == "__main__":
    test_copilot_endpoint()
