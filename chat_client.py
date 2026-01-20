import os
import logging
import httpx
from openai import OpenAI

from dotenv import load_dotenv
load_dotenv()

# --- Setup Logging ---
# Provides visibility into which model is being called and any potential errors.
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Environment Variable Loading and Client Initialization ---
# Best practice: Load API keys from environment variables.
# This section attempts to initialize clients for all potential providers.
# If a key is missing or a library is not installed, the provider will be gracefully skipped.

ALIYUN_API_KEY = os.getenv("ALIYUN_API_KEY")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# --- Client Storage ---
clients = {}

# --- Initialize DeepSeek Client (OpenAI Compatible) ---
if ALIYUN_API_KEY:
    try:
        logging.info("Configuring Aliyun DeepSeek client...")
        # 阿里云使用了不同的 ID 命名，为了防止冲突，我们在字典里叫它 'aliyun_deepseek'
        clients['aliyun_deepseek'] = OpenAI(
            api_key=ALIYUN_API_KEY,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
        )
        logging.info("Aliyun DeepSeek client initialized.")
    except Exception as e:
        logging.error(f"Error initializing Aliyun DeepSeek client: {e}")

# --- Initialize DeepSeek Client (OpenAI Compatible) ---
if DEEPSEEK_API_KEY:
    try:
        logging.info("Configuring Official DeepSeek client...")
        clients['official_deepseek'] = OpenAI(
            api_key=DEEPSEEK_API_KEY,
            base_url="https://api.deepseek.com"
        )
        logging.info("Official DeepSeek client initialized.")
    except Exception as e:
        logging.error(f"Error initializing Official DeepSeek client: {e}")


# --- Initialize Google Gemini Client ---
if GOOGLE_API_KEY:
    try:
        from google import genai
        logging.info("Configuring Google Gemini client (New SDK)...")
        clients['gemini'] = genai.Client(api_key=GOOGLE_API_KEY)
        logging.info("Google Gemini client initialized.")
    except ImportError:
        logging.warning(
            "Google Gemini client could not be initialized. `google.generativeai` library is not installed.")
    except Exception as e:
        logging.error(f"Error initializing Google Gemini client: {e}")


# --- Initialize OpenAI Client ---
if OPENAI_API_KEY:
    try:
        clients['openai'] = OpenAI(api_key=OPENAI_API_KEY)
        logging.info("OpenAI client initialized.")
    except Exception as e:
        logging.error(f"Error initializing OpenAI client: {e}")


def _call_openai_compatible(client, messages, model, temperature):
    """
    Handles calls to OpenAI compatible clients.
    """
    completion = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature
    )
    return completion.choices[0].message.content


def _call_google_gemini(client, messages, model, temperature):
    """Handles calls to Google's Gemini API."""
    # Gemini uses a slightly different message format and response structure.
    from google.genai import types
    prompt = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=temperature
        )
    )
    return response.text


LLM_PROVIDERS = [
    {
        "name": "Aliyun DeepSeek-V3",
        "client_key": "aliyun_deepseek",
        "call_function": _call_openai_compatible,
        "model": "deepseek-v3"
    },
    {
        "name": "DeepSeek-V3",
        "client_key": "official_deepseek",
        "call_function": _call_openai_compatible,
        "model": "deepseek-chat"  # As per DeepSeek documentation
    },
    {
        "name": "OpenAI gpt-5-nano",
        "client_key": "openai",
        "call_function": _call_openai_compatible,
        "model": "gpt-5-nano"  # Example model, can be changed
    },
    {
        "name": "gemini-2.5-flash",
        "client_key": "gemini",
        "call_function": _call_google_gemini,
        "model": "gemini-2.5-flash"
    }
]


def send_message(messages, temperature=1.0):
    # print("messages:", messages)
    """
    Sends a message to a series of LLM providers with a fallback mechanism.

    It tries to call the providers in the order defined in LLM_PROVIDERS.
    If a call fails, it logs the error and automatically tries the next provider.

    Args:
        messages (list): A list of message dictionaries (e.g., [{'role': 'user', 'content': '...'}])
        temperature (float): The generation temperature.

    Returns:
        str: The content of the successful response.

    Raises:
        RuntimeError: If all configured LLM providers fail to respond.
    """
    for provider in LLM_PROVIDERS:
        provider_name = provider["name"]
        client_key = provider["client_key"]

        # Check if the client for this provider was successfully initialized
        if client_key not in clients:
            logging.warning(f"Skipping {provider_name} because its client is not available.")
            continue

        try:
            logging.info(f"Attempting to call {provider_name}...")
            client_instance = clients[client_key]

            # if provider["client_key"] == 'gemini':
            #     response = provider["call_function"](client_instance, messages, provider["model"])
            # else:
            response = provider["call_function"](client_instance, messages, provider["model"], temperature)

            logging.info(f"Successfully received response from {provider_name}.")
            # print(f"Assistant: {response}")
            return response

        except Exception as e:
            logging.error(f"Failed to call {provider_name}. Error: {e}")
            continue

    raise RuntimeError("All LLM providers failed to generate a response.")


def chat_with_model():
    """A simple multi-turn conversation loop to demonstrate the fallback mechanism."""
    chat_history = []
    print("\n--- Chat System Ready (Type 'exit' to quit) ---")
    while True:
        try:
            user_input = input("You: ")
            if user_input.lower() in ["exit", "quit"]:
                print("Exiting chat.")
                break
        except EOFError:
            break

        # Add the model's response to the history for context
        chat_history.append({'role': 'user', 'content': user_input})
        try:
            model_response = send_message(chat_history)
            print(f"Assistant: {model_response}")
            chat_history.append({'role': 'assistant', 'content': model_response})
        except RuntimeError as e:
            print(f"Error: {e}")
            break


if __name__ == "__main__":
    print("Starting chat session with LLM fallback system.")
    print("Set your API keys as environment variables: DEEPSEEK_API_KEY, OPENAI_API_KEY, GOOGLE_API_KEY")
    print("Enter 'exit' or 'quit' to end the session.")
    chat_with_model()