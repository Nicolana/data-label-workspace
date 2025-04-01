import os
import re
import fnmatch
from typing import List, Dict, Any, Optional
import docx
import PyPDF2
import chardet
from pathlib import Path

from app.models.index import ChunkingStrategy, ChunkingConfig, DocumentCreate


class DocumentProcessor:
    """
    文档处理器，负责处理上传的文件并进行切片
    """
    
    # 代码文件扩展名列表
    CODE_EXTENSIONS = [
        # Python
        '.py', '.pyx', '.pyi', '.pyw', 
        # Web
        '.html', '.htm', '.css', '.js', '.jsx', '.ts', '.tsx', '.vue', '.json',
        # Java相关
        '.java', '.kt', '.groovy', '.scala',
        # C/C++相关
        '.c', '.cpp', '.cc', '.h', '.hpp',
        # 其他常见编程语言
        '.go', '.rb', '.php', '.pl', '.swift', '.rs', '.cs', '.fs', '.sh', '.bat', '.ps1'
    ]
    
    # 忽略的文件和目录模式
    IGNORE_PATTERNS = [
        # 构建目录
        '**/node_modules/**', '**/build/**', '**/dist/**', '**/target/**', '**/.git/**',
        # 缓存和临时文件
        '**/__pycache__/**', '**/.cache/**', '**/tmp/**', '**/.tmp/**',
        # 编译文件
        '**/*.pyc', '**/*.pyo', '**/*.class', '**/*.o', '**/*.obj',
        # 日志文件
        '**/*.log',
        # 大型二进制文件
        '**/*.zip', '**/*.tar', '**/*.gz', '**/*.jar', '**/*.war',
        '**/*.mp3', '**/*.mp4', '**/*.avi', '**/*.mov', '**/*.png', '**/*.jpg', '**/*.jpeg',
        '**/*.gif', '**/*.ico', '**/*.svg', '**/*.pdf'
    ]
    
    @staticmethod
    async def process_file(file_path: str, chunking_config: ChunkingConfig) -> List[str]:
        """
        处理文件并返回切片后的文本块
        
        Args:
            file_path: 文件路径
            chunking_config: 切片配置
            
        Returns:
            List[str]: 切片后的文本块列表
        """
        # 获取文件后缀
        file_ext = Path(file_path).suffix.lower()
        
        # 根据文件类型提取文本
        if file_ext == '.txt':
            text = DocumentProcessor._read_text_file(file_path)
        elif file_ext == '.docx':
            text = DocumentProcessor._read_docx_file(file_path)
        elif file_ext == '.pdf':
            text = DocumentProcessor._read_pdf_file(file_path)
        elif file_ext in ['.md', '.markdown']:
            text = DocumentProcessor._read_markdown_file(file_path)
        elif file_ext in DocumentProcessor.CODE_EXTENSIONS:
            text = DocumentProcessor._read_code_file(file_path)
        else:
            raise ValueError(f"不支持的文件类型: {file_ext}")
        
        # 根据切片策略处理文本
        if chunking_config.strategy == ChunkingStrategy.NO_CHUNKING:
            return [text]
        elif chunking_config.strategy == ChunkingStrategy.PARAGRAPH:
            return DocumentProcessor._chunk_by_paragraph(text, chunking_config)
        elif chunking_config.strategy == ChunkingStrategy.SENTENCE:
            return DocumentProcessor._chunk_by_sentence(text, chunking_config)
        elif chunking_config.strategy == ChunkingStrategy.FIXED_SIZE:
            return DocumentProcessor._chunk_by_fixed_size(
                text, 
                chunking_config.chunk_size, 
                chunking_config.chunk_overlap
            )
        else:
            raise ValueError(f"不支持的切片策略: {chunking_config.strategy}")
    
    @staticmethod
    def _read_text_file(file_path: str) -> str:
        """读取文本文件，支持自动检测编码"""
        with open(file_path, 'rb') as f:
            raw_data = f.read()
            # 检测编码
            result = chardet.detect(raw_data)
            encoding = result['encoding']
            
            # 尝试解码
            try:
                return raw_data.decode(encoding)
            except UnicodeDecodeError:
                # 如果检测到的编码不正确，尝试使用 utf-8
                try:
                    return raw_data.decode('utf-8')
                except UnicodeDecodeError:
                    # 最后尝试使用 gbk
                    return raw_data.decode('gbk', errors='replace')
    
    @staticmethod
    def _read_docx_file(file_path: str) -> str:
        """读取docx文件"""
        doc = docx.Document(file_path)
        full_text = []
        for para in doc.paragraphs:
            if para.text:
                full_text.append(para.text)
        return '\n'.join(full_text)
    
    @staticmethod
    def _read_pdf_file(file_path: str) -> str:
        """读取PDF文件"""
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = []
            for page_num in range(len(reader.pages)):
                page = reader.pages[page_num]
                text.append(page.extract_text())
            return '\n'.join(text)
    
    @staticmethod
    def _read_markdown_file(file_path: str) -> str:
        """读取Markdown文件，保留原始格式"""
        # Markdown直接作为文本文件读取，保留其格式，便于后续处理
        return DocumentProcessor._read_text_file(file_path)
    
    @staticmethod
    def _read_code_file(file_path: str) -> str:
        """读取代码文件，添加文件路径作为前缀"""
        content = DocumentProcessor._read_text_file(file_path)
        return f"File: {file_path}\n\n```{os.path.splitext(file_path)[1][1:]}\n{content}\n```"
    
    @staticmethod
    def _should_ignore_file(file_path: str) -> bool:
        """检查是否应该忽略文件"""
        for pattern in DocumentProcessor.IGNORE_PATTERNS:
            if fnmatch.fnmatch(file_path, pattern):
                return True
        return False
    
    @staticmethod
    async def process_directory(dir_path: str, chunking_config: ChunkingConfig, recursive: bool = True) -> List[Dict[str, Any]]:
        """
        递归处理目录下的所有文件
        
        Args:
            dir_path: 目录路径
            chunking_config: 切片配置
            recursive: 是否递归处理子目录
            
        Returns:
            List[Dict]: 处理结果列表，每个元素包含文件名、路径和文本块
        """
        results = []
        
        for root, dirs, files in os.walk(dir_path):
            # 处理当前目录下的文件
            for file in files:
                file_path = os.path.join(root, file)
                
                # 检查是否应该忽略
                if DocumentProcessor._should_ignore_file(file_path):
                    continue
                
                # 检查文件扩展名是否支持
                ext = os.path.splitext(file)[1].lower()
                if ext not in ['.txt', '.docx', '.pdf', '.md', '.markdown'] and ext not in DocumentProcessor.CODE_EXTENSIONS:
                    continue
                
                try:
                    # 处理文件
                    chunks = await DocumentProcessor.process_file(file_path, chunking_config)
                    relative_path = os.path.relpath(file_path, dir_path)
                    
                    results.append({
                        'filename': file,
                        'path': relative_path,
                        'chunks': chunks,
                        'chunk_count': len(chunks),
                        'total_characters': sum(len(chunk) for chunk in chunks)
                    })
                except Exception as e:
                    print(f"处理文件 {file_path} 失败: {str(e)}")
            
            # 如果不递归，直接返回
            if not recursive:
                break
        
        return results
    
    @staticmethod
    def _chunk_by_paragraph(text: str, config: ChunkingConfig) -> List[str]:
        """按段落切分文本"""
        # 使用自定义分隔符或默认段落分隔
        separator = config.separator or r'\n\s*\n'
        paragraphs = re.split(separator, text)
        
        # 过滤空段落
        chunks = [p.strip() for p in paragraphs if p.strip()]
        
        # 如果段落过长，可以进一步切分
        if config.chunk_size:
            result = []
            for chunk in chunks:
                if len(chunk) > config.chunk_size:
                    result.extend(DocumentProcessor._chunk_by_fixed_size(
                        chunk, config.chunk_size, config.chunk_overlap
                    ))
                else:
                    result.append(chunk)
            return result
        
        return chunks
    
    @staticmethod
    def _chunk_by_sentence(text: str, config: ChunkingConfig) -> List[str]:
        """按句子切分文本"""
        # 中文和英文的句子结束符
        sentence_endings = r'(?<=[.。!！?？])\s+'
        sentences = re.split(sentence_endings, text)
        
        # 过滤空句子
        sentences = [s.strip() for s in sentences if s.strip()]
        
        # 将句子组合成块，不超过最大块大小
        chunks = []
        current_chunk = []
        current_size = 0
        
        for sentence in sentences:
            # 如果当前句子加上当前块超过了最大块大小，并且当前块不为空
            if current_size + len(sentence) > config.chunk_size and current_chunk:
                chunks.append(' '.join(current_chunk))
                # 添加重叠部分
                if config.chunk_overlap > 0 and current_chunk:
                    # 找到重叠的句子
                    overlap_size = 0
                    overlap_sentences = []
                    for s in reversed(current_chunk):
                        if overlap_size + len(s) <= config.chunk_overlap:
                            overlap_sentences.insert(0, s)
                            overlap_size += len(s)
                        else:
                            break
                    current_chunk = overlap_sentences
                    current_size = overlap_size
                else:
                    current_chunk = []
                    current_size = 0
            
            current_chunk.append(sentence)
            current_size += len(sentence)
        
        # 添加最后一个块
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks
    
    @staticmethod
    def _chunk_by_fixed_size(text: str, chunk_size: int, chunk_overlap: int) -> List[str]:
        """按固定大小切分文本"""
        chunks = []
        start = 0
        text_len = len(text)
        
        while start < text_len:
            # 计算当前块的结束位置
            end = min(start + chunk_size, text_len)
            
            # 获取当前块
            chunk = text[start:end]
            
            # 如果不是最后一个块，并且不是在一个完整的词的边界
            if end < text_len and end < text_len - 1 and not text[end].isspace():
                # 向后查找空格或标点符号作为分割点
                next_space = text.find(' ', end)
                next_newline = text.find('\n', end)
                next_punct = max([text.find(p, end) for p in ['.', '。', '!', '！', '?', '？', ',', '，', ';', '；']])
                
                # 找到最近的分割点
                splits = [s for s in [next_space, next_newline, next_punct] if s != -1]
                if splits:
                    end = min(splits)
                    chunk = text[start:end]
            
            chunks.append(chunk.strip())
            
            # 计算下一个块的起始位置，考虑重叠
            start = end - chunk_overlap if end - chunk_overlap > start else end
        
        return chunks
    
    @staticmethod
    def chunks_to_documents(chunks: List[str], metadata: Optional[Dict[str, Any]] = None, file_path: Optional[str] = None) -> List[DocumentCreate]:
        """
        将文本块转换为文档对象
        
        Args:
            chunks: 文本块列表
            metadata: 要添加到所有文档的元数据
            file_path: 文件路径，将作为元数据添加
            
        Returns:
            List[DocumentCreate]: 文档对象列表
        """
        base_metadata = metadata or {}
        
        # 如果提供了文件路径，添加到元数据
        if file_path:
            base_metadata["file_path"] = file_path
            base_metadata["file_name"] = os.path.basename(file_path)
            base_metadata["file_extension"] = os.path.splitext(file_path)[1]
        
        return [
            DocumentCreate(
                content=chunk,
                metadata={
                    **base_metadata,
                    "chunk_index": i,
                    "total_chunks": len(chunks)
                }
            )
            for i, chunk in enumerate(chunks)
        ] 