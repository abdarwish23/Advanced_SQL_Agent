# app/utils/llm_utils.py

from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_groq import ChatGroq
from langchain_ollama import ChatOllama
from app.config import Config

def get_llm(provider, model_name):
    temperature = Config.LLM_TEMPERATURE

    if provider == 'openai':
        return ChatOpenAI(model_name=model_name, temperature=temperature)
    elif provider == 'anthropic':
        return ChatAnthropic(model=model_name, temperature=temperature)
    elif provider == 'groq':
        return ChatGroq(model_name=model_name, temperature=temperature)
    elif provider == 'ollama':
        return ChatOllama(model=model_name, temperature=temperature)
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")


