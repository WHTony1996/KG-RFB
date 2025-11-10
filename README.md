# Chat-RFB: A Knowledge Graph-based Q&A System for Redox Flow Batteries
**Chat-RFB** is a powerful, end-to-end system designed to automatically construct a Knowledge Graph (KG) from a vast corpus of scientific literature on Redox Flow Batteries (RFB) and provide an intelligent Question-Answering (Q&A) bot based on this graph. This project leverages the power of Large Language Models (LLMs) to transform unstructured text into structured knowledge and utilizes a Retrieval-Augmented Generation (RAG) architecture to provide users with precise, fact-based, and domain-specific answers.

## Core Features

-   **Automated Knowledge Extraction**: Automatically extracts entities, relationships, and attributes from scientific papers in PDF and TXT formats to form knowledge triplets.
-   **Efficient Graph Construction**: Utilizes Neo4j's high-performance bulk importer to rapidly build a large-scale knowledge graph containing millions of nodes and relationships.
-   **Intelligent Q&A (RAG)**:
    -   **Natural Language to Cypher**: Intelligently translates a user's natural language questions into executable Cypher queries for the Neo4j database.
    -   **Precise Knowledge Retrieval**: Retrieves the most relevant, fact-based context from the knowledge graph.
    -   **High-Quality Answer Generation**: Generates professional, accurate, and trustworthy answers by grounding the LLM's response in the retrieved knowledge.
-   **Modular Design**: The codebase is cleanly structured into four core modules—extraction, refinement, construction, and Q&A—making it easy to maintain and extend.

## System Architecture & Workflow

The system's workflow is divided into four main phases:

1.  **Phase 1: Knowledge Extraction (`pdf_extract_text.py`)**
    -   The system reads all PDF/TXT documents from a specified directory.
    -   `LangChain` is used to split long texts into manageable chunks.
    -   A Large Language Model (e.g., DeepSeek-v3) is invoked to process each chunk and extract structured knowledge triplets in JSON format.

2.  **Phase 2: Data Refining & Transformation (`txt_2_json.py`)**
    This phase implements a data processing pipeline that transforms raw text outputs into structured CSV files, optimized for bulk import into Neo4j. The process involves several key steps:

    -   TXT to JSON Conversion (`txt_2_json.py`)**: The raw `.txt` files containing AI-generated, JSON-like text are parsed. This script intelligently handles common formatting errors and converts each file into a well-structured `.json` file.

    -   JSON to CSV Aggregation (`json_2_csv.py`)**: All individual `.json` files are aggregated. The script extracts the node and relationship data from them and consolidates everything into a single, master CSV file.

    -   Enrichment and Finalization (`add-ref.py`)**: The master CSV is enriched by adding source literature information. A critical de-duplication process is then performed to ensure each node is unique, assigning a unique ID to each. The final output is split into two import-ready files: `node_new.csv` (for unique entities) and `relation_new.csv` (for the relationships between them).


3.  **Phase 3: Knowledge Graph Construction (`main.py`)**
    -   The `neo4j-admin database import` command is executed to efficiently load the processed CSV files into the Neo4j database, completing the KG construction.

4.  **Phase 4: Question-Answering System (`llm_with_neo4j.py`)**
    -   A user inputs a question in natural language.
    -   The LLM translates the question into a Cypher query.
    -   The system executes the query against the Neo4j KG to retrieve relevant information.
    -   The LLM then generates a final, context-aware answer based on the retrieved information.

## Tech Stack

-   **Backend**: Python 3.12
-   **Database**: Neo4j (e.g., Community Edition 5.6.1)
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
    git clone https://github.com/your-username/Chat-RFB.git
    cd Chat-RFB
    ```

2.  **Install Python Dependencies**
    It is recommended to use a virtual environment:
    ```bash
    python -m chat-rfb venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    pip install pandas neo4j openai langchain-text-splitters "PyPDFLoader[image]" tqdm requests httpx readerwriterlock
    ```    *(You can also create a `requirements.txt` file with the libraries listed above and run `pip install -r requirements.txt`)*

3.  **Configure Neo4j**
    -   Open Neo4j and create a new database (the project default is `neo4j`).
    -   **Crucially, you must update the file paths** in the `command` variable within `main.py` to point to the `import` directory of your own Neo4j installation.
      ```python
      # in main.py
      command = """neo4j-admin database import full `
             --nodes=Node=C:/Your/Path/To/Neo4j/import/node_new.csv `
             --relationships=ORDERED=C:/Your/Path/To/Neo4j/import/relation_new.csv `
             ..."""
      ```
    -   Update your Neo4j connection details (if they are not the default) in `llm_with_neo4j.py`.
      ```python
      # in llm_with_neo4j.py
      run_cypher_query(..., uri="bolt://localhost:7687", user="neo4j", password="your_password")
      ```

4.  **Configure LLM API Key**
    -   Open `chatgpt_client.py`.
    -   Replace the placeholder `api_key` with your actual API key from DeepSeek or another OpenAI-compatible service.
      ```python
      # in chat_client.py
      client = OpenAI(
          base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
          api_key="sk-your_api_key_here",
      )
      ```

5.  **Prepare Your Data**
    -   Place all your source `.pdf` or `.txt` files into a directory.
    -   **Update the hardcoded paths** in the scripts (especially in `txt_2_json.py`,`add-ref.py`,`json_2_csv.py`and `csv_refine.py`) to point to your data directories. For example, change `F:\WORK\flow_battery_pdf\pdfoutputreview` to your chosen path.

## Usage

Run the main script from your terminal to control the entire workflow.

```bash
python main.py
```

The program will display a task menu:
```
0, quit
1, Extract node information
2, Add a reference index
3, Write to the neo4j platform
4, Use a question and answer system
```

**Please execute the tasks sequentially (1 -> 2 -> 3 -> 4) for the first run:**

1.  **Enter `1`**: To begin extracting knowledge from your PDF/TXT files. This may take a long time depending on the number of documents.
2.  **Enter `2`**: To run the multi-step data processing pipeline. This phase cleans the extracted text and generates the final CSV files for import. It involves the following scripts:
    *   `txt_2_json.py`: Converts the raw text files into structured JSON format, intelligently fixing common errors.
    *   `json_2_csv.py`: Aggregates all the generated JSON files into a single master CSV file.
    *   `add-ref.py`: Enriches the master CSV with source information, de-duplicates data, and creates the final `node` and `relation` files ready for import.
    
    > **Note:** Please ensure Step 1 is completed before running this pipeline.
3.  **Enter `3`**: To bulk-import the data into your Neo4j database, building the knowledge graph.
4.  **Enter `4`**: To launch the interactive Q&A system. You can now ask questions in the console, for example:
    > "What are the advantages of anthraquinone in organic flow batteries?"
    > "List the properties of vanadium."

Enter `exit` or `0` to quit the program or the Q&A session.

## Code Modules Overview

-   `main.py`: The main entry point and workflow controller for the project.
-   `pdf_extract_text.py`: Handles reading text from documents, chunking, and calling the LLM for knowledge extraction.
-   `txt_2_json.py`: Contains functions for data cleaning, node de-duplication, and formatting data for Neo4j import.
-   `llm_with_neo4j.py`: Implements the core RAG logic, including Cypher generation, Neo4j querying, and final answer generation.
-   `chatgpt_client.py`: A client wrapper for communicating with the Large Language Model API.
-   `subNeo4j/`: (Inferred) A directory for helper scripts related to data transformation, such as `csv_refine.py`.

## Roadmap

-   **Web Interface**: Develop a user-friendly UI using Gradio or Streamlit.
-   **Model Evaluation**: Create a benchmark dataset to quantitatively measure the accuracy of knowledge extraction and Q&A performance.
-   **Incremental Updates**: Implement a mechanism to periodically process new literature and incrementally update the knowledge graph.
-   **Visualization**: Integrate tools like Neo4j Bloom to visualize knowledge subgraphs and retrieval paths for user queries.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request or create an Issue to report bugs, suggest features, or ask questions.

