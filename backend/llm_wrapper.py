
from typing import Iterator, List
import openai
import os
from openai import AzureOpenAI
from dotenv import load_dotenv

from api_schemas import ChatMessage
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


def _normalize_messages(messages: List[ChatMessage]) -> List[dict]:
    normalized = []
    for m in messages:
        if hasattr(m, "model_dump"):
            normalized.append(m.model_dump())
        elif isinstance(m, dict):
            normalized.append(m)
        else:
            # Fallback: best-effort cast
            normalized.append({"role": getattr(m, "role", None), "content": getattr(m, "content", None)})
    return normalized
    

def stream_llm(messages: List[ChatMessage], model: str = "gpt-4.1") -> Iterator[str]:
    normalized_messages = _normalize_messages(messages)
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

        obj = {"messages": normalized_messages}
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
            yield f"[MedGEMMA Error] {r.status_code}: {r.text}"
            return

        if "choices" in data and data["choices"] and "message" in data["choices"][0]:
            full_text = data["choices"][0]["message"].get("content", str(data))
        elif "output" in data:
            full_text = data["output"]
        else:
            full_text = str(data)

        chunk_size = 512
        for i in range(0, len(full_text), chunk_size):
            yield full_text[i:i + chunk_size]
        return

    config = MODEL_CONFIGS.get(model)
    if not config or not config["api_key"] or not config["endpoint"]:
        raise ValueError(f"Missing API key or endpoint for model: {model}")

    client = AzureOpenAI(
        api_key=config["api_key"],
        api_version=config["api_version"],
        azure_endpoint=config["endpoint"]
    )

    payload = {
        "model": config["deployment"],
        "messages": normalized_messages,
        "stream": True
    }
    if model in ["gpt-4.1", "gpt-4.1-mini", "gpt-4.1-nano"]:
        payload["temperature"] = 0.7

    response = client.chat.completions.create(**payload)
    for chunk in response:
        if not chunk.choices:
            continue
        delta = chunk.choices[0].delta
        if delta and delta.content:
            yield delta.content