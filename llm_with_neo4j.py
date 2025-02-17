from neo4j import GraphDatabase
import logging
import vllm_client as vc
import chatgpt_client as cc

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
MATCH (a:Node)-[r]->(b:Node)
WHERE a.name = ""
RETURN     
    a.name AS aName, 
    r.relationship AS rRelationship, 
    b.name AS bName"""

kg_prompt = """The following information is obtained through a knowledge graph.
    Please answer the user's question professionally based on the following information.
         If the information is closely related to the question, please refer to known information as much as possible.
         Known relevant information:"""


def get_query(question):
    logging.info(question)
    cypher_messages.clear()
    cypher_messages.append({'role': 'system', 'content': query_prompt})
    cypher_messages.append({'role': 'user', 'content': question})
    cypher_messages.append({'role': 'assistant', 'content': cypher_example})
    return cc.send_message(cypher_messages)


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


def answer_question(kg_records, question):
    logging.info(f"run_cypher_query records:\n{kg_records}")
    kg_records = str(kg_records)[:20000]
    prompt = f"""{kg_prompt}\n {kg_records}"""
    # 遍历列表并替换
    for i, message in enumerate(question_messages):
        if message.get("role") == "system":
            del question_messages[i]  # 替换为新的字典项
            break  # 找到后退出循环
    question_messages.append({'role': 'system', 'content': prompt})
    question_messages.append({'role': 'user', 'content': question})
    response = cc.send_message(question_messages)
    question_messages.append({'role': 'assistant', 'content': response})
    return response


if __name__ == "__main__":
    cypher_messages = []
    question_messages = []
    # 清空日志文件
    filename = '.\\1.log'
    with open(filename, 'w'):
        pass  # 这将创建一个空文件或清空现有文件
    # 设置日志配置
    logging.basicConfig(filename=filename, level=logging.INFO, format='%(asctime)s %(filename)s [line:%(lineno)d]  - %(levelname)s - %(message)s')

    question = "Which refenence mentioned anthraquinone for redox flow batteries?"
    while True:
        # 用户输入问题
        question = input("请输入您的问题（输入'exit'结束对话）：")
        # 如果用户输入 "exit"，退出循环
        if question.lower() == "exit":
            print("对话已结束。")
            break

        query = get_query(question)  # cyphter编辑器模型
        records = run_cypher_query(cypher_query=query)
        answer = answer_question(kg_records=records, question=question)  # kg辅助模型

        logging.info(f"answer:\n\t{answer}")
