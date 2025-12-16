from pathlib import Path
import requests
import json
import os
import logging
import concurrent.futures
from threading import Lock
from langchain_text_splitters import CharacterTextSplitter
from tqdm import tqdm
from langchain_community.document_loaders import PyPDFLoader
import chat_client as cc


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


def text_splitter(art_text):
    text = str(art_text)
    # Create a TextSplitter instance
    text_splitter = CharacterTextSplitter(
        separator=" ",
        chunk_size=20000,
        chunk_overlap=500,
        length_function=len,
        is_separator_regex=False,
    )

    #Create document
    texts = text_splitter.create_documents([text])
    print(f"art_text{len(art_text)} text_splitter len is :{len(texts)}")
    return texts


def process_file(file_path, prompt):
    """
    处理单个文件的函数
    """
    print(f"Processing: {file_path.name}")  # 减少刷屏，交给 tqdm

    current_dir = Path.cwd()
    # 创建对应的输出文件夹
    output_subdir = current_dir / "ref_data" / file_path.stem
    output_subdir.mkdir(parents=True, exist_ok=True)

    article_text = ""

    # 1. 读取文件内容
    try:
        if file_path.suffix.lower() == '.pdf':
            article_text = load_PDF(file_path)
        elif file_path.suffix.lower() == '.txt':
            with open(file_path, 'r', encoding="utf-8") as f:
                article_text = f.read()
    except Exception as e:
        print(f"Error reading {file_path.name}: {e}")
        return
        # 埋点 2：检查有没有读到内容
    print(f"--> [调试] 文件读取长度: {len(article_text)} 字符")
    if not article_text:
        print(f"Warning: No text extracted from {file_path.name}")
        return

    # 2. 切分文本
    texts = text_splitter(article_text)

    # 埋点 3：检查切分结果
    print(f"--> [调试] 切分数量: {len(texts)} 个片段")
    if len(texts) == 0:
        print("⚠️ [警告] 切分后没有任何片段！")
        return
    # 3. 循环调用 AI
    for i, text in enumerate(texts):
        # 检查该切片是否已经处理过（断点续传）
        output_txt_path = output_subdir / f"{i}.txt"
        if output_txt_path.exists():
            print(f"--> [跳过] 文件已存在: {i}.txt")
            continue

        chunk_content = text.page_content  # Langchain Document 对象的属性是 page_content
        # 埋点 4：确认当前片段有内容
        print(f"--> [调试] 正在准备第 {i} 个片段，长度 {len(chunk_content)}")
        message = [
            {'role': 'system', 'content': prompt},
            {'role': 'user', 'content': chunk_content}
        ]

        try:
            print(f"--> [请求中] 正在发送第 {i} 个片段给 AI...")  # 埋点 5
            # 调用 AI
            response_data = cc.send_message(messages=message)

            # 保存结果
            if response_data:
                print(f"✅ [成功] 收到 AI 回复，长度: {len(response_data)}，正在写入...")
                with open(output_txt_path, "w", encoding="utf-8") as w:
                    w.write(response_data)
            else:
                print(f"❌ [失败] AI 返回了空内容 (None 或 Empty String)")

        except Exception as e:
            print(f"Error processing chunk {i} of {file_path.name}: {e}")


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
    current_dir = Path.cwd()
    target_dir_name = "pdfoutputreview"
    source_dir = current_dir / target_dir_name
    # 自动创建目录（如果不存在）
    if not source_dir.exists():
        source_dir.mkdir(parents=True, exist_ok=True)
        print(f"Folder '{target_dir_name}' created. Please put your PDF/TXT files in it!")
        return
    # 1. 修复：同时获取 PDF 和 TXT 文件
    files = list(source_dir.glob("*.txt")) + list(source_dir.glob("*.pdf"))
    if not files:
        print(f"No .txt or .pdf files found in {source_dir}")
        return
    print(f"Found {len(files)} files. Starting processing...")

    max_workers = 1

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 使用 map 提交任务，process_file 不需要 lock 参数了
        futures = [executor.submit(process_file, file, prompt) for file in files]

        # 使用 as_completed 配合 tqdm 显示进度
        for _ in tqdm(concurrent.futures.as_completed(futures), total=len(files), desc="Processing Files"):
            pass


if __name__ == "__main__":
    # Configure log settings
    logging.basicConfig(filename='error.log', level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')
    main()
