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

## Architecture

```
User Input → Controller (Mode Decision) → Parallel Executor (DAG/Parallel) → Aggregator → Results
```

### Components

1. **Controller**: Analyzes requests, determines Mode A/B, and generates execution plans (JSON).
2. **Parallel Executor**: Runs agents concurrently. Handles DAGs for dependent tasks using topological sort.
3. **LLM Clients**: Unified interface for OpenAI and Groq APIs with caching and retries.
4. **API**: FastAPI backend serving the UI and orchestration endpoints.

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

## License

MIT License - See LICENSE file for details

## Authors

TAMUCC LLM Project Team