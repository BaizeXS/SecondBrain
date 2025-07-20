#!/usr/bin/env python3
"""Test OpenRouter API connection and models."""

import asyncio
import os
import sys
from typing import Any

import httpx
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

if not OPENROUTER_API_KEY:
    print("❌ Error: OPENROUTER_API_KEY not found in environment variables")
    sys.exit(1)

# Free models from the backend code
FREE_MODELS = [
    "qwen/qwen3-235b-a22b:free",
    "qwen/qwen3-30b-a3b:free",
    "qwen/qwen3-32b:free",
    "deepseek/deepseek-r1-0528-qwen3-8b:free",
    "deepseek/deepseek-r1-0528:free",
    "deepseek/deepseek-chat-v3-0324:free",
    "meta-llama/llama-4-maverick:free",
    "meta-llama/llama-4-scout:free",
    "moonshotai/kimi-k2:free",
]


async def test_openrouter_connection():
    """Test basic connection to OpenRouter."""
    print("🔍 Testing OpenRouter connection...")

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                "https://openrouter.ai/api/v1/models",
                headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}"},
            )

            if response.status_code == 200:
                print("✅ Successfully connected to OpenRouter API")
                return True
            else:
                print(f"❌ Failed to connect: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ Connection error: {e}")
            return False


async def test_free_model(model_id: str) -> dict[str, Any]:
    """Test a specific free model."""
    print(f"\n🧪 Testing model: {model_id}")

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model_id,
                    "messages": [{"role": "user", "content": "Say 'Hello' in one word"}],
                    "max_tokens": 10,
                    "temperature": 0.5,
                },
            )

            if response.status_code == 200:
                data = response.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                print(f"  ✅ Model available - Response: {content.strip()}")
                return {"status": "available", "response": content}
            else:
                error_data = response.json()
                error_msg = error_data.get("error", {}).get("message", str(error_data))
                print(f"  ❌ Model unavailable - {error_msg}")
                return {"status": "unavailable", "error": error_msg}
        except Exception as e:
            print(f"  ❌ Error: {e}")
            return {"status": "error", "error": str(e)}


async def test_auto_model():
    """Test the auto routing model."""
    print("\n🤖 Testing OpenRouter Auto model...")

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "openrouter/auto",
                    "messages": [{"role": "user", "content": "What's 2+2? Answer in one number only."}],
                    "max_tokens": 10,
                },
            )

            if response.status_code == 200:
                data = response.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                model_used = data.get("model", "unknown")
                print(f"  ✅ Auto routing works - Used model: {model_used}")
                print(f"  Response: {content.strip()}")
            else:
                print(f"  ❌ Auto routing failed: {response.text}")
        except Exception as e:
            print(f"  ❌ Error: {e}")


async def main():
    """Run all tests."""
    print("🚀 OpenRouter Configuration Test")
    print("=" * 50)

    # Test connection
    if not await test_openrouter_connection():
        return

    # Test auto model
    await test_auto_model()

    # Test free models
    print("\n📊 Testing Free Models")
    print("-" * 50)

    results = {"available": [], "unavailable": []}

    for model in FREE_MODELS:
        result = await test_free_model(model)
        if result["status"] == "available":
            results["available"].append(model)
        else:
            results["unavailable"].append(model)

        # Small delay to avoid rate limiting
        await asyncio.sleep(1)

    # Summary
    print("\n📋 Test Summary")
    print("=" * 50)
    print(f"✅ Available models ({len(results['available'])}):")
    for model in results["available"]:
        print(f"  - {model}")

    if results["unavailable"]:
        print(f"\n❌ Unavailable models ({len(results['unavailable'])}):")
        for model in results["unavailable"]:
            print(f"  - {model}")

    print("\n💡 Recommendations:")
    if results["available"]:
        print(f"  - Use these free models for testing: {', '.join(results['available'][:3])}")
    print("  - Use 'openrouter/auto' for automatic model selection")
    print("  - Check https://openrouter.ai/models for the latest model list")


if __name__ == "__main__":
    asyncio.run(main())

