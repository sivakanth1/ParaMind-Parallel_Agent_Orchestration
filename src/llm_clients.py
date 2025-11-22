import asyncio
from typing import Dict, Optional
from openai import AsyncOpenAI
from groq import AsyncGroq
import os
from src.cache import ResponseCache
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# Initialize cache
cache = ResponseCache()

# Configure logging
logger.add("logs/llm_calls_{time}.log", rotation="1 day", retention="7 days")

class LLMClient:
    """Unified interface for different LLM APIs"""
    
    def __init__(self):
        # Try loading from .env if not in environment
        if not os.getenv("OPENAI_API_KEY"):
            try:
                from dotenv import load_dotenv
                load_dotenv()
            except ImportError:
                logger.warning("python-dotenv not installed, skipping .env load")
            
        openai_key = os.getenv("OPENAI_API_KEY")
        groq_key = os.getenv("GROQ_API_KEY")
        
        if not openai_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        if not groq_key:
            raise ValueError("GROQ_API_KEY not found in environment variables")
            
        self.openai_client = AsyncOpenAI(api_key=openai_key)
        self.groq_client = AsyncGroq(api_key=groq_key)
        logger.info("LLMClient initialized successfully")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(Exception),
        reraise=True
    )
    async def call_llm(
        self, 
        model: str, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        use_cache: bool = True  # Add option to disable cache
    ) -> Dict:
        """
        Universal LLM caller with caching, error handling, and retries
        """
        import time
        
        # 🔍 CHECK CACHE FIRST (before making API call)
        if use_cache:
            cache_key_prompt = f"{system_prompt or ''}\n{prompt}"
            cached_result = cache.get(model, cache_key_prompt)
            if cached_result:
                logger.info(f"✅ Cache HIT for model={model}, prompt_length={len(prompt)}")
                return cached_result
            logger.debug(f"Cache MISS for model={model}")
        
        # Start timing
        start = time.time()
        logger.info(f"🚀 Calling {model} (prompt_length={len(prompt)}, temp={temperature})")
        
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            # Route to appropriate client
            if "gpt" in model.lower():
                response = await self.openai_client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                content = response.choices[0].message.content
                tokens = response.usage.total_tokens
            
            elif "llama" in model.lower() or "mixtral" in model.lower() or "gemma" in model.lower():
                response = await self.groq_client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                content = response.choices[0].message.content
                tokens = response.usage.total_tokens
            
            else:
                # Do not retry on configuration errors
                raise ValueError(f"Unsupported model: {model}")
            
            latency = time.time() - start
            
            result = {
                "response": content,
                "model": model,
                "tokens": tokens,
                "latency": round(latency, 2),
                "error": None
            }
            
            # 💾 SAVE TO CACHE (after successful call)
            if use_cache:
                cache_key_prompt = f"{system_prompt or ''}\n{prompt}"
                cache.set(model, cache_key_prompt, result)
                logger.debug(f"Cached result for {model}")
            
            logger.success(f"✅ {model} responded in {latency:.2f}s, {tokens} tokens")
            return result
        
        except ValueError:
            # Re-raise configuration errors immediately without retry
            raise
        except Exception as e:
            latency = time.time() - start
            logger.warning(f"⚠️ {model} failed after {latency:.2f}s: {str(e)} - Retrying...")
            raise e # Let tenacity handle the retry