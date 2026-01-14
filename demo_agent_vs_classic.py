"""
Day 8 Demo: Classic Chains vs Modern Agents

This script demonstrates the key differences between:
- Classic chain-based RAG (Days 1-7)
- Modern agent-based RAG (Day 8)

Run this after uploading a document to see how each approach handles different queries.
"""

import requests
import json
from typing import Dict, Any


BASE_URL = "http://localhost:8000"


def print_section(title: str):
    """Print formatted section header"""
    print("\n" + "=" * 70)
    print(f" {title}")
    print("=" * 70 + "\n")


def test_query(endpoint: str, question: str, label: str) -> Dict[str, Any]:
    """Test a query and print results"""
    print(f"\n🔹 {label}")
    print(f"Question: \"{question}\"")
    print(f"Endpoint: {endpoint}")
    print("-" * 70)

    response = requests.post(
        f"{BASE_URL}{endpoint}",
        json={"question": question}
    )

    if response.status_code == 200:
        data = response.json()
        print(f"✓ Answer: {data['answer'][:200]}...")
        print(f"✓ Sources: {len(data.get('sources', []))} documents retrieved")

        # Check if agent endpoint
        if "agent_used_retrieval" in data:
            print(f"✓ Agent used retrieval: {data['agent_used_retrieval']}")

        return data
    else:
        print(f"✗ Error: {response.status_code} - {response.text}")
        return {}


def main():
    """Run comparison demo"""

    print_section("Day 8 Demo: Classic Chains vs Modern Agents")

    print("""
This demo compares two RAG approaches:

1. Classic Chains (/chat/)
   - Fixed pipeline: ALWAYS retrieves documents first
   - Then generates answer
   - Simple, predictable, fast (1 LLM call)

2. Modern Agents (/agent/chat)
   - Dynamic: DECIDES whether to retrieve
   - Can skip retrieval for greetings
   - Flexible but slower (2+ LLM calls)
""")

    # Test 1: Greeting (should NOT need retrieval)
    print_section("Test 1: Greeting - No retrieval needed")

    print("Classic approach: Will retrieve anyway (wasteful)")
    test_query("/chat/", "Hello!", "Classic Chain")

    print("\nModern approach: Should skip retrieval")
    test_query("/agent/chat", "Hello!", "Modern Agent")

    # Test 2: Document question (NEEDS retrieval)
    print_section("Test 2: Document Question - Retrieval needed")

    print("Classic approach: Always retrieves (good for Q&A)")
    test_query("/chat/", "What is this document about?", "Classic Chain")

    print("\nModern approach: Agent decides to retrieve")
    test_query("/agent/chat", "What is this document about?", "Modern Agent")

    # Test 3: Follow-up
    print_section("Test 3: Follow-up Question")

    print("Classic approach:")
    test_query("/chat/", "Can you explain that more simply?", "Classic Chain")

    print("\nModern approach:")
    test_query("/agent/chat", "Can you explain that more simply?", "Modern Agent")

    # Get comparison
    print_section("Comparison Summary")

    response = requests.get(f"{BASE_URL}/agent/compare")
    if response.status_code == 200:
        comparison = response.json()
        print(json.dumps(comparison, indent=2))

    print_section("Conclusion")
    print("""
KEY DIFFERENCES:

Classic Chains:
✓ Faster (1 LLM call)
✓ Predictable
✓ Good for pure Q&A
✗ Wastes retrieval on greetings
✗ Fixed pipeline

Modern Agents:
✓ Intelligent (decides when to retrieve)
✓ Handles greetings efficiently
✓ More flexible
✗ Slower (2+ LLM calls)
✗ Less predictable

RECOMMENDATION:
- Start with classic chains for simple Q&A
- Migrate to agents when you need conversational flexibility
- Or use BOTH: /chat/ for docs, /agent/chat for conversations
""")


if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to API")
        print("Make sure the server is running: make dev")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
