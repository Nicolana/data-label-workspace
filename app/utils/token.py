import tiktoken
from typing import List, Dict

def count_tokens(messages: List[Dict[str, str]]) -> int:
    """计算消息列表的token数量"""
    enc = tiktoken.encoding_for_model("gpt-3.5-turbo")
    total_tokens = 0
    
    for message in messages:
        # 计算消息内容的 tokens
        total_tokens += len(enc.encode(message["content"]))
        
        # 计算角色名称的 tokens
        total_tokens += len(enc.encode(message["role"]))
        
        # 添加一些系统消息的 tokens
        if message["role"] == "system":
            total_tokens += 4
        elif message["role"] == "user":
            total_tokens += 4
        elif message["role"] == "assistant":
            total_tokens += 4
    
    return total_tokens 