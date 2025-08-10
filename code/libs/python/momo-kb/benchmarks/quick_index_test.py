"""
Quick test to verify indexing performance improvements.
"""

import asyncio
import time
from momo_kb import KnowledgeBase, Node, Edge


async def quick_index_test():
    """Quick test of indexed performance."""
    print("🚀 Quick Index Performance Test")
    print("=" * 40)

    async with KnowledgeBase() as kb:
        # Add test data
        print("📊 Adding 1000 nodes...")
        for i in range(1000):
            await kb.insert_node(
                Node(
                    label="TestNode",
                    properties={"category": f"cat_{i % 10}", "value": i},
                )
            )

        # Test label query
        start = time.perf_counter()
        result = await kb.query_nodes(label="TestNode")
        label_time = (time.perf_counter() - start) * 1000

        # Test property query
        start = time.perf_counter()
        result = await kb.query_nodes(properties={"category": "cat_5"})
        prop_time = (time.perf_counter() - start) * 1000

        # Test specific value query
        start = time.perf_counter()
        result = await kb.query_nodes(properties={"value": 500})
        value_time = (time.perf_counter() - start) * 1000

        print(f"✅ Label query (1000 results): {label_time:.2f}ms")
        print(f"✅ Property query (100 results): {prop_time:.2f}ms")
        print(f"✅ Value query (1 result): {value_time:.2f}ms")

        # Performance assessment
        if label_time < 10 and prop_time < 5 and value_time < 2:
            print("🎉 EXCELLENT: Indexing is working well!")
        elif label_time < 50 and prop_time < 20 and value_time < 10:
            print("✅ GOOD: Indexing provides decent performance")
        else:
            print("⚠️  NEEDS WORK: Indexing not providing expected speedup")


if __name__ == "__main__":
    asyncio.run(quick_index_test())
