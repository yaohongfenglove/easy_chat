import os
from typing import List

import gradio as gr
import openai
import tiktoken
from openai import OpenAIError
from tenacity import retry, wait_random, stop_after_attempt, retry_if_exception_type

try:
    from conf.config import BASE_DIR, config, logger
except ModuleNotFoundError:
    import os
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # 离开IDE也能正常导入自己定义的包
    from conf.config import BASE_DIR, config, logger


openai.api_base = os.getenv("OPENAI_API_BASE") if os.getenv("OPENAI_API_BASE") else config["openai"]["open_ai_proxy"]["api_base"]
openai.api_key = os.getenv("OPENAI_API_KEY") if os.getenv("OPENAI_API_KEY") else config["openai"]["open_ai_proxy"]["api_key"]


def num_tokens_from_messages(messages, model="gpt-3.5-turbo-0613"):
    """Return the number of tokens used by a list of messages."""
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        raise ValueError(f"{model} model not found.")

    if model in {
        "gpt-3.5-turbo-0613",
        "gpt-3.5-turbo-16k-0613",
        "gpt-4-0314",
        "gpt-4-32k-0314",
        "gpt-4-0613",
        "gpt-4-32k-0613",
    }:
        tokens_per_message = 3
        tokens_per_name = 1

    elif model == "gpt-3.5-turbo-0301":
        tokens_per_message = 4  # every message follows <|start|>{role/name}\n{content}<|end|>\n
        tokens_per_name = -1  # if there's a name, the role is omitted
    elif "gpt-3.5-turbo" in model:
        print("Warning: gpt-3.5-turbo may update over time. Returning num tokens assuming gpt-3.5-turbo-0613.")
        return num_tokens_from_messages(messages, model="gpt-3.5-turbo-0613")
    elif "gpt-4" in model:
        print("Warning: gpt-4 may update over time. Returning num tokens assuming gpt-4-0613.")
        return num_tokens_from_messages(messages, model="gpt-4-0613")
    else:
        raise NotImplementedError(
            f"""num_tokens_from_messages() is not implemented for model {model}. See https://github.com/openai/openai-python/blob/main/chatml.md for information on how messages are converted to tokens."""
        )
    num_tokens = 0
    for message in messages:
        num_tokens += tokens_per_message
        for key, value in message.items():
            num_tokens += len(encoding.encode(value))
            if key == "name":
                num_tokens += tokens_per_name
    num_tokens += 3  # every reply is primed with <|start|>assistant<|message|>
    return num_tokens


def build_messages(question: str, chat_history: List[List[str]]):
    """
    结合历史消息，生成查询内容
    :param question: 待查询的问题
    :param chat_history: 历史消息列表，[["question1", "answer1"], ["question2", "answer2"]]
    :return: 含历史消息的查询内容
    """

    messages = list()
    for item in chat_history:
        messages.append({"role": "user", "content": f"{item[0]}"})
        messages.append({"role": "assistant", "content": f"{item[1]}"})

    messages.append({"role": "user", "content": f"{question}"})

    num_tokens = num_tokens_from_messages(messages, model=config["openai"]["open_ai_chat_model"])
    logger.info(f"prompt的token计数：{num_tokens}")

    max_tokens = config["openai"]["max_tokens"]
    if num_tokens >= max_tokens:
        raise ValueError(f"超出设定的最大token数{max_tokens}了：当前为{num_tokens}")

    return messages


@retry(retry=retry_if_exception_type(OpenAIError), reraise=True,
       wait=wait_random(min=config["openai"]["openai_retry"]["min_wait"], max=config["openai"]["openai_retry"]["max_wait"]),
       stop=stop_after_attempt(config["openai"]["openai_retry"]["max_attempt_number"]))
def get_bot_message(question: str, chat_history: List[List[str]]):
    """
    结合历史消息，获取gpt答复
    :param question: 待查询的问题
    :param chat_history: 历史消息列表，[["question1", "answer1"], ["question2", "answer2"]]
    :return: 答复
    """
    messages = build_messages(question=question, chat_history=chat_history)

    try:
        response = openai.ChatCompletion.create(
            model=config["openai"]["open_ai_chat_model"],  # 对话模型的名称
            messages=messages,
            temperature=0,
        )
        response_content = response['choices'][0]['message']['content']
    except OpenAIError as e:
        raise ValueError(f"获取回复失败：{str(e)}")

    return response_content


def respond(message: str, chat_history: List[List[str]]):
    """
    获取gpt的响应
    :param message: 用户消息
    :param chat_history: 历史消息列表，[["question1", "answer1"], ["question2", "answer2"]]
    :return:
    """
    try:
        bot_message = get_bot_message(message, chat_history)

        chat_history.append([message, bot_message])

        logger.info(f"{chat_history}")

        message = ""
    except Exception as e:
        raise gr.Error(str(e))

    return message, chat_history


def main():
    with gr.Blocks(theme=gr.themes.Base(), title="EasyChat") as app:
        gr.Markdown("# <center>EasyChat")

        # 输入输出组件
        chat_history = gr.Chatbot(label="聊天记录")
        message = gr.Textbox(label="", placeholder="请输入...")

        # 动作按钮
        send = gr.Button("发送", variant="primary")

        # 事件绑定
        send.click(fn=respond,
                   inputs=[message, chat_history],
                   outputs=[message, chat_history])

    app.queue(concurrency_count=10, api_open=False)

    app.launch(
        server_name="0.0.0.0", server_port=7099,  # Hagging Face托管时注释掉这一行
        auth=("admin", "1003"),
        favicon_path=os.path.join(BASE_DIR, "logo.png"),
        show_api=False
    )


if __name__ == "__main__":
    main()
