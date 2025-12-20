# Auto-Parallelization Multi-Agent System 🚀

An intelligent agentic system that automatically optimizes Python code by identifying slow sequential loops and refactoring them into parallel implementations using `joblib`.

## 🏗️ Architecture

The system uses **LangGraph** to coordinate specialized AI agents and a consistent feedback loop.

```mermaid
graph TD
    User[User Input File] --> Main[main.py]
    Main -->|Create| Temp[Temp Environment]
    Main -->|Source Code| Graph[LangGraph Workflow]
    
    subgraph "LangGraph Agents"
        Analyzer[Analyzer Agent]
        AST[AST Parser (ast_utils)] -->|Line Numbers| Analyzer
        Implementer[Implementer Agent]
        Validator[Validator Agent]
    end
    
    Graph -->|Step 1| AST
    Analyzer -->|Analysis Report| Implementer
    Implementer -->|Refactored Code| Validator
    
    Validator -->|Generate & Run Script| Temp
    Temp -->|Validation Result| Router{Valid?}
    
    Router -->|Yes| Success[Save Output]
    Router -->|No| Implementer
```

## ✨ Features

-   **Static Analysis (AST)**: Mathematically precise identification of loops and variables before the AI even sees the code.
-   **Multi-Agent Workflow**:
    -   🕵️ **Analyzer**: Combines AST data with LLM reasoning to find parallelizable bottlenecks.
    -   👷 **Implementer**: Refactors code using standard libraries (`joblib`).
    -   ✅ **Validator**: Writes custom test scripts to verify correctness (Output A == Output B) and speedup.
-   **Safe Execution**: Runs validation in a temporary sandbox (`temp_env`) that is automatically cleaned up.
-   **No Hallucinations**: Code is strictly validated by execution, not just by "looking valid".

## 🚀 Getting Started

### Prerequisites

-   Python 3.10+
-   Azure OpenAI API Key (or compatible LLM config)

### Installation

1.  Clone the repository.
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
3.  Configure your environment variables in `.env`:
    ```ini
    GPT_OSS_DEPLOYMENT_NAME=gpt-4o
    AZURE_OPENAI_API_VERSION=...
    AZURE_OPENAI_ENDPOINT=...
    AZURE_OPENAI_API_KEY=...
    ```

## 💻 Usage

Run the main script with your target Python file:

```bash
python main.py path/to/your_script.py
```

### Example

**Input (`workload.py`)**:
```python
def main():
    results = []
    for i in range(10):
        results.append(slow_function(i))
```

**Output (`workload_optimized.py`)**:
```python
from joblib import Parallel, delayed

def main():
    results = Parallel(n_jobs=-1)(delayed(slow_function)(i) for i in range(10))
```

## 📂 Project Structure

-   `main.py`: CLI entry point. Manages file I/O and lifecycle.
-   `graphs/workflow.py`: The LangGraph state machine definition.
-   `agents/`:
    -   `analyser.py`: Identifies loops.
    -   `implementer.py`: Writes parallel code.
    -   `validator.py`: Writes test scripts.
    -   `ast_utils.py`: Python AST walker utility.
-   `temp_env/`: (Ephemeral) Created during runtime for isolated testing.
