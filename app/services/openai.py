import json
from typing import List, Dict, Any, AsyncGenerator
from openai import OpenAI
from app.core.config import settings

class OpenAIService:
    def __init__(self):
        self.client = OpenAI(
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_API_HOST
        )
    
    async def generate_chat_completion(
        self,
        messages: List[Dict[str, str]],
        stream: bool = False,
        temperature: float = 0.7,
        max_tokens: int = 4000
    ) -> AsyncGenerator[str, None]:
        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=messages,
                stream=stream,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            if stream:
                for chunk in response:
                    if chunk.choices[0].delta.content is not None:
                        yield f"data: {json.dumps({'content': chunk.choices[0].delta.content})}\n\n"
            else:
                yield f"data: {json.dumps({'content': response.choices[0].message.content})}\n\n"
                
        except Exception as e:
            if stream:
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
            raise e 