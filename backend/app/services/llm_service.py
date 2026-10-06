import os
import logging
from typing import List, Optional
from sentence_transformers import SentenceTransformer

from app.core.config import settings

logger = logging.getLogger(__name__)


class LLMServiceError(Exception):
    """Custom exception for LLM & Embedding service failures."""
    pass


class EmbeddingService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EmbeddingService, cls).__new__(cls)
            logger.info(f"Loading embedding model: {settings.EMBEDDING_MODEL}")
            cls._instance.model = SentenceTransformer(settings.EMBEDDING_MODEL)
        return cls._instance

    def embed_text(self, text: str) -> List[float]:
        try:
            vector = self.model.encode(text, convert_to_numpy=True)
            return vector.tolist()
        except Exception as e:
            raise LLMServiceError(f"Embedding generation failed: {str(e)}")

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        try:
            vectors = self.model.encode(texts, convert_to_numpy=True)
            return vectors.tolist()
        except Exception as e:
            raise LLMServiceError(f"Batch embedding generation failed: {str(e)}")


class LLMProvider:
    @staticmethod
    def generate_answer(prompt: str, system_prompt: str) -> str:
        provider = (settings.LLM_PROVIDER or "gemini").lower()

        if provider == "gemini":
            return LLMProvider._call_gemini(prompt, system_prompt)
        elif provider == "openai":
            return LLMProvider._call_openai(prompt, system_prompt)
        elif provider == "groq":
            return LLMProvider._call_groq(prompt, system_prompt)
        else:
            raise LLMServiceError(f"Unsupported LLM provider: '{provider}'. Choose gemini, openai, or groq.")

    @staticmethod
    def _call_gemini(prompt: str, system_prompt: str) -> str:
        api_key = settings.GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise LLMServiceError("GEMINI_API_KEY is missing. Please set it in your .env file.")

        full_prompt = f"{system_prompt}\n\nUser Question & Context:\n{prompt}"
        
        # Try new google-genai client first, fallback to google.generativeai
        try:
            from google import genai
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=full_prompt,
            )
            if response and response.text:
                return response.text.strip()
            raise LLMServiceError("Gemini returned an empty response.")
        except ImportError:
            try:
                import google.generativeai as genai_old
                genai_old.configure(api_key=api_key)
                model = genai_old.GenerativeModel(settings.GEMINI_MODEL)
                response = model.generate_content(full_prompt)
                if response and response.text:
                    return response.text.strip()
                raise LLMServiceError("Gemini returned an empty response.")
            except Exception as ex:
                raise LLMServiceError(f"Gemini API error: {str(ex)}")
        except Exception as e:
            raise LLMServiceError(f"Gemini API error: {str(e)}")

    @staticmethod
    def _call_openai(prompt: str, system_prompt: str) -> str:
        api_key = settings.OPENAI_API_KEY or os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise LLMServiceError("OPENAI_API_KEY is missing. Please set it in your .env file.")

        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1
            )
            content = response.choices[0].message.content
            if content:
                return content.strip()
            raise LLMServiceError("OpenAI returned an empty response.")
        except Exception as e:
            raise LLMServiceError(f"OpenAI API error: {str(e)}")

    @staticmethod
    def _call_groq(prompt: str, system_prompt: str) -> str:
        api_key = settings.GROQ_API_KEY or os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise LLMServiceError("GROQ_API_KEY is missing. Please set it in your .env file.")

        try:
            from groq import Groq
            client = Groq(api_key=api_key)
            response = client.chat.completions.create(
                model=settings.GROQ_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1
            )
            content = response.choices[0].message.content
            if content:
                return content.strip()
            raise LLMServiceError("Groq returned an empty response.")
        except Exception as e:
            raise LLMServiceError(f"Groq API error: {str(e)}")
