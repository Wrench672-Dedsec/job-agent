# Job Agent (LangGraph)

A minimal multi-agent project for an investment research job application assistant. This is a runnable scaffold with a LangGraph flow, FastAPI endpoint, and CLI runner. The agent logic defaults to rule-based mock output, and can switch to a free local Meta Llama setup through Ollama.

## Structure

- src/app/graph: LangGraph state and wiring
- src/app/agents: agent stubs (JD parser, diagnosis, rewriter, interview, networking, RAG)
- src/app/schemas: request/response models
- data: data directory (seed, logs)
- tests: smoke tests

## Setup

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Copy and edit environment file if needed:

```bash
copy .env.example .env
```

To use the free Meta Llama route, install Ollama and pull a model first:

```bash
ollama pull llama3.1:8b
ollama serve
```

## Run API

```bash
uvicorn app.main:app --reload --app-dir src
```

Open http://127.0.0.1:8000/docs for Swagger UI.

## Run CLI

```bash
set PYTHONPATH=src
python -m app.cli --provider ollama --model llama3.1:8b --resume ./data/seed/resume.txt --jd ./data/seed/jd.txt
```

## Next Steps

- Replace rule-based agents with LLM prompts.
- Connect RAG storage and a vector index.
- Extend the seed cases in data/seed/cases.json.
- Add persistence for candidate profiles and cases.
