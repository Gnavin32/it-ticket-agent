# IT Ticket Triage Agent

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![LangGraph](https://img.shields.io/badge/LangGraph-1.0%2B-green)](https://github.com/langchain-ai/langgraph)

AI-powered IT ticket triage system built with LangGraph that automatically validates, classifies, and routes support tickets to appropriate teams.

## Prerequisites

- **Python 3.10+** (async/await, type hints)
- **pip** (Python package manager)
- **OpenRouter API key** (optional; falls back to mock keyword-based classifier)

## Installation

### 1. Clone or Download the Repository

```bash
git clone https://github.com/yourusername/it-ticket-agent.git
cd it-ticket-agent
```

### 2. Create a Virtual Environment (Recommended)

```bash
python -m venv venv

# On Windows:
venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

The `requirements.txt` file specifies:
- `langgraph>=1.0` — Workflow orchestration and state management
- `openai>=1.40` — OpenAI/OpenRouter API client
- `python-dotenv>=1.0` — Environment variable management

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# OpenRouter API key (optional)
# If not provided, the agent uses a fallback mock classifier
OPENROUTER_API_KEY=your-openrouter-key-here

# LLM model selection (default: openai/gpt-oss-20b)
TRIAGE_MODEL=openai/gpt-oss-20b

# Force mock classifier even if API key exists (optional)
USE_MOCK_LLM=false
```

### Programmatic Configuration

Edit `config.py` to customize:

```python
# Classification vocabulary
CATEGORIES = [
    "Password Reset",
    "Hardware Issue",
    "Software Issue",
    "Network/Connectivity",
    "Access Request",
    "General Inquiry",
]

URGENCIES = ["Low", "Medium", "High", "Critical"]

# Routing thresholds
AUTO_RESOLVE_MIN_CONFIDENCE = 0.8      # Password resets at ≥80% confidence
FALLBACK_MAX_CONFIDENCE = 0.6          # Unknown tickets at <60% confidence

# Category → Support Team mapping
ASSIGNMENT_GROUPS = {
    "Password Reset": "Identity & Access Team",
    "Hardware Issue": "Desktop Support",
    "Software Issue": "Application Support",
    "Network/Connectivity": "Network Operations",
    "Access Request": "Identity & Access Team",
    "General Inquiry": "Service Desk",
}

FALLBACK_GROUP = "AI Review Queue"  # Default for low-confidence tickets
```

## Usage

### Run the Agent

```bash
python run.py
```

Processes sample tickets and saves JSON results to `output/`.

## Project Structure

```
it-ticket-agent/
├── README.md
├── requirements.txt
├── .env
├── .env.example
├── agent.py
├── nodes.py
├── state.py
├── config.py
├── run.py
├── output/
└── interview_talking_points.md
```


