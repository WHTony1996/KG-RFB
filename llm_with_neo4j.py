from neo4j import GraphDatabase
import logging
import chat_client as cc
import re

query_prompt = """I am working with a Neo4j database and would like you to help me construct a Cypher query based on the information I provide. Please generate a syntactically correct Cypher query statement that can be executed directly in the Neo4j environment. Ensure that the query is precise and optimized for performance. I will describe the information I need to retrieve; please make sure the generated Cypher query accurately reflects my requirements.
Now I'm going to tell you a little bit about this knowledge graph.
1. This knowledge graph is a flow battery graph based on research literature on flow batteries.
2. All the content is stored in the name attribute of node.
3. Relationships can be unrestricted in the query process to expand the search scope.
4. It is recommended that you search not only for relationships that start from the subject, but also for relationships that point to the subject.
5. All relations is stored in the relationship attribute of relationship.

You generate a Cypher query related to the problem. The query scope of the statement can be as broad as possible. We will also have personnel to process the data.
Please define only one node variable in Cypher's where.

please only answer the cypher code. Don't have any grammar problems. with out any title, such as cypher ```.
"""

cypher_example = """
MATCH (a)-[r]->(b)
WHERE a.name CONTAINS ""
RETURN     
    a.name AS aName, 
    r.relationship AS rRelationship, 
    b.name AS bName"""

kg_prompt = """The following information is obtained through a knowledge graph.
    Please answer the user's question professionally based on the following information.
         If the information is closely related to the question, please refer to known information as much as possible.
         Known relevant information:"""


def clean_cypher_response(response_text):
    """
    清洗 LLM 的回复，只提取 Cypher 代码部分
    """
    # 1. 如果包含 Markdown 代码块 (```cypher ... ```)，用正则提取中间的内容
    pattern = r"```(?:cypher)?\s*(.*?)```"
    match = re.search(pattern, response_text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()

    # 2. 如果没有 Markdown，尝试寻找 'MATCH' 关键词的位置
    # 因为 Cypher 99% 都是以 MATCH 开头的
    match_index = response_text.find("MATCH")
    if match_index != -1:
        # 从 MATCH 开始截取到最后
        return response_text[match_index:].strip()

    # 3. 如果实在找不到，就原样返回（或者返回空字符串防止报错）
    return response_text.strip()


def get_query(question):
    logging.info(question)
    messages = []
    messages.append({'role': 'system', 'content': query_prompt})
    messages.append({'role': 'user', 'content': question})
    messages.append({'role': 'assistant', 'content': cypher_example})
    raw_response = cc.send_message(messages)
    clean_response = clean_cypher_response(raw_response)
    return clean_response


def run_cypher_query(cypher_query, uri="bolt://localhost:7687", user="neo4j", password="bjutB406"):
    """
    Executes a Cypher query against a Neo4j database and returns the result.

    :param cypher_query: A string containing the Cypher query to execute.
    :param uri: The URI of the Neo4j instance.
    :param user: Username for authentication.
    :param password: Password for authentication.
    :return: Query result as a list of dictionaries.
    """
    logging.info(cypher_query)
    # Initialize the driver
    driver = GraphDatabase.driver(uri, auth=(user, password))

    try:
        with driver.session() as session:
            # Execute the Cypher query
            result = session.run(cypher_query)
            # Extract records into a list of dictionaries
            records = [record.data() for record in result]
            # print(records)
            return records
    finally:
        # Ensure the driver is closed after executing the query
        driver.close()


def answer_question(kg_records, question, chat_history):
    logging.info(f"run_cypher_query records:\n{kg_records}")
    kg_records_str = str(kg_records)[:20000]
    current_system_content = f"{kg_prompt}\n {kg_records_str}"
    messages_to_send = [{'role': 'system', 'content': current_system_content}]
    messages_to_send.extend(chat_history)
    messages_to_send.append({'role': 'user', 'content': question})
    response = cc.send_message(messages_to_send)
    chat_history.append({'role': 'user', 'content': question})
    chat_history.append({'role': 'assistant', 'content': response})
    return response


def main():
    chat_history = []
    filename = '.\\1.log'
    with open(filename, 'w'):
        pass
    logging.basicConfig(filename=filename, level=logging.INFO,
                        format='%(asctime)s %(filename)s [line:%(lineno)d]  - %(levelname)s - %(message)s')

    # question = "Which refenence mentioned anthraquinone for redox flow batteries?"
    while True:
        try:
            question = input("Please enter your question (enter 'exit' to end the conversation):")
            if question.lower() == "exit":
                print("The conversation has ended.")
                break

            query = get_query(question)  # Cypher Editor Model
            records = run_cypher_query(cypher_query=query)
            # KG auxiliary model
            answer = answer_question(kg_records=records, question=question, chat_history=chat_history)
            # print(f"Assistant: {answer}")
            logging.info(f"answer:\n\t{answer}")
        except Exception as e:
            # print(f"An error occurred: {e}")
            logging.error(f"Main Loop Error: {e}")


if __name__ == "__main__":
    logging.basicConfig(filename='error.log', level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')
    main()

