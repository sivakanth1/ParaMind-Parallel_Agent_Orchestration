import asyncio
import time
from src.llm_clients import LLMClient
from src.agents import ParallelExecutor

async def benchmark():
    client = LLMClient()
    executor = ParallelExecutor(client)
    
    prompt = "What is AI?"
    models = ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]
    
    # Sequential execution
    start = time.time()
    results_seq = []
    for model in models:
        result = await client.call_llm(model, prompt)
        results_seq.append(result)
    sequential_time = time.time() - start
    
    # Parallel execution
    start = time.time()
    results_par = await executor.mode_a_execution(prompt, models)
    parallel_time = time.time() - start
    
    speedup = sequential_time / parallel_time
    
    print(f"Sequential: {sequential_time:.2f}s")
    print(f"Parallel: {parallel_time:.2f}s")
    print(f"Speedup: {speedup:.2f}x")
    
asyncio.run(benchmark())