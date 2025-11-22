import streamlit as st
import asyncio
import os
import sys
from pathlib import Path
from loguru import logger
import sys

# Configure main app logging
logger.remove()  # Remove default handler
logger.add(sys.stderr, level="INFO")  # Console output
logger.add("logs/app_{time}.log", rotation="1 day", retention="7 days")  # File output

logger.info("🚀 ParaMind application started")

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
from dotenv import load_dotenv
load_dotenv(project_root / '.env')

# Check API keys first
openai_key = os.getenv("OPENAI_API_KEY")
groq_key = os.getenv("GROQ_API_KEY")

st.set_page_config(
    page_title="ParaMind - Parallel Agent Orchestration",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 ParaMind: Dynamic Parallel Agentic Orchestration")
st.caption("Intelligent multi-agent system with adaptive parallelization")

# Check for API keys
if not openai_key or not groq_key:
    st.error("⚠️ API Keys Missing!")
    st.write("Please add your API keys to the `.env` file:")
    st.code("""
OPENAI_API_KEY=sk-proj-your-key-here
GROQ_API_KEY=gsk_your-key-here
    """)
    st.info("Get keys from:\n- OpenAI: https://platform.openai.com/api-keys\n- Groq: https://console.groq.com/keys")
    st.stop()

# Import after API key check
try:
    from src.llm_clients import LLMClient
    from src.controller import Controller
    from src.agents import ParallelExecutor
    from src.aggregator import Aggregator
except ImportError as e:
    st.error(f"Import error: {e}")
    st.write("Make sure you ran: `pip install -e .` from the project root")
    st.stop()

# Initialize clients (cached)
@st.cache_resource
def get_clients():
    try:
        llm_client = LLMClient()
        controller = Controller(llm_client)
        executor = ParallelExecutor(llm_client)
        aggregator = Aggregator(llm_client)
        return llm_client, controller, executor, aggregator
    except Exception as e:
        st.error(f"Failed to initialize clients: {e}")
        return None, None, None, None

llm_client, controller, executor, aggregator = get_clients()

if not all([llm_client, controller, executor, aggregator]):
    st.stop()

# Sidebar configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    aggregation_method = st.selectbox(
        "Aggregation Method",
        ["List All", "Summarize", "Best of N"]
    )
    
    st.divider()
    st.markdown("### 📊 Execution Modes")
    st.info("**Mode A:** Data-parallel (same prompt, multiple models)")
    st.info("**Mode B:** Instruction-parallel (decomposed subtasks)")
    
    st.divider()
    st.markdown("### 🧪 Example Prompts")
    st.code("Compare Python vs JavaScript for backend", language=None)
    st.code("Plan a 3-day Tokyo trip with budget and itinerary", language=None)

# Main interface
user_prompt = st.text_area(
    "Enter your request:",
    placeholder="e.g., 'Compare Python vs JavaScript for backend development'",
    height=100
)

if st.button("🚀 Execute", type="primary"):
    if not user_prompt:
        st.warning("Please enter a prompt")
    else:
        logger.info(f"User submitted prompt: '{user_prompt[:100]}'")
        logger.info(f"Aggregation method: {aggregation_method}")
        try:
            with st.spinner("🧠 Analyzing request..."):
                # Run async code
                plan = asyncio.run(controller.analyze_and_plan(user_prompt))
            logger.info(f"Execution plan: Mode {plan['mode']}")
            
            # Display plan
            st.subheader(f"📋 Execution Plan: Mode {plan['mode']}")
            st.write(plan["reasoning"])
            
            with st.spinner("⚡ Executing agents in parallel..."):
                if plan["mode"] == "A":
                    results = asyncio.run(
                        executor.mode_a_execution(
                            user_prompt, 
                            plan["plan"]["models"]
                        )
                    )
                else:
                    results = asyncio.run(
                        executor.mode_b_execution(
                            plan["plan"]["subtasks"]
                        )
                    )
            
            # Aggregate results
            st.subheader("📤 Results")
            
            if aggregation_method == "List All":
                output = aggregator.list_all(results)
                st.markdown(output)
            
            elif aggregation_method == "Summarize":
                with st.spinner("📝 Synthesizing responses..."):
                    output = asyncio.run(aggregator.summarize(results))
                st.markdown(output)
            
            elif aggregation_method == "Best of N":
                with st.spinner("🏆 Selecting best response..."):
                    output = asyncio.run(
                        aggregator.best_of_n(results, user_prompt)
                    )
                st.markdown(output)
            
            # Metrics
            st.subheader("📊 Metrics")
            col1, col2, col3, col4 = st.columns(4)
            
            total_latency = max([r["latency"] for r in results])
            total_tokens = sum([r["tokens"] for r in results])
            success_rate = len([r for r in results if not r["error"]]) / len(results) * 100
            failed_agents = len([r for r in results if r["error"]])
            
            col1.metric("Total Latency", f"{total_latency:.2f}s")
            col2.metric("Total Tokens", total_tokens)
            col3.metric("Success Rate", f"{success_rate:.0f}%")
            col4.metric("Failed Agents", failed_agents)
            
            # Show detailed results in expander
            with st.expander("📋 View Detailed Results"):
                for i, result in enumerate(results, 1):
                    st.markdown(f"**Agent {i} ({result['model']})**")
                    st.write(f"- Latency: {result['latency']}s")
                    st.write(f"- Tokens: {result['tokens']}")
                    if result['error']:
                        st.error(f"Error: {result['error']}")
                    else:
                        st.success("Success")
                    st.divider()
            
            def calculate_cost(results):
                """Estimate cost based on tokens (Groq is free, but good for comparison)"""
                total_cost = 0
                for r in results:
                    if "gpt" in r["model"].lower():
                        total_cost += (r["tokens"] / 1_000_000) * 0.50
                return total_cost
            
            cost = calculate_cost(results)
            st.write(f"💰 Estimated cost: ${cost:.4f}")
            logger.success(f"Request completed successfully in {total_latency:.2f}s")
        
        except Exception as e:
            logger.error(f"Request failed: {str(e)}")
            st.error(f"Execution failed: {str(e)}")
            st.exception(e)