import PyPDF2
import os
import logging
from tqdm import tqdm
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import CharacterTextSplitter, NLTKTextSplitter
from openai import OpenAI
import datetime
import shutil
import json
# import nltk
# nltk.download('punkt_tab')
import chatgpt_client as cc

# Set OpenAI's API key and API base to use vLLM's API server.
openai_api_key = "EMPTY"
openai_api_base = "http://172.19.7.73:6000/v1"  # VLLM 开源模型路径

client = OpenAI(
    api_key=openai_api_key,
    base_url=openai_api_base,
)


def load_PDF(pdf_path):
    loader = PyPDFLoader(pdf_path,
                         extract_images=False,
                         )
    # docs = loader.load()
    # print(docs[0].metadata)
    pages = []
    for doc in loader.lazy_load():
        # doc = doc.page_content.replace('\n', ' ')
        page_doc = doc.page_content
        pages.append(page_doc)
    # print(f"{type(pages)} pages len:", len(pages))
    return pages


def read_pdfs(file_path):
    with open(file_path, 'r') as pdf_file:
        # 创建一个PDF阅读器对象
        reader = PyPDF2.PdfReader(pdf_file)
        res = []
        for page_num in range(len(reader.pages)):
            # 获取当前页面的文本内容
            text = reader.pages[page_num].extract_text()
            # print(text)
            res.append(text)
    return res


def send_message(content='', prompt='', temperature=0.9):
    chat_response = client.chat.completions.create(
        model="QWen2.5-72B-Instruct-AWQ",
        messages=[
            {
                "role": "system",
                "content": prompt
             },
            {
                "role": "user",
                "content": content
             },
        ],
        temperature=temperature,
        top_p=0.8,
        # max_tokens=127000,
        extra_body={
            "repetition_penalty": 1.05,
        },
        # response_format={"type": "json_object"}
    )
    if chat_response.choices is not None:
        # logging.info("AI:", chat_response.choices[0])

        response = chat_response.choices[0].message.content
        print(response)
    return response


def text_splitter(text):
    # print(f"{type(text)}text len is :{len(text)}")
    str_text = ''
    for t in text:
        str_text += t
    # 创建TextSplitter实例
    text_splitter = CharacterTextSplitter(
        separator="\n",
        chunk_size=4000,
        chunk_overlap=500,
        length_function=len,
        is_separator_regex=False,
    )

    # 创建文档
    # texts = text_splitter.create_documents(text)
    texts = text_splitter.split_text(text=str_text)
    print(f'{type(texts)} split_text len: {len(texts)}\n')
    # for t in texts:
    #     logging.info(t)
    # print(f'{type(texts)}texts len2: {len(texts)}\n{texts[1]}')
    return texts


if __name__ == "__main__":
    prompt_table = f"""Prompt:[I have provided you with a paper from which I can learn about the material composition and performance of flow batteries.
Please use a standardized table in markdown format to summarize the following detailed information in the article.
If no information is provided in the paper or you are unsure, please use "N/A" to fill in the table.]
This table should have 25 columns, with the following header:
    Publication time、DOI、type of flow battery (classified by chemical composition)	、Positive electrode material、
    Negative electrode material、membrane material、battery cycle times、battery power density、
    self discharge rate、Bipolar plate channel material、Bipolar plate flow channel type、Frame plate structure、
    Battery compression ratio、Electrolyte capacity、Electrolyte concentration、Voltage Efficiency、
    coulombic efficiency	energy efficiency、energy density、discharge capacity、Charging capacity、
    Electrode manufacturer、Specification of electrode substrate material、Electrode base material、
    Density of electrode base material、Other electrode characteristics
    ##Draw a table to summarize data.
[Example]:
```markdown
| doi | type of flow battery (classified by chemical composition) | 
| --- | --- | 
| 10.1002/batt.202200009 | vanadium redo flow battery(vrfb)|
```
    """
    prompt_make_node = """
"You are an expert in creating graphic databases. You can create nodes and relationships based on the information. 
Ideally, all nodes should be one or two words. Return JSON. Json can only contain "start_node",  "relationship", "end_node". 
I am currently creating a knowledge graph. Output the result in JSON format ! Please strictly follow the JSON output format",

"example":
{"start_node":"word","relationship":"word","end_node":"word"},
{"start_node":"Person","relationship":"create","end_node":"database"}
    """
    prompt ="""
"You are an expert in creating graphic databases. You can create nodes and relationships based on the information. 
Ideally, all nodes should be one or two words. Return JSON. Json can only contain "start_node",  "relationship", "end_node". 
I am currently creating a knowledge graph. Output the result in JSON format ! Please strictly follow the JSON output format",

"example":
{"start_node":"word","relationship":"word","end_node":"word"},
{"start_node":"Person","relationship":"create","end_node":"database"}
    """

    # 清空日志文件
    with open('.\\log\\client.log', 'w'):
        pass  # 这将创建一个空文件或清空现有文件
    # 设置日志配置
    logging.basicConfig(filename='./log/client.log', level=logging.INFO, format='%(asctime)s %(filename)s [line:%(lineno)d]  - %(levelname)s - %(message)s')

    # 初始化历史记录并添加系统消息
    # prompt = [system_message]
    for file in tqdm(os.listdir(f"..\\..\\flow_battery_pdf\\new_lvxiuliang")):
        file_path = os.path.join(f"..\\..\\flow_battery_pdf\\new_lvxiuliang", file)

        article_text: []
        article_text_str = ''
        # try:

        article_text = load_PDF(file_path)
        # for i in article_text:
        #     article_text_str += i
        print(file_path, f"pdf pages:{len(article_text)}")
        list_docs = text_splitter(article_text)
        # print(type(list_docs))
        i = 0
        # 获取PDF文件所在的目录和文件名（不带扩展名）
        pdf_dir, pdf_filename = os.path.split(file_path)
        pdf_name, _ = os.path.splitext(pdf_filename)
        # 创建与PDF同名的文件夹
        pdf_path = f"..\\new_lvxiuliang\\{pdf_name}"
        os.makedirs(pdf_path, exist_ok=True)
        for doc in list_docs:
            text = doc
            i += 1
            logging.info(f"file_path{file_path}:{i}:\n {text}")
            response = cc.send_message(content=text, prompt=prompt, temperature=1.0)
            print(f"response:{response}")
            json_path = f"{str(i)}.json"
            txt_path = f"{str(i)}.txt"
            try:
                json_content = json.loads(response)
                # 创建并写入JSON文件，文件名为PDF文件名前缀加上.json
                json_file_path = os.path.join(pdf_path, json_path)
                with open(json_file_path, mode="w", encoding="utf-8") as w:
                    json.dump(json_content, w, ensure_ascii=False, indent=4)
            except json.JSONDecodeError as jsonDecodeError:
                logging.error(jsonDecodeError)
                with open(os.path.join(pdf_path, txt_path), mode="w", encoding="utf-8") as w:
                    w.write(response)

        # except Exception as e:
        #     logging.error(e)
        #     # Construct the full path to the target folder
        #     target_path = os.path.join("..\\..\\flow_battery_pdf\\new_lvxiuliang\\", file)
        #     try:
        #         # Move the file to the target folder
        #         shutil.copy(file_path, target_path)
        #         logging.error(f"An error occurred while moving the file: {e}. File moved successfully to {target_path}")
        #     except Exception as e:
        #         logging.error(f"An error occurred while moving the file: {e}")
        #     continue

