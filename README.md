# Multi-Agent Code Translation

This repository contains the full implementation of a modular multi-agent system for automated code translation between Python and Java. The system was developed as part of a Master of Engineering project at the University of Toronto under the supervision of Prof. Eldan Cohen.

The project investigates whether breaking down translation into specialized agent subtasks (e.g., analysis, translation, evaluation, regeneration) can improve performance over a single LLM-based translator.

---

## 🔍 Overview

Large Language Models (LLMs) can generate code but often fail to preserve semantic accuracy, especially for statically typed languages like Java. This project explores multi-agent architectures that coordinate translation, evaluation, and regeneration steps to improve translation robustness and correctness.

The following five architectures are implemented and evaluated:

- **Baseline Translator**: One-shot GPT-4o translation
- **Multi-Agent #1**: Translator + Evaluator + Regenerator (unit-test based)
- **Multi-Agent #2**: Adds Analyzer Agent to Architecture #1
- **Multi-Agent #3**: Deep Analyzer + Claude Sonnet Evaluator (no unit tests)
- **Multi-Agent #2 + DA**: Uses the Deep Analyzer from Architecture #3 within Architecture #2

---

## 🛠️ Technologies

- **LangGraph**: Multi-agent orchestration
- **GPT-4o (OpenAI)**: Main LLM for all agents
- **Claude 3.7 Sonnet (Anthropic)**: Used for critique-based evaluation in Architecture #3
- **Python**: Scripting, orchestration, testing

---

## 📁 Repository Structure
  ```text
    multi-agent-code-translation
    ├── baseline                        # Baseline one‑shot architecture
    │   ├── code                        # Implementation and agent logic
    │   └── evaluation                  # Evaluation results
    │
    ├── multiagent_1                     # Architecture #1: Translator + Evaluator + Regenerator
    │   ├── code  
    │   └── evaluation  
    │
    ├── multiagent_2                     # Architecture #2: Adds Analyzer to #1, Includes Multi-Agent #2 + DA
    │   ├── code  
    │   └── evaluation
    │
    ├── multiagent_3                     # Architecture #3: Deep Analyzer + Claude Evaluator
    │   ├── code
    │   └── evaluation  
    │
    ├── Dataset.zip                     # GeeksforGeeks test dataset (Python ↔ Java)
    ├── Meng_Project_Final_Report.pdf   # Final technical report
    ├── requirements.txt                # Python dependencies
    └── README.md                       # Project documentation
``` 
---

## 🚀 Getting Started

1. Clone the repository:
   ```bash
   git clone https://github.com/Pyoussefpour/multi-agent-code-translation.git
   cd multi-agent-code-translation

2. Install dependencies:
   ```bash
    pip install -r requirements.txt

3. Set your OpenAI and Claude API keys as environment variables.\
   ```bash
    export OPENAI_API_KEY=your_openai_api_key
    export CLAUDE_API_KEY=your_claude_api_key

5. Run the translation Architecture pipeline


## 📊 Evaluation Results

| Architecture         | Python → Java | Java → Python |
|----------------------|---------------|----------------|
| Baseline GPT-4o      | 46%           | 84%            |
| Multi-Agent #1       | 68%           | 82%            |
| Multi-Agent #2       | 68%           | 80%            |
| Multi-Agent #3       | **78%**       | 84%            |
| Multi-Agent #2 + DA  | 68%           | **86%**        |



