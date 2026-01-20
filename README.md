<div align="center">

# Chat-RFB: A Flow Battery Chat System Leveraging Knowledge Graphs and Large Language Models

[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows%2010%20Only-0078D6.svg)](https://www.microsoft.com/windows)
[![Neo4j](https://img.shields.io/badge/Database-Neo4j-008CC1.svg)](https://neo4j.com/)
[![LLM](https://img.shields.io/badge/AI-LLM%20%2B%20RAG-green.svg)](https://openai.com/)

</div>

---

**Chat-RFB** is a powerful, end-to-end system designed to automatically construct a Knowledge Graph (KG) from a vast corpus of scientific literature on Redox Flow Batteries (RFB) and provide an intelligent Question-Answering (Q&A) bot based on this graph. 

This project leverages the power of Large Language Models (LLMs) to transform unstructured text into structured knowledge and utilizes a Retrieval-Augmented Generation (RAG) architecture to provide users with precise, fact-based, and domain-specific answers.

> [!NOTE]
> **Validated Environment:** This system has been rigorously tested and validated on **Windows 10** using **Python 3.12** and the **DeepSeek-V3** model. While other configurations may work, this specific setup is highly recommended for stability. 

---

## ✨ Core Features

- **🤖 Automated Knowledge Extraction**  
  Automatically extracts entities, relationships, and attributes from scientific papers in PDF and TXT formats to form knowledge triplets.

- **🧹 Robust Data Cleaning**  
  Includes intelligent parsing logic to handle LLM output quirks (e.g., stripping Markdown code blocks) and fixes common JSON formatting errors.

- **⚡ One-Click Graph Preparation**  
  A streamlined pipeline that aggregates raw data, deduplicates nodes, creates reference indices (DOI linking), and generates CSVs ready for Neo4j import.

- **🧠 Intelligent Q&A (RAG)**  
  - **Natural Language to Cypher:** Intelligently translates a user's natural language questions into executable Cypher queries.
  - **Multi-turn Conversation:** Supports context-aware follow-up questions.
  - **Precise Knowledge Retrieval:** Retrieves the most relevant facts from the knowledge graph to ground the LLM's answers.

---

## 🏗 System Architecture & Workflow

The system's workflow is divided into four main phases:

### Phase 1: Knowledge Extraction (`pdf_extract_text.py`)
- The system reads all PDF/TXT documents from a specified directory.
- `LangChain` is used to split long texts into manageable chunks.
- A Large Language Model (e.g., DeepSeek-v3) is invoked to process each chunk and extract structured knowledge triplets in JSON format.

### Phase 2: Data Refining & Transformation (`txt_2_json.py` & `csv_refine.py`)
This phase is a unified pipeline triggered by Task 2 in the main menu:
- **TXT to JSON Cleaning:** `txt_2_json.py` traverses all DOI subfolders. It uses regex to strip Markdown tags (e.g., ` ```json ... ``` `) often added by LLMs and repairs syntax errors to save valid `.json` files.
- **CSV Aggregation & Refinement:** `subNeo4j/csv_refine.py` aggregates all JSON data, assigns unique IDs to nodes, deduplicates entries, and establishes "Mention" relationships between entities and their source DOIs.
- **Output:** A `CSV_Output` directory containing `node_new.csv` and `relation_new.csv`.

### Phase 3: Knowledge Graph Construction (`main.py`)
- The `neo4j-admin database import` command is executed to efficiently load the processed CSV files into the Neo4j database, completing the KG construction.

### Phase 4: Question-Answering System (`llm_with_neo4j.py`)
- A user inputs a question in natural language.
- The LLM translates the question into a Cypher query.
- The system executes the query against the Neo4j KG to retrieve relevant information.
- The LLM then generates a final, context-aware answer based on the retrieved information.

---

## 🛠 Tech Stack

| Component | Technology |
| :--- | :--- |
| **OS Requirement** | **Windows 10** (Due to `pywin32` and PowerShell dependencies) |
| **Language** | Python 3.12 |
| **Recommended Model** | **DeepSeek-V3** (Verified for optimal performance) |
| **Database** | Neo4j Community/Enterprise |
| **Graph Operations** | `neo4j` (Python Driver), `neo4j-admin` |
| **Data Handling** | `pandas` |
| **Text Processing** | `langchain-text-splitters`, `PyPDFLoader` |


---
## 🚀 Getting Started

### Prerequisites
- **Operating System:** Windows 10 or 11.
- **Database:** Neo4j Desktop or Server installed.
- **API Key:** A valid API key for **DeepSeek** (recommended) or OpenAI.

### Installation & Setup

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/WHTony1996/KG-RFB.git
    cd KG-RFB
    ```

2.  **Install Python Dependencies**
    It is recommended to use a virtual environment:
    ```bash
    conda create -n chat_rfb_env python=3.12
    conda activate chat_rfb_env
    pip install -r requirements.txt
    ```

3.  **Configure Environment Variables**
    Create a `.env` file in the root directory to store your API keys securely.
    ```env
    DEEPSEEK_API_KEY=sk-your_deepseek_key_here
    OPENAI_API_KEY=sk-your_openai_key_here
    # Add other keys (ALIYUN, GOOGLE) if needed
    ```

4.  **Configure Neo4j**
    Update your Neo4j connection details in `llm_with_neo4j.py` if they differ from the defaults:
    ```python
    # llm_with_neo4j.py
    run_cypher_query(..., uri="bolt://localhost:7687", user="neo4j", password="your_password")
    ```

5.  **Prepare Your Data**
   *   **Option A (Build from Source):** Place your source `.pdf` files into a directory (e.g., `...KG-RFB\pdfoutputreview`).
   *   **Option B (Use Pre-built Database):** If you wish to skip the data extraction and graph construction phases (Tasks 1-3) and test the Q&A system immediately:
       *   Locate the `import/rfbdatabase.rar` file in this repository.
       *   Extract the contents into your Neo4j installation directory under `data/databases/`.
       *   Switch your Neo4j active database to this `rfbdatabase` (or overwrite the default `neo4j` database folder).

---

## 📖 Usage

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
> [!IMPORTANT]
> **Quick Start Mode:**
> We have provided a **pre-constructed Knowledge Graph database** compressed as `import/rfbdatabase.rar`. 
> *   **To use it:** Unzip this file directly into your Neo4j `data/databases/` directory. This allows you to skip Tasks 1, 2, and 3, and proceed directly to **Task 4** to test the Q&A system.
> *   **To build from scratch:** Please execute the tasks in order (1 -> 2 -> 3 -> 4).

1.  **Task 1:** Enter `1`.
    The system will extract text from your PDF/TXT files and save raw chunks into a `ref_data` (or similar) folder.

2.  **Task 2:** Enter `2`.
    - You will be asked to input the **ROOT directory** containing the DOI folders generated in Task 1.
    - The system will clean the text, convert it to JSON, and generate `node_new.csv` and `relation_new.csv` in a `CSV_Output` folder next to your data.

3.  **Task 3:** Enter `3`.
    - **Note:** Stop your Neo4j database service before running this.
    - Input the `CSV_Output` directory path.
    - The script will generate and attempt to run the PowerShell command to import data. If it fails due to permissions, copy the generated command and run it manually in a generic terminal as Administrator.

4.  **Task 4:** Enter `4`.
    Start asking questions about Redox Flow Batteries!

---

## 📂 Code Modules Overview

| File Name | Description |
| :--- | :--- |
| `main.py` | The central controller that manages the user interface and task orchestration. |
| `chat_client.py` | A unified wrapper for LLM API calls (DeepSeek, OpenAI, Gemini) with fallback mechanisms. |
| `pdf_extract_text.py` | Handles document loading, chunking, and initial information extraction via LLM. |
| `txt_2_json.py` | Contains robust logic to extract valid JSON from LLM responses (strips Markdown) and fix syntax errors. |
| `subNeo4j/csv_refine.py` | A comprehensive class for aggregating JSON data, generating unique IDs, deduping entities, and building the reference index (DOI linking). |
| `llm_with_neo4j.py` | Implements the RAG system, managing chat history and Neo4j Cypher query generation. |

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a **Pull Request** or create an **Issue** to report bugs, suggest features, or ask questions.
