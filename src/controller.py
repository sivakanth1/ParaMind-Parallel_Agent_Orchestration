"""
Improved Controller with ML-based decision making and comprehensive logging
"""
import json
import re
from typing import Dict, List
from loguru import logger
from src.llm_clients import LLMClient

# Configure controller-specific logging
logger.add("logs/controller_{time}.log", rotation="1 day", retention="7 days", level="DEBUG")

class Controller:
    """Enhanced controller with better decision logic"""
    
    def __init__(self, llm_client: LLMClient, model: str = "llama-3.3-70b-versatile"):
        self.client = llm_client
        self.model = model
        logger.info(f"Controller initialized with model: {model}")

    async def analyze_and_plan(self, user_prompt: str) -> Dict:
        """Analyzes user prompt and returns execution plan"""
        
        logger.info(f"🧠 Controller analyzing prompt: '{user_prompt[:100]}...'")
        
        # Try LLM-based decision first
        llm_decision = await self._llm_based_decision(user_prompt)
        
        if llm_decision and self._validate_plan(llm_decision):
            logger.success(f"✅ LLM-based decision: Mode {llm_decision['mode']}")
            return llm_decision
        
        # Fallback to semantic analysis
        logger.warning("⚠️ LLM decision failed validation, using semantic fallback")
        return self._semantic_fallback(user_prompt)
    
    async def _llm_based_decision(self, user_prompt: str) -> Dict:
        """Ask LLM to decide mode"""
        
        logger.debug("Requesting LLM-based mode decision")
        
        # Improved prompt with few-shot examples
        system_prompt = """You are an expert task analyzer. Decide execution mode and output ONLY valid JSON.

AVAILABLE MODELS (use ONLY these exact names):
- llama-3.3-70b-versatile
- llama-3.1-8b-instant

MODE A - Data Parallel (Same prompt, multiple models):
- Comparisons: "Compare X vs Y"
- Multiple perspectives: "What do experts think about..."
- Variations: "Generate 3 different versions of..."

MODE B - Instruction Parallel (Decompose into subtasks):
- Multi-component requests: "Plan trip with budget AND attractions AND food"
- Independent research: "Research history, current state, and future of X"
- Separate deliverables: "Create workout plan, meal plan, and schedule"
- Dependent tasks: "Research X then write a summary" (Task 2 depends on Task 1)

EXAMPLES - Use ONLY the available models listed above:

Input: "Compare Python vs JavaScript"
Output:
{
  "mode": "A",
  "reasoning": "Comparison task requires multiple perspectives",
  "plan": {
    "models": ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]
  }
}

Input: "Plan 3-day Tokyo trip with budget, attractions, and food"
Output:
{
  "mode": "B",
  "reasoning": "Request has 3 independent components that can run in parallel",
  "plan": {
    "subtasks": [
      {
        "id": 1,
        "description": "Create detailed 3-day budget breakdown for Tokyo trip",
        "model": "llama-3.3-70b-versatile",
        "depends_on": []
      },
      {
        "id": 2,
        "description": "List top attractions for a 3-day Tokyo itinerary with timing",
        "model": "llama-3.1-8b-instant",
        "depends_on": []
      },
      {
        "id": 3,
        "description": "Recommend restaurants and food experiences in Tokyo",
        "model": "llama-3.3-70b-versatile",
        "depends_on": []
      }
    ]
  }
}

Input: "Research the history of Bitcoin and then write a summary based on that research"
Output:
{
  "mode": "B",
  "reasoning": "Sequential task: Summary depends on Research",
  "plan": {
    "subtasks": [
      {
        "id": 1,
        "description": "Research the detailed history and origins of Bitcoin",
        "model": "llama-3.3-70b-versatile",
        "depends_on": []
      },
      {
        "id": 2,
        "description": "Write a concise summary of Bitcoin's history based on the research",
        "model": "llama-3.3-70b-versatile",
        "depends_on": [1]
      }
    ]
  }
}

CRITICAL RULES:
1. Output ONLY valid JSON with NO markdown, NO code blocks, NO explanations
2. ALWAYS include both "mode" and "plan" keys
3. Mode A: "plan" must have "models" array - use ONLY 2 models from the available list
4. Mode B: "plan" must have "subtasks" array with 2-5 subtasks
5. Each subtask MUST have: id, description, model, and depends_on (array of IDs)
6. NEVER invent model names - use ONLY: llama-3.3-70b-versatile, llama-3.1-8b-instant
7. If uncertain, choose Mode A (safer default)

Now analyze this request and respond with ONLY the JSON:"""

        result = await self.client.call_llm(
            model=self.model,
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=0.0,  # Changed from 0.1 to 0.0 for maximum consistency
            max_tokens=1000
        )
        
        if result["error"]:
            logger.error(f"❌ Controller LLM call failed: {result['error']}")
            return None
        
        # Parse JSON
        try:
            response_text = result["response"].strip()
            logger.debug(f"Raw LLM response: {response_text[:200]}...")
            
            # Clean markdown
            if "```" in response_text:
                json_match = re.search(r'```(?:json)?\s*(.*?)\s*```', response_text, re.DOTALL)
                if json_match:
                    response_text = json_match.group(1)
                    logger.debug("Removed markdown code blocks")
            
            # Extract JSON object
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                response_text = json_match.group(0)
            
            # Try to fix common JSON errors before parsing
            # Fix 1: Replace "config" with "plan" (LLM sometimes uses wrong key)
            response_text = response_text.replace('"config":', '"plan":')
            
            # Fix 2: Try to fix bracket mismatches
            # Count opening and closing brackets
            open_braces = response_text.count('{')
            close_braces = response_text.count('}')
            open_brackets = response_text.count('[')
            close_brackets = response_text.count(']')
            
            # Add missing closing brackets/braces
            if open_brackets > close_brackets:
                response_text = response_text.rstrip() + ']' * (open_brackets - close_brackets)
            if open_braces > close_braces:
                response_text = response_text.rstrip() + '}' * (open_braces - close_braces)
            
            logger.debug(f"Cleaned response: {response_text[:200]}...")
            
            plan = json.loads(response_text)
            plan["mode"] = plan["mode"].upper()
            
            # Validate and fix model names
            VALID_MODELS = ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]
            
            # Fix missing plan structure (LLM sometimes omits it)
            if "plan" not in plan:
                logger.warning("LLM response missing 'plan' key, adding default")
                plan["plan"] = {
                    "models": VALID_MODELS
                }
            
            # For Mode A: filter out invalid models
            if plan["mode"] == "A" and "models" in plan["plan"]:
                original_models = plan["plan"]["models"]
                valid_models = [m for m in original_models if m in VALID_MODELS]
                
                if len(valid_models) < len(original_models):
                    invalid = set(original_models) - set(valid_models)
                    logger.warning(f"Removed invalid models: {invalid}")
                
                # Ensure we have at least 2 models
                if len(valid_models) < 2:
                    valid_models = VALID_MODELS[:2]
                    logger.warning("Not enough valid models, using defaults")
                
                plan["plan"]["models"] = valid_models
            
            # For Mode B: validate subtask models
            elif plan["mode"] == "B" and "subtasks" in plan["plan"]:
                for subtask in plan["plan"]["subtasks"]:
                    if subtask.get("model") not in VALID_MODELS:
                        logger.warning(f"Invalid model in subtask {subtask['id']}, using default")
                        # Alternate between models
                        subtask["model"] = VALID_MODELS[subtask["id"] % 2]
            
            logger.success(f"✅ Successfully parsed LLM decision: Mode {plan['mode']}")
            logger.info(f"Reasoning: {plan.get('reasoning', 'No reasoning provided')}")
            
            return plan
            
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"JSON parsing failed: {e}. Attempting self-correction...")
            
            # Self-correction attempt
            try:
                correction_prompt = f"""The previous JSON was invalid. Fix it and return ONLY valid JSON.
                Error: {str(e)}
                Invalid JSON: {result['response']}"""
                
                correction_result = await self.client.call_llm(
                    model=self.model,
                    prompt=correction_prompt,
                    system_prompt="You are a JSON fixer. Return ONLY valid JSON.",
                    temperature=0.0
                )
                
                # Parse corrected response
                corrected_text = correction_result["response"].strip()
                if "```" in corrected_text:
                    json_match = re.search(r'```(?:json)?\s*(.*?)\s*```', corrected_text, re.DOTALL)
                    if json_match:
                        corrected_text = json_match.group(1)
                
                plan = json.loads(corrected_text)
                if self._validate_plan(plan):
                    logger.success("✅ JSON self-correction successful!")
                    return plan
            except Exception as correction_error:
                logger.error(f"Self-correction failed: {correction_error}")
            
            logger.error("Plan generation failed after correction, falling back to Mode A")
            return self._create_mode_a_plan(user_prompt)
            
        except Exception as e:
            logger.error(f"❌ LLM decision parsing failed: {e}")
            logger.debug(f"Failed response text: {response_text[:300]}")
            return None
    
    def _validate_plan(self, plan: Dict) -> bool:
        """Validate plan structure"""
        if not plan or "mode" not in plan:
            logger.warning("Plan validation failed: missing 'mode' key")
            return False
        
        # After our fix, plan key should exist, but double-check
        if "plan" not in plan:
            logger.warning("Plan validation failed: missing 'plan' key")
            return False
        
        if plan["mode"] == "A":
            # Check if models list exists and has at least 1 model (we can work with that)
            models = plan["plan"].get("models", [])
            is_valid = len(models) >= 1
            if is_valid:
                logger.debug(f"Mode A plan validated: {len(models)} model(s)")
            else:
                logger.warning("Mode A plan invalid: no models specified")
            return is_valid
        
        elif plan["mode"] == "B":
            subtasks = plan["plan"].get("subtasks", [])
            is_valid = 2 <= len(subtasks) <= 5
            if is_valid:
                # Validate DAG structure
                if self._validate_dag(subtasks):
                    logger.debug(f"Mode B plan validated: {len(subtasks)} subtasks with valid dependencies")
                    return True
                else:
                    logger.warning("Mode B plan invalid: circular or invalid dependencies")
                    return False
            else:
                logger.warning(f"Mode B plan invalid: {len(subtasks)} subtasks (need 2-5)")
            return is_valid
        
        logger.warning(f"Unknown mode: {plan['mode']}")
        return False

    def _validate_dag(self, subtasks: List[Dict]) -> bool:
        """Validate that dependencies form a valid DAG (no cycles, valid IDs)"""
        ids = {t["id"] for t in subtasks}
        
        # Check if all dependencies exist
        for task in subtasks:
            deps = task.get("depends_on", [])
            if not isinstance(deps, list):
                # Allow missing depends_on (assume empty) but if present must be list
                if deps is None:
                    continue
                return False
            for dep_id in deps:
                if dep_id not in ids:
                    logger.warning(f"Task {task['id']} depends on non-existent task {dep_id}")
                    return False
                if dep_id == task["id"]:
                    logger.warning(f"Task {task['id']} depends on itself")
                    return False

        # Check for cycles using DFS
        visited = set()
        path = set()
        
        def has_cycle(task_id):
            visited.add(task_id)
            path.add(task_id)
            
            task = next(t for t in subtasks if t["id"] == task_id)
            for dep_id in task.get("depends_on", []):
                if dep_id not in visited:
                    if has_cycle(dep_id):
                        return True
                elif dep_id in path:
                    return True
            
            path.remove(task_id)
            return False
            
        for task in subtasks:
            if task["id"] not in visited:
                if has_cycle(task["id"]):
                    logger.warning("Cycle detected in dependencies")
                    return False
                    
        return True
    
    def _semantic_fallback(self, user_prompt: str) -> Dict:
        """Improved fallback using semantic analysis"""
        
        logger.info("🔍 Using semantic fallback analysis")
        
        # Analyze prompt structure
        analysis = self._analyze_prompt_structure(user_prompt)
        
        logger.debug(f"Prompt analysis: {analysis}")
        
        if analysis["is_comparison"]:
            logger.info("✓ Detected comparison pattern → Mode A")
            return self._create_mode_a_plan("Detected comparison request")
        
        if analysis["component_count"] >= 2:
            logger.info(f"✓ Detected {analysis['component_count']} components → Mode B")
            return self._create_mode_b_plan(user_prompt, analysis)
        
        # Default to Mode A
        logger.info("→ Defaulting to Mode A (single task)")
        return self._create_mode_a_plan("Default: single task best suited for multiple perspectives")
    
    def _analyze_prompt_structure(self, prompt: str) -> Dict:
        """Analyze prompt to detect structure"""
        prompt_lower = prompt.lower()
        
        # Comparison indicators
        comparison_patterns = [
            r'\bcompare\b', r'\bversus\b', r'\bvs\.?\b',
            r'\bbetter\b', r'\bwhich\b', r'\bdifference\b',
            r'\bpros and cons\b', r'\badvantages?\b'
        ]
        is_comparison = any(re.search(p, prompt_lower) for p in comparison_patterns)
        
        # Component detection
        and_count = len(re.findall(r'\band\b', prompt_lower))
        comma_count = prompt_lower.count(',')
        
        # Task indicators
        task_verbs = ['plan', 'create', 'design', 'list', 'research', 
                      'analyze', 'develop', 'write', 'generate']
        task_count = sum(1 for verb in task_verbs if verb in prompt_lower)
        
        # Estimate independent components
        component_count = 0
        if and_count >= 2:
            component_count = and_count + 1
        elif comma_count >= 2:
            component_count = comma_count + 1
        elif task_count >= 2:
            component_count = task_count
        
        return {
            "is_comparison": is_comparison,
            "and_count": and_count,
            "comma_count": comma_count,
            "task_count": task_count,
            "component_count": component_count
        }
    
    def _create_mode_a_plan(self, reasoning: str) -> Dict:
        """Create Mode A plan"""
        plan = {
            "mode": "A",
            "reasoning": reasoning,
            "plan": {
                "models": ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]
            }
        }
        logger.info(f"📋 Created Mode A plan: {reasoning}")
        return plan
    
    def _create_mode_b_plan(self, prompt: str, analysis: Dict) -> Dict:
        """Create Mode B plan by decomposing prompt"""
        
        logger.debug(f"Attempting to decompose prompt based on analysis")
        
        # Try to split by 'and' or commas
        if analysis["and_count"] >= 2:
            parts = [p.strip() for p in re.split(r'\band\b', prompt, flags=re.IGNORECASE)]
            logger.debug(f"Split by 'and': {len(parts)} parts")
        elif analysis["comma_count"] >= 2:
            parts = [p.strip() for p in prompt.split(',')]
            logger.debug(f"Split by comma: {len(parts)} parts")
        else:
            logger.warning("Cannot decompose: insufficient separators")
            return self._create_mode_a_plan("Cannot decompose into independent tasks")
        
        # Clean and limit to 5 parts
        parts = [p for p in parts if len(p) > 10][:5]
        logger.debug(f"After cleaning: {len(parts)} valid parts")
        
        if len(parts) < 2:
            logger.warning("Decomposition resulted in < 2 subtasks")
            return self._create_mode_a_plan("Decomposition resulted in too few subtasks")
        
        # Create subtasks
        subtasks = []
        for i, part in enumerate(parts, 1):
            model = "llama-3.3-70b-versatile" if i % 2 == 1 else "llama-3.1-8b-instant"
            subtasks.append({
                "id": i,
                "description": part,
                "model": model,
                "depends_on": []
            })
            logger.debug(f"Subtask {i}: '{part[:50]}...' → {model}")
        
        plan = {
            "mode": "B",
            "reasoning": f"Detected {len(parts)} independent components",
            "plan": {
                "subtasks": subtasks
            }
        }
        
        logger.success(f"📋 Created Mode B plan with {len(subtasks)} subtasks")
        return plan