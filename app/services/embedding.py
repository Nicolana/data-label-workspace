import numpy as np
import torch
from sentence_transformers import SentenceTransformer
from app.core.config import settings

class EmbeddingService:
    def __init__(self):
        self.model = SentenceTransformer(settings.SENTENCE_TRANSFORMER_MODEL)
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.model.to(self.device)
    
    def get_embedding(self, text: str) -> np.ndarray:
        """获取文本的向量表示"""
        with torch.no_grad():
            embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.astype(np.float32) 