# Chat-RFB: a flow battery chat system leveraging knowledge graphs and large language models
**Chat-RFB** is a powerful, end-to-end system designed to automatically construct a Knowledge Graph (KG) from a vast corpus of scientific literature on Redox Flow Batteries (RFB) and provide an intelligent Question-Answering (Q&A) bot based on this graph. This project leverages the power of Large Language Models (LLMs) to transform unstructured text into structured knowledge and utilizes a Retrieval-Augmented Generation (RAG) architecture to provide users with precise, fact-based, and domain-specific answers.

## Core Features

-   **Automated Knowledge Extraction**: Automatically extracts entities, relationships, and attributes from scientific papers in PDF and TXT formats to form knowledge triplets.
-   **Robust Data Cleaning**: Includes intelligent parsing logic to handle LLM output quirks (e.g., stripping Markdown code blocks) and fixes common JSON formatting errors.
-   **One-Click Graph Preparation**: A streamlined pipeline that aggregates raw data, deduplicates nodes, creates reference indices (DOI linking), and generates CSVs ready for Neo4j import.
-   **Intelligent Q&A (RAG)**:
    -   **Natural Language to Cypher**: Intelligently translates a user's natural language questions into executable Cypher queries.
    -   **Multi-turn Conversation**: Supports context-aware follow-up questions.
    -   **Precise Knowledge Retrieval**: Retrieves the most relevant facts from the knowledge graph to ground the LLM's answers.

## System Architecture & Workflow

The system's workflow is divided into four main phases:

1.  **Phase 1: Knowledge Extraction (`pdf_extract_text.py`)**
    -   The system reads all PDF/TXT documents from a specified directory.
    -   `LangChain` is used to split long texts into manageable chunks.
    -   A Large Language Model (e.g., DeepSeek-v3) is invoked to process each chunk and extract structured knowledge triplets in JSON format.

2.  **Phase 2: Data Refining & Transformation (`txt_2_json.py` & `csv_refine.py`)**
    This phase is a unified pipeline triggered by Task 2 in the main menu:
    -   **TXT to JSON Cleaning**: `txt_2_json.py` traverses all DOI subfolders. It uses regex to strip Markdown tags (e.g., ` ```json ... ``` `) often added by LLMs and repairs syntax errors to save valid `.json` files.
    -   **CSV Aggregation & Refinement**: `subNeo4j/csv_refine.py` aggregates all JSON data, assigns unique IDs to nodes, deduplicates entries, and establishes "Mention" relationships between entities and their source DOIs.
    -   **Output**: A `CSV_Output` directory containing `node_new.csv` and `relation_new.csv`.


3.  **Phase 3: Knowledge Graph Construction (`main.py`)**
    -   The `neo4j-admin database import` command is executed to efficiently load the processed CSV files into the Neo4j database, completing the KG construction.

4.  **Phase 4: Question-Answering System (`llm_with_neo4j.py`)**
    -   A user inputs a question in natural language.
    -   The LLM translates the question into a Cypher query.
    -   The system executes the query against the Neo4j KG to retrieve relevant information.
    -   The LLM then generates a final, context-aware answer based on the retrieved information.

## Tech Stack

-   **Backend**: Python 3.12
-   **Database**: Neo4j 
-   **Core Libraries**:
    -   `openai`: For interacting with LLM APIs (compatible with DeepSeek, etc.).
    -   `neo4j`: For connecting to and querying the Neo4j database.
    -   `pandas`: For data manipulation and CSV handling.
    -   `langchain-text-splitters`: For efficient text chunking.
    -   `PyPDFLoader`: For reading content from PDF files.
    -   `tqdm`: For displaying elegant progress bars.

## Getting Started

### Prerequisites

-   Neo4j Desktop or Server installed and running.

### Installation & Setup

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/WHTony1996/KG-RFB.git
    cd KG-RFB
    ```

2.  **Install Python Dependencies**
    It is recommended to use a virtual environment:
    ```bash
    conda create -n chat_rfb python=3.12
    conda activate chat_rfb
    pip install -r requirements.txt

3.  **Configure Environment Variables**
    Create a `.env` file in the root directory to store your API keys securely. 
    ```env
    DEEPSEEK_API_KEY=sk-your_deepseek_key_here
    OPENAI_API_KEY=sk-your_openai_key_here
    # Add other keys (ALIYUN, GOOGLE, ANTHROPIC) if needed
    ```
    
4. **Configure Neo4j**
Update your Neo4j connection details in `llm_with_neo4j.py` if they differ from the defaults:
    ```python
    # llm_with_neo4j.py
    run_cypher_query(..., uri="bolt://localhost:7687", user="neo4j", password="your_password")
    ```

5.  **Prepare Your Data**
    -   Place your source `.pdf` files into a directory (e.g., `F:\Data\Source`).
    -   The system will automatically create output folders structure during Phase 1.

## Usage

Run the main script from your terminal to control the entire workflow.

```bash
python main.py
```

The program will display a task menu:
```
0, quit
1, Extract node information
2, Process Data (TXT -> JSON -> CSV + Reference Index)
3, Write to the neo4j platform
4, Use a question and answer system
```

**Please execute the tasks sequentially (1 -> 2 -> 3 -> 4) for the first run:**

-  Task 1: Enter 1. The system will extract text from your PDF/TXT files and save raw chunks into a ref_data (or similar) folder.
-  Task 2: Enter 2.
You will be asked to input the ROOT directory containing the DOI folders generated in Task 1.
The system will clean the text, convert it to JSON, and generate node_new.csv and relation_new.csv in a CSV_Output folder next to your data.
-  Task 3: Enter 3.
Important: Stop your Neo4j database service before running this.
Input the CSV_Output directory path.
The script will generate and attempt to run the PowerShell command to import data. If it fails due to permissions, copy the generated command and run it manually in a generic terminal as Administrator.
-  Task 4: Enter 4. Start asking questions about Redox Flow Batteries!

## Code Modules Overview

-  main.py: The central controller that manages the user interface and task orchestration.
-  chat_client.py: A unified wrapper for LLM API calls (DeepSeek, OpenAI, Gemini) with fallback mechanisms.
-  pdf_extract_text.py: Handles document loading, chunking, and initial information extraction via LLM.
-  txt_2_json.py: Contains robust logic to extract valid JSON from LLM responses (strips Markdown) and fix syntax errors.
-  subNeo4j/csv_refine.py: A comprehensive class for aggregating JSON data, generating unique IDs, deduping entities, and building the reference index (DOI linking).
-  llm_with_neo4j.py: Implements the RAG system, managing chat history and Neo4j Cypher query generation.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request or create an Issue to report bugs, suggest features, or ask questions.

