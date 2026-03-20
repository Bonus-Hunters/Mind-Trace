import os
from langchain_ollama import OllamaLLM, OllamaEmbeddings
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

from core.rag.llm_config import LLMConfig


def get_llm(config: LLMConfig):
    if config.provider == "ollama":
        return OllamaLLM(
            model=config.model,
            temperature=config.temperature
        )

    elif config.provider == "openai":
        if not config.api_key:
            raise ValueError("OpenAI API key is required")

        os.environ["OPENAI_API_KEY"] = config.api_key
        return ChatOpenAI(
            model=config.model,
            temperature=config.temperature
        )

    elif config.provider == "gemini":
        if not config.api_key:
            raise ValueError("Gemini API key is required")

        os.environ["GOOGLE_API_KEY"] = config.api_key
        return ChatGoogleGenerativeAI(
            model=config.model,
            temperature=config.temperature
        )

    else:
        raise ValueError(f"Unsupported LLM provider: {config.provider}")


def get_embeddings(config: LLMConfig):
    if config.provider == "ollama":
        return OllamaEmbeddings(model=config.model)

    elif config.provider == "openai":
        os.environ["OPENAI_API_KEY"] = config.api_key
        return OpenAIEmbeddings(model=config.model)

    elif config.provider == "gemini":
        os.environ["GOOGLE_API_KEY"] = config.api_key
        return GoogleGenerativeAIEmbeddings(model=config.model)

    else:
        raise ValueError(f"Unsupported embedding provider: {config.provider}")

import subprocess

def pull_model(model_name):
    subprocess.run(["ollama", "pull", model_name], check=True)
