# ParaMind: Dynamic Parallel Agentic Orchestration

**ParaMind** is an advanced intelligent orchestration engine designed to overcome the limitations of single-agent LLM interactions. By leveraging **parallel processing** and **dynamic task decomposition**, ParaMind transforms slow, serial interactions into fast, concurrent workflows.

![ParaMind Project Mind Map](assets/project_mindmap.png)

## 🚀 Key Features

- **Mode A (Data-Parallel)**: Execute the same prompt across multiple LLM models simultaneously for comparison or consensus.
- **Mode B (Task-Parallel)**: Decompose complex tasks into independent or dependent subtasks (DAG execution).
- **Smart Controller**: AI-powered decision engine that chooses the optimal execution mode using LLM reasoning or semantic fallback.
- **Dependency Management**: Automatically handles task dependencies in Mode B, executing tasks in topological order.
- **Robustness**: Built-in retries, error handling, and partial failure recovery.
- **High Performance**: Caching layer and parallel execution deliver 2x-5x speedups (up to 100x with cache).
- **Modern Web UI**: Fast, responsive interface built with FastAPI and Vanilla JS.

## 🏗️ System Architecture

The project follows a modern, decoupled client-server architecture.

```mermaid
graph TD
    User[User Interface] <-->|REST API| API[FastAPI Backend]
    
    subgraph "Backend Core"
        API --> Controller[Smart Controller]
        API --> Executor[Parallel Executor]
        API --> Aggregator[Result Aggregator]
        
        Controller -->|Analyze & Plan| LLM[LLM Client]
        Executor -->|Execute Tasks| LLM
        Aggregator -->|Synthesize| LLM
        
        LLM <-->|Cache Hit/Miss| Cache[Response Cache]
        LLM <-->|External API| Groq[Groq API]
        LLM <-->|External API| OpenAI[OpenAI API]
    end
```

### Component Analysis

#### 1. The Controller (`src/controller.py`)
The "Brain" of the operation. It analyzes user intent using **Llama 3.3 70B** to generate a JSON execution plan. It features:
*   **LLM Decision:** Uses few-shot prompting to decide between Mode A and Mode B.
*   **Self-Correction:** Automatically fixes invalid JSON output from the LLM.
*   **Semantic Fallback:** Uses regex-based heuristics if the LLM fails.

#### 2. The Executor (`src/agents.py`)
The "Muscle" that executes the plan.
*   **Concurrency:** Built on Python's `asyncio` for non-blocking parallel execution.
*   **DAG Logic:** Uses **Topological Sort** to organize Mode B subtasks into "execution layers".
*   **Dynamic Refinement:** Automatically re-runs tasks if the output is too short or apologetic.

#### 3. The Aggregator (`src/aggregator.py`)
The "Synthesizer". Combines individual agent outputs into a single, coherent response using a fast summarization model (**Llama 3.1 8B**).

#### 4. Infrastructure (`src/llm_clients.py`)
*   **Unified Client:** Wrapper for Groq and OpenAI APIs.
*   **Caching:** File-based caching (`.cache/`) drastically reduces latency and cost.
*   **Resilience:** Implements retries and rate limiting via `tenacity` and `asyncio.Semaphore`.

## 📂 Project Structure

```
ParaMind-Parallel_Agent_Orchestration/
├── src/
│   ├── api.py             # FastAPI backend entry point
│   ├── controller.py      # Mode decision & planning logic
│   ├── agents.py          # Parallel & DAG execution engine
│   ├── llm_clients.py     # API wrappers with caching/retries
│   ├── aggregator.py      # Result synthesis logic
│   └── cache.py           # File-based caching implementation
├── ui/
│   ├── index.html         # Main Single Page Application (SPA)
│   ├── style.css          # Custom CSS styling
│   └── app.js             # Frontend logic (Fetch API, DOM manipulation)
├── benchmarks/
│   ├── run_eval.py        # Automated benchmark runner
│   ├── analyze_results.py # Result analysis and reporting
│   └── prompts.json       # Test cases
├── tests/
│   ├── test_dependencies.py
│   └── test_robustness.py
├── config/                # Configuration files
├── logs/                  # Application logs
├── .env                   # API keys (not in git)
└── README.md
```

## 📊 Benchmark Results

Latest run (Dec 2, 2025):
*   **Success Rate:** 100% (25/25 prompts)
*   **Mode Accuracy:** 100%
*   **Avg Speedup:** High (>100x due to caching)

## 🛠️ Setup

### Prerequisites
- Python 3.11+
- Conda (recommended)
- API keys for OpenAI and Groq

### Installation

1. Clone the repository:
```bash
cd ParaMind-Parallel_Agent_Orchestration
```

2. Create conda environment:
```bash
conda create -n paramind python=3.11 -y
conda activate paramind
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure API keys:
```bash
cp .env.example .env
# Edit .env and add your API keys
```

## 🚀 Usage

### Run the Web Application
Start the FastAPI server:
```bash
uvicorn src.api:app --reload
```
Open your browser at `http://localhost:8000`.

### Run Benchmarks
```bash
python benchmarks/run_eval.py
```

## 🔮 Roadmap

- [x] Basic Mode A and Mode B execution
- [x] DAG-based dependency execution
- [x] Modern Web UI (FastAPI + JS)
- [x] Caching layer for responses
- [x] Advanced error recovery (Retries, Partial Failures)
- [x] Comprehensive Benchmarking Suite
- [ ] Cost tracking and budgeting
- [ ] Support for more LLM providers (Anthropic, Google)
