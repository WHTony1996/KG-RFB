import os
import logging
import httpx

# --- Setup Logging ---
# Provides visibility into which model is being called and any potential errors.
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Environment Variable Loading and Client Initialization ---
# Best practice: Load API keys from environment variables.
# This section attempts to initialize clients for all potential providers.
# If a key is missing or a library is not installed, the provider will be gracefully skipped.

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")  # Example for future extension

# --- Client Storage ---
clients = {}

# --- Initialize DeepSeek Client (OpenAI Compatible) ---
if DEEPSEEK_API_KEY:
    try:
        clients['deepseek'] = {
            "client": httpx.Client(),  # Placeholder, OpenAI client handles this
            "api_client": "openai",
            "model": "deepseek-chat",
            "instance": "https://api.deepseek.com"
        }
        logging.info("DeepSeek client configured.")
    except ImportError:
        logging.warning("DeepSeek client could not be initialized. `openai` library may be missing.")
    except Exception as e:
        logging.error(f"Error initializing DeepSeek client: {e}")

# --- Initialize OpenAI Client ---
if OPENAI_API_KEY:
    try:
        from openai import OpenAI

        clients['openai'] = OpenAI(api_key=OPENAI_API_KEY)
        logging.info("OpenAI client initialized.")
    except ImportError:
        logging.warning("OpenAI client could not be initialized. `openai` library is not installed.")
    except Exception as e:
        logging.error(f"Error initializing OpenAI client: {e}")

# --- Initialize Google Gemini Client ---
if GOOGLE_API_KEY:
    try:
        import google.generativeai as genai

        genai.configure(api_key=GOOGLE_API_KEY)
        clients['gemini'] = genai.GenerativeModel('gemini-pro')
        logging.info("Google Gemini client initialized.")
    except ImportError:
        logging.warning(
            "Google Gemini client could not be initialized. `google.generativeai` library is not installed.")
    except Exception as e:
        logging.error(f"Error initializing Google Gemini client: {e}")

# --- Initialize Anthropic Client (Example for future extension) ---
if ANTHROPIC_API_KEY:
    try:
        from anthropic import Anthropic

        clients['anthropic'] = Anthropic(api_key=ANTHROPIC_API_KEY)
        logging.info("Anthropic client initialized.")
    except ImportError:
        logging.warning("Anthropic client could not be initialized. `anthropic` library is not installed.")
    except Exception as e:
        logging.error(f"Error initializing Anthropic client: {e}")


def _call_openai_compatible(client_name, messages, model, temperature):
    """Handles calls to OpenAI and OpenAI-compatible APIs like DeepSeek."""
    from openai import OpenAI

    config = clients[client_name]
    api_key = DEEPSEEK_API_KEY if client_name == 'deepseek' else OPENAI_API_KEY

    client = OpenAI(api_key=api_key, base_url=config.get("instance"))

    completion = client.chat.completions.create(
        model=config["model"],
        messages=messages,
        temperature=temperature
    )
    return completion.choices[0].message.content


def _call_google_gemini(client, messages, temperature):
    """Handles calls to Google's Gemini API."""
    # Gemini uses a slightly different message format and response structure.
    response = client.generate_content(messages)
    return response.text


LLM_PROVIDERS = [
    {
        "name": "DeepSeek-V3",
        "client_key": "deepseek",
        "call_function": _call_openai_compatible,
        "model": "deepseek-chat"  # As per DeepSeek documentation
    },
    {
        "name": "OpenAI GPT-4",
        "client_key": "openai",
        "call_function": _call_openai_compatible,
        "model": "gpt-4-turbo"  # Example model, can be changed
    },
    {
        "name": "Google Gemini Pro",
        "client_key": "gemini",
        "call_function": _call_google_gemini,
        "model": "gemini-pro"
    }
]


def send_message(messages, temperature=0.7):
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

            # For OpenAI-compatible clients, we pass the name to handle different configs
            if provider["call_function"] == _call_openai_compatible:
                response = provider["call_function"](client_key, messages, provider["model"], temperature)
            else:
                response = provider["call_function"](client_instance, messages, temperature)

            logging.info(f"Successfully received response from {provider_name}.")
            return response

        except Exception as e:
            logging.error(f"Failed to call {provider_name}. Error: {e}")
            # The loop will automatically continue to the next provider
            continue

    # This part is reached only if all providers in the loop have failed
    raise RuntimeError("All LLM providers failed to generate a response.")


def chat_with_model():
    """A simple multi-turn conversation loop to demonstrate the fallback mechanism."""
    chat_history = []
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit"]:
            print("Exiting chat.")
            break

        chat_history.append({'role': 'user', 'content': user_input})

        try:
            # Call the robust send_message function
            model_response = send_message(chat_history)

            print(f"Assistant: {model_response}")

            # Add the model's response to the history for context
            chat_history.append({'role': 'assistant', 'content': model_response})

        except RuntimeError as e:
            print(f"Error: {e}")
            # Optionally, break the loop or allow the user to try again
            break
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            break


if __name__ == "__main__":
    print("Starting chat session with LLM fallback system.")
    print("Set your API keys as environment variables: DEEPSEEK_API_KEY, OPENAI_API_KEY, GOOGLE_API_KEY")
    print("Enter 'exit' or 'quit' to end the session.")
    chat_with_model()