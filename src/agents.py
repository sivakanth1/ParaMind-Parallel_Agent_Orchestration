import asyncio
from typing import List, Dict

from src.llm_clients import LLMClient
from loguru import logger

logger.add("logs/agents_{time}.log", rotation="1 day", retention="7 days")

class ParallelExecutor:
    """Executes agents concurrently"""
    
    def __init__(self, llm_client: LLMClient, max_concurrent: int = 3):
        self.client = llm_client
        self.semaphore = asyncio.Semaphore(max_concurrent)
    
    async def execute_agent(
        self, 
        model: str, 
        prompt: str, 
        timeout: int = 30
    ) -> Dict:
        """Execute single agent with timeout and semaphore"""
        async with self.semaphore:
            try:
                return await asyncio.wait_for(
                    self.client.call_llm(model, prompt + "\n\nIMPORTANT: Format your response using Markdown. Use tables for structured data, bullet points for lists, and bold text for key information."),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                return {
                    "response": "",
                    "model": model,
                    "tokens": 0,
                    "latency": timeout,
                    "error": "Timeout"
                }
    
    async def mode_a_execution(self, prompt: str, models: List[str]) -> List[Dict]:
        """Execute same prompt across multiple models"""
        logger.info(f"⚡ Mode A: Executing prompt across {len(models)} models")
    
        tasks = [self.execute_agent(model, prompt) for model in models]
        results = await asyncio.gather(*tasks)
    
        success_count = len([r for r in results if not r["error"]])
        logger.success(f"✅ Mode A complete: {success_count}/{len(models)} successful")
    
        return results

    async def mode_b_execution(self, subtasks: List[Dict]) -> List[Dict]:
        """Execute different subtasks concurrently"""
        # Check for dependencies
        if any(t.get("depends_on") for t in subtasks):
            logger.info("🔄 Detected dependencies, switching to DAG execution")
            return await self.mode_b_execution_with_deps(subtasks)

        logger.info(f"⚡ Mode B: Executing {len(subtasks)} subtasks in parallel")
    
        tasks = [
            self.execute_agent(subtask["model"], subtask["description"])
            for subtask in subtasks
        ]
        results = await asyncio.gather(*tasks)
    
        success_count = len([r for r in results if not r["error"]])
        logger.success(f"✅ Mode B complete: {success_count}/{len(subtasks)} successful")
    
        return results

    async def mode_b_execution_with_deps(self, subtasks: List[Dict]) -> List[Dict]:
        """Execute subtasks respecting dependencies (DAG)"""
        logger.info(f"🔗 Mode B (DAG): Executing {len(subtasks)} subtasks with dependencies")
        
        try:
            layers = self._topological_sort(subtasks)
        except ValueError as e:
            logger.error(f"DAG Sort failed: {e}")
            return []

        results_map = {} # id -> result dict
        final_results = []
        failed_task_ids = set()
        
        for i, layer in enumerate(layers):
            logger.info(f"  ▶ Layer {i+1}/{len(layers)}: Executing tasks {[t['id'] for t in layer]}")
            
            # Filter out tasks with failed dependencies
            executable_tasks = []
            for task in layer:
                deps = task.get("depends_on", [])
                if any(dep_id in failed_task_ids for dep_id in deps):
                    logger.warning(f"  ⚠️ Skipping Task {task['id']} due to failed dependency")
                    skipped_result = {
                        "id": task["id"],
                        "description": task["description"],
                        "response": "Skipped due to failed dependency",
                        "error": "Dependency failed",
                        "model": task["model"],
                        "tokens": 0,
                        "latency": 0
                    }
                    results_map[task["id"]] = skipped_result
                    final_results.append(skipped_result)
                    failed_task_ids.add(task["id"])
                else:
                    executable_tasks.append(task)
            
            if not executable_tasks:
                continue
            
            # Prepare tasks for this layer
            layer_coroutines = []
            for task in executable_tasks:
                # Build context from dependencies
                context = self._build_context(task, results_map)
                prompt_with_context = f"{context}\n\nTask: {task['description']}" if context else task['description']
                
                layer_coroutines.append(
                    self.execute_agent(task["model"], prompt_with_context)
                )
            
            # Execute layer
            layer_results = await asyncio.gather(*layer_coroutines)
            
            # Store results
            for task, result in zip(executable_tasks, layer_results):
                # Add task metadata to result for tracking
                result["id"] = task["id"]
                result["task_id"] = task["id"]
                results_map[task["id"]] = result
                final_results.append(result)
                
                if result.get("error"):
                    logger.error(f"  ❌ Task {task['id']} failed: {result['error']}")
                    failed_task_ids.add(task["id"])
                else:
                    logger.success(f"  ✅ Task {task['id']} completed")
                
        success_count = len([r for r in final_results if not r["error"]])
        logger.success(f"✅ Mode B (DAG) complete: {success_count}/{len(subtasks)} successful")
        return final_results

    def _topological_sort(self, subtasks: List[Dict]) -> List[List[Dict]]:
        """Sort tasks into execution layers"""
        # Build graph
        graph = {t["id"]: set(t.get("depends_on", [])) for t in subtasks}
        task_map = {t["id"]: t for t in subtasks}
        
        layers = []
        completed = set()
        
        # Safety check for infinite loops
        max_loops = len(subtasks) + 2
        loops = 0
        
        while len(completed) < len(subtasks):
            loops += 1
            if loops > max_loops:
                raise ValueError("Circular dependency or unresolved dependency detected")

            # Find tasks with all dependencies met
            current_layer = []
            for task_id, deps in graph.items():
                if task_id not in completed and deps.issubset(completed):
                    current_layer.append(task_map[task_id])
            
            if not current_layer:
                raise ValueError("Circular dependency or unresolved dependency detected")
            
            layers.append(current_layer)
            completed.update(t["id"] for t in current_layer)
            
        return layers

    def _build_context(self, task: Dict, results_map: Dict) -> str:
        """Create context string from parent task results"""
        deps = task.get("depends_on", [])
        if not deps:
            return ""
            
        context_parts = ["### Previous Results:"]
        for dep_id in deps:
            if dep_id in results_map:
                parent_result = results_map[dep_id]["response"]
                # Truncate if too long (simple heuristic for now)
                if len(parent_result) > 2000:
                    parent_result = parent_result[:2000] + "...(truncated)"
                context_parts.append(f"From Task {dep_id}:\n{parent_result}\n")
        
        return "\n".join(context_parts)