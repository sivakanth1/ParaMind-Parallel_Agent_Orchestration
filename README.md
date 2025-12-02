# ParaMind: Dynamic Parallel Agentic Orchestration

An intelligent multi-agent system that dynamically decides whether to run tasks in parallel across multiple LLMs or decompose complex requests into concurrent subtasks (DAGs).

## Features

- **Mode A (Data-Parallel)**: Execute the same prompt across multiple LLM models simultaneously for comparison or consensus.
- **Mode B (Instruction-Parallel)**: Decompose complex tasks into independent or dependent subtasks (DAG execution).
- **Smart Controller**: AI-powered decision engine that chooses the optimal execution mode using LLM reasoning or semantic fallback.
- **Dependency Management**: Automatically handles task dependencies in Mode B, executing tasks in topological order.
- **Robustness**: Built-in retries, error handling, and partial failure recovery.
- **Modern Web UI**: Fast, responsive interface built with FastAPI and Vanilla JS.
- **Comprehensive Benchmarking**: Automated evaluation suite to measure speedup, latency, and success rates.

## Supported Models

ParaMind supports a variety of high-performance LLMs via Groq and OpenAI:

*   **Llama 3.3 70B Versatile** (`llama-3.3-70b-versatile`): High intelligence, great for planning and complex reasoning.
*   **Llama 3.1 8B Instant** (`llama-3.1-8b-instant`): Extremely fast, ideal for simple subtasks and summarization.
*   **Mixtral 8x7B** (`mixtral-8x7b-32768`): Strong performance on logical tasks.
*   **Gemma 2 9B** (`gemma2-9b-it`): Google's lightweight open model.
*   **OpenAI GPT Models**: Compatible with GPT-3.5/4 (via configuration).

## Project Mind Map

![ParaMind Project Mind Map](assets/project_mindmap.png)

## System Architecture

```mermaid
graph TD
    User[User Input] --> Controller[Controller (Brain)]
    Controller -->|Mode A| Parallel[Parallel Executor]
    Controller -->|Mode B| DAG[DAG Executor]
    Parallel --> Aggregator[Result Aggregator]
    DAG --> Aggregator
    Aggregator --> Final[Unified Response]
```

### Technical Deep Dive

#### 1. The Controller (`src/controller.py`)
Responsible for understanding user intent. It uses **Few-Shot Prompting** with a smart model (`llama-3.3-70b`) to generate an execution plan. If the LLM fails, a **Semantic Fallback** engine analyzes linguistic markers (e.g., "compare", "and", "plan") to determine the mode deterministically.

#### 2. The Executor (`src/agents.py`)
*   **Concurrency:** Built on Python's `asyncio` for non-blocking parallel execution.
*   **DAG Logic:** Uses **Topological Sort** to organize Mode B subtasks into "execution layers". Tasks in the same layer run simultaneously.
*   **Context Injection:** Dynamically injects the output of parent tasks into the context window of dependent child tasks.

#### 3. The Aggregator (`src/aggregator.py`)
Synthesizes individual agent outputs into a single, coherent response using a fast summarization model (`llama-3.1-8b`), ensuring the user gets a unified answer rather than disjointed parts.

## Performance Metrics

ParaMind tracks key metrics to demonstrate efficiency:

*   **Sequential Baseline:** Estimated time if tasks were performed one by one ($\sum Latency$).
*   **Parallel Execution:** Actual wall-clock time taken ($\max Latency$).
*   **Speedup Factor:** $\frac{\text{Sequential Baseline}}{\text{Parallel Execution}}$ (typically 2x-5x).

## Setup

### Prerequisites

- Python 3.11+
- Conda/Anaconda (recommended) or Python venv
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

### API Keys

- **OpenAI**: Get from https://platform.openai.com/api-keys
- **Groq** (FREE): Get from https://console.groq.com/keys

## Usage

### Run the Web Application

Start the FastAPI server:
```bash
uvicorn src.api:app --reload
```

Open your browser at `http://localhost:8000`.

### Example Prompts

**Mode A (Data-Parallel):**
- "Compare Python vs JavaScript for backend development"
- "Generate 3 different marketing taglines for a coffee shop"

**Mode B (Instruction-Parallel):**
- "Plan a 5-day Tokyo trip with budget, attractions, and food recommendations" (Parallel subtasks)
- "Research the history of Bitcoin and then write a summary based on that research" (Dependent subtasks)

## Benchmarking

Run the automated evaluation suite:

```bash
python benchmarks/run_eval.py
```

Results will be saved to `benchmarks/results/` in JSON and CSV formats.

## Project Structure

```
ParaMind-Parallel_Agent_Orchestration/
├── src/
│   ├── api.py             # FastAPI backend
│   ├── controller.py      # Mode decision & planning logic
│   ├── agents.py          # Parallel & DAG execution
│   ├── llm_clients.py     # API wrappers with caching/retries
│   └── aggregator.py      # Result synthesis
├── ui/
│   ├── index.html         # Main UI
│   ├── style.css          # Styling
│   └── app.js             # Frontend logic
├── benchmarks/
│   ├── run_eval.py        # Benchmark runner
│   └── prompts.json       # Test cases
├── tests/
│   ├── test_dependencies.py
│   └── test_robustness.py
├── .env                   # API keys (not in git)
└── README.md
```

## Development

### Running Tests

```bash
pytest tests/
```

## Roadmap

- [x] Basic Mode A and Mode B execution
- [x] DAG-based dependency execution
- [x] Modern Web UI (FastAPI + JS)
- [x] Caching layer for responses
- [x] Advanced error recovery (Retries, Partial Failures)
- [x] Comprehensive Benchmarking Suite
- [ ] Cost tracking and budgeting
- [ ] Support for more LLM providers (Anthropic, Google)
