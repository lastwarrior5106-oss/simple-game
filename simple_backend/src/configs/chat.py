import os
from langchain_core.language_models import BaseChatModel
from langchain_groq import ChatGroq
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint



def get_tool_llm(temperature: float = 0.0) -> BaseChatModel:
    
    provider = os.getenv("LLM_PROVIDER", "groq").lower()

    if provider == "groq":
        return ChatGroq(
            model=os.getenv("GROQ_TOOL_MODEL"),
            temperature=temperature,
            api_key=os.getenv("GROQ_API_KEY"),
        )
    elif provider == "huggingface":
        repo_id = os.getenv("HF_TOOL_MODEL")
        safe_temp = temperature if temperature > 0.0 else 0.01
        
        llm = HuggingFaceEndpoint(
            repo_id=repo_id,
            task="text-generation",
            temperature=safe_temp,
            huggingfacehub_api_token=os.getenv("HF_TOKEN"),
            max_new_tokens=1024,
        )
        return ChatHuggingFace(llm=llm)
    else:
        raise ValueError(f"Bilinmeyen sağlayıcı: {provider}")

def get_reasoning_llm(temperature: float = 0.3) -> BaseChatModel:
    
    provider = os.getenv("LLM_PROVIDER", "groq").lower()

    if provider == "groq":
        return ChatGroq(
            model=os.getenv("GROQ_REASON_MODEL"),
            temperature=temperature,
            api_key=os.getenv("GROQ_API_KEY"),
        )
    elif provider == "huggingface":
        repo_id = os.getenv("HF_REASON_MODEL")
        safe_temp = temperature if temperature > 0.0 else 0.01
        
        llm = HuggingFaceEndpoint(
            repo_id=repo_id,
            task="text-generation",
            temperature=safe_temp,
            huggingfacehub_api_token=os.getenv("HF_TOKEN"),
            max_new_tokens=4096,
        )
        return ChatHuggingFace(llm=llm)
    else:
        raise ValueError(f"Bilinmeyen sağlayıcı: {provider}")

def get_router_llm() -> BaseChatModel:
    return get_tool_llm(temperature=0.0)


def get_responder_llm() -> BaseChatModel:
    return get_reasoning_llm(temperature=0.3)