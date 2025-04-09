import httpx
from openai import OpenAI
import os

# 初始化消息列表
messages = []

# 配置 OpenAI 客户端，使用代理
# client = OpenAI(
#     api_key = "",
#     http_client=httpx.Client(
#         proxy="",  # 代理服务器的URL
#         transport=httpx.HTTPTransport(local_address="0.0.0.0"),  # 本地地址配置
#         verify=False  # 禁用SSL证书验证（不推荐在生产环境中使用）
#     )
# )


# 配置 阿里云 客户端，使用代理,deepseek
client = OpenAI(
    # 若没有配置环境变量，请用百炼API Key将下行替换为：api_key="sk-xxx",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    api_key = os.getenv("OPENAI_API_KEY"),
    # http_client=httpx.Client(
    #     proxy="",  # 代理服务器的URL
    #     transport=httpx.HTTPTransport(local_address="0.0.0.0"),  # 本地地址配置
    #     verify=False  # 禁用SSL证书验证（不推荐在生产环境中使用）
    #     )
)


def send_message(messages, temperature=1.0):
    # 创建一个聊天完成请求
    completion = client.chat.completions.create(
        model="deepseek-v3",
        messages=messages,
        # stream=True,
        temperature=temperature,
        # top_p=0.8,
        # max_tokens=2048,
        # extra_body={
        #     "repetition_penalty": 1.05,
        # },
        # response_format={"type": "json_object"}
    )
    response = completion.choices[0].message.content
    return response


# 多轮对话
def chat_with_model():
    while True:
        # 用户输入问题
        user_input = input("请输入您的问题（输入'exit'结束对话）：")

        # 如果用户输入 "exit"，退出循环
        if user_input.lower() == "exit":
            print("对话已结束。")
            break

        # 将用户输入添加到消息列表中
        messages.append({'role': 'user', 'content': user_input})

        # 调用模型生成回复
        completion = client.chat.completions.create(
            model="deepseek-v3",  # 可按需更换模型名称
            messages=messages
        )

        # # 打印思考过程
        # print("="*20 + "思考过程" + "="*20)
        # if hasattr(completion.choices[0].message, 'reasoning_content'):
        #     print(completion.choices[0].message.reasoning_content)

        # 打印最终答案
        print("=" * 20 + "最终答案" + "=" * 20)
        print(completion.choices[0].message.content)

        # 将模型回复添加到消息列表中，以便实现上下文管理
        messages.append({'role': 'assistant', 'content': completion.choices[0].message.content})
        print("messagess: ", messages)


if __name__ == "__main__":
    chat_with_model()

