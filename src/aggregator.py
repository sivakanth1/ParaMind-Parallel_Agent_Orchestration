from typing import List, Dict
from src.llm_clients import LLMClient

class Aggregator:
    """Aggregates results from parallel agents"""
    
    def __init__(self, llm_client: LLMClient):
        self.client = llm_client
    
    def list_all(self, results: List[Dict]) -> str:
        """Simply list all responses with labels"""
        output = []
        for i, result in enumerate(results, 1):
            if result["error"]:
                output.append(f"**Agent {i} ({result['model']}):** Error - {result['error']}")
            else:
                output.append(f"**Agent {i} ({result['model']}):**\n{result['response']}\n")
        return "\n\n".join(output)
    
    async def summarize(self, results: List[Dict]) -> str:
        """Use LLM to synthesize all responses"""
        valid_responses = [r for r in results if not r["error"]]
        
        if not valid_responses:
            return "All agents failed."
        
        combined = "\n\n".join([
            f"Model {r['model']}: {r['response']}" 
            for r in valid_responses
        ])
        
        summary_prompt = f"""Synthesize these responses into a coherent summary:

{combined}

Provide a comprehensive summary that captures key insights from all models."""
        
        result = await self.client.call_llm(
           # model="gpt-3.5-turbo",
            model="llama-3.1-8b-instant",
            prompt=summary_prompt,
            max_tokens=500
        )
        
        return result["response"]
    
    async def best_of_n(self, results: List[Dict], original_prompt: str) -> str:
        """Select best response using judge LLM"""
        valid_responses = [r for r in results if not r["error"]]
        
        if not valid_responses:
            return "All agents failed."
        
        if len(valid_responses) == 1:
            return valid_responses[0]["response"]
        
        judge_prompt = f"""Original Question: {original_prompt}

Evaluate these responses and return ONLY the number (1, 2, 3, etc.) of the best response:

{chr(10).join([f"{i+1}. {r['response']}" for i, r in enumerate(valid_responses)])}

Best response number:"""
        
        result = await self.client.call_llm(
            # model="gpt-3.5-turbo",
            model="llama-3.1-8b-instant",
            prompt=judge_prompt,
            temperature=0.1,
            max_tokens=10
        )
        
        try:
            best_idx = int(result["response"].strip()) - 1
            return valid_responses[best_idx]["response"]
        except:
            return valid_responses[0]["response"]