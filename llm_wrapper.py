
import openai
import os
from openai import AzureOpenAI
from dotenv import load_dotenv
load_dotenv()

import requests


# Map each model to its deployment name, API key, and endpoint
MODEL_CONFIGS = {
    "gpt-4.1": {
        "deployment": "gpt-4.1",  # Replace with your deployment name if different
        "api_key": os.getenv("AZURE_OPENAI_API_KEY"),
        "endpoint": os.getenv("AZURE_OPENAI_ENDPOINT"),
        "api_version": "2024-12-01-preview"
    },
    "gpt-4.1-mini": {
        "deployment": "gpt-4.1-mini",  # Replace with your deployment name if different
        "api_key": os.getenv("AZURE_OPENAI_API_KEY"),
        "endpoint": os.getenv("AZURE_OPENAI_ENDPOINT"),
        "api_version": "2024-12-01-preview"
    },
    "gpt-4.1-nano": {
        "deployment": "gpt-4.1-nano",  # Replace with your deployment name if different
        "api_key": os.getenv("AZURE_OPENAI_API_KEY"),
        "endpoint": os.getenv("AZURE_OPENAI_ENDPOINT"),
        "api_version": "2024-12-01-preview"
    },
    "gpt-5": {
        "deployment": "gpt-5",  # Replace with your deployment name if different
        "api_key": os.getenv("AZURE_OPENAI_API_KEY_GPT_5"),
        "endpoint": os.getenv("AZURE_OPENAI_ENDPOINT_GPT_5"),
        "api_version": "2025-01-01-preview"
    },
    "gpt-5-mini": {
        "deployment": "gpt-5-mini",  # Replace with your deployment name if different
        "api_key": os.getenv("AZURE_OPENAI_API_KEY_GPT_5_MINI"),
        "endpoint": os.getenv("AZURE_OPENAI_ENDPOINT_GPT_5_MINI"),
        "api_version": "2025-04-01-preview"
    },
    "gpt-5-nano": {
        "deployment": "gpt-5-nano",  # Replace with your deployment name if different
        "api_key": os.getenv("AZURE_OPENAI_API_KEY_GPT_5_NANO"),
        "endpoint": os.getenv("AZURE_OPENAI_ENDPOINT_GPT_5_NANO"),
        "api_version": "2025-01-01-preview"
    },
    "medgemma-27b-multimodal7": {
        "url": os.getenv("MEDGEMMA_MODEL_URL"),
        "api_key": "",  # Always blank
        "verify_tls": True
    },
}


def query_llm(messages, model="gpt-4.1"):
    if model == "medgemma-27b-multimodal7":
        config = MODEL_CONFIGS[model]
        url = config["url"]
        api_key = config["api_key"]
        verify_tls = config["verify_tls"]
        def _chat_headers():
            h = {"Accept": "application/json"}
            if api_key:
                h["Authorization"] = f"Bearer {api_key}"
            return h
        obj = {"messages": messages}
        timeout = 120
        r = requests.post(
            url,
            json=obj,
            headers=_chat_headers(),
            timeout=timeout,
            verify=verify_tls,
        )
        try:
            data = r.json()
        except Exception:
            return f"[MedGEMMA Error] {r.status_code}: {r.text}"
        # Try to extract response in OpenAI style, fallback to raw text
        if "choices" in data and data["choices"] and "message" in data["choices"][0]:
            return data["choices"][0]["message"].get("content", str(data))
        elif "output" in data:
            return data["output"]
        return str(data)
    # Default: OpenAI/Azure models
    config = MODEL_CONFIGS.get(model)
    if not config or not config["api_key"] or not config["endpoint"]:
        raise ValueError(f"Missing API key or endpoint for model: {model}")
    client = AzureOpenAI(
        api_key=config["api_key"],
        api_version=config["api_version"],
        azure_endpoint=config["endpoint"]
    )
    # Only set temperature for models that support it
    if model in ["gpt-4.1", "gpt-4.1-mini", "gpt-4.1-nano"]:
        response = client.chat.completions.create(
            model=config["deployment"],
            messages=messages,
            temperature=0.7
        )
    else:
        response = client.chat.completions.create(
            model=config["deployment"],
            messages=messages
        )
    return response.choices[0].message.content

