from pathlib import Path

import requests
import json
import os
import logging
import concurrent.futures
from threading import Lock
# from readerwriterlock import rwlock
from langchain_text_splitters import CharacterTextSplitter
from tqdm import tqdm
from langchain_community.document_loaders import PyPDFLoader
# import torch
import chat_client as cc

def send_message(prompt, article_text):
    url = "http://172.19.7.73:43413"
    headers = {'Content-Type': 'application/json'}
    data = {
            "prompt": prompt,
            "history": article_text,
        # "model": "Qwen/Qwen2.5-7B-Instruct-AWQ",
        # "messages": [
        #     {"role": "system", "content": "You are Qwen, created by Alibaba Cloud. You are a helpful assistant."},
        #     {"role": "user", "content": "Tell me something about large language models."}
        # ],
        "temperature": 0.7,
        "top_p": 0.8,
        "repetition_penalty": 1.05,
        "max_tokens": 512
    }

    response = requests.post(url, headers=headers, data=data)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: Received status code {response.status_code}")
        return None


def load_PDF(pdf_path):
    loader = PyPDFLoader(pdf_path,
                         extract_images=False,
                         )
    # docs = loader.load()
    # print(docs[0].metadata)
    pages = []
    for doc in loader.lazy_load():
        doc = doc.page_content.replace('\n', ' ')
        pages.append(doc)
    return pages


def document_to_dict(doc):
    return {
        'metadata': doc.metadata,
        'page_content': doc.page_content
    }


def text_splitter(art_text):
    text = [art_text]
    # Create a TextSplitter instance
    text_splitter = CharacterTextSplitter(
        separator=" ",
        chunk_size=20000,
        chunk_overlap=500,
        length_function=len,
        is_separator_regex=False,
    )

    # 创建文档
    texts = text_splitter.create_documents(text)
    # texts = text_splitter.split_text(text=str_text)
    # print(f'{type(texts)}texts len1: {len(texts)}\n{texts[0]}')
    # print(f'{type(texts)}texts len2: {len(texts)}\n{texts[1]}')
    print(f"art_text{len(art_text)} text_splitter len is :{len(texts)}")
    return texts


def process_pdf(txt_file, lock, prompt):
    """
    :param txt_file:  Enter the text content of txt
    :param lock:
    :param prompt: Prompt words
    :return:
    """
    print(f"Processing {txt_file}")

    output_file = Path(r"F:\WORK\flow_battery_pdf\jsonfile_5") / txt_file.name[:-4]
    # Ensure the target directory exists (create it if it does not exist).
    output_file.mkdir(parents=True, exist_ok=True)
    article_text =""
    if txt_file.suffix == '.pdf':
        article_text = load_PDF(txt_file)
    elif txt_file.suffix == '.txt':
        with open(txt_file, 'r', encoding="utf-8") as f:
            article_text = f.read()
    # article_text.append(prompt)
    texts = text_splitter(article_text)

    try:
        for i, text in enumerate(texts):
            article_text_str = str(text)
            print(len(article_text_str))
            # response_data = send_message(article_text_str, article_text=[])
            message = []
            message.append({'role': 'system', 'content': prompt})
            message.append({'role': 'user', 'content': article_text_str})
            response_data = cc.send_message(messages=message)
            if response_data:
                print("AI:", response_data)
            output_txt_path = output_file / f"{i}.txt"
            # with Lock:
            with open(output_txt_path, "w", encoding="utf-8") as w:
                w.write(response_data)
    except Exception as e:
        print(e)

def main():
    # Define a system message as part of the context.
    prompt = """ You are an expert in creating knowledge graph database. Here are some article excerpts related to the field of redox flow batteries that need to be organized. You need create professional nodes and relationships based on important the information. This includes all key data information describing battery performance. Ideally, all nodes should be one or two words. Return JSON. Json can only contain start_node relationship、end_node, and the Label of nodes. Output the result in JSON format without any line breaks, etc. ! Please strictly follow the JSON output format.,
"you_need":
[
"1.JSON file contains multiple dictionaries",
"2.Each dictionary contains five key-value pairs that: start_node, relationship, end_note,start_node_label,end_node_label",
"3.The value is a str",
"4.Please use the correct json format.",
"5. Note that if the text content is recognized as a reference, skip the relevant content",
"6. Explain the meaning of abbreviations, such as RFB is Redox Flow Battery",
"7. Require all labels to be represented by a single noun",
"8. Use singular form for nouns",
"9. Collect as much data information as possible, including numerical values and units"
],
"example":
[
{"start_node":"RFB","relationship":"is","end_node":"Redox Flow Battery", "start_node_label":"abbreviation", "end_node_label":"full name"},
{"start_node":"word","relationship":"word","end_node":"word", "start_node_label":"label", "end_node_label":"label"}
]
"""

    # Initialize history and add system messages
    # prompt = [system_message]
    txt_dir = Path(r"F:\WORK\flow_battery_pdf\pdfoutputreview")
    txt_paths = list(txt_dir.glob("*.txt"))
    # for file in tqdm(txt_paths):
    #     file = str(file)
        # txt_path = os.path.join(txt_dir, file)


    # Initialize locks and thread pools
    lock = Lock()
    max_workers = 80

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Use TQDM to track progress and submit tasks.
        list(tqdm(
            executor.map(lambda file: process_pdf(file, lock, prompt), txt_paths),
            total=len(txt_paths),
            desc="Processing jsons"
        ))


if __name__ == "__main__":
    # Configure log settings
    logging.basicConfig(filename='error.log', level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')
    main()
