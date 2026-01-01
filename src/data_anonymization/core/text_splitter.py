import re
import logging
from typing import List
from langchain_text_splitters import TextSplitter
from .entities import ChunkWithPosition

logger = logging.getLogger(__name__)



class PositionAwareTextSplitter(TextSplitter):
    """Text splitter that tracks positions in original text"""
    
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 100):
        super().__init__(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        logger.info(f"Initialized splitter: chunk_size={chunk_size}, overlap={chunk_overlap}")
    
    def split_text_with_positions(self, text: str) -> List[ChunkWithPosition]:
        """Split text into chunks while tracking original positions"""
        chunks_with_pos = []
        text_length = len(text)
        current_pos = 0
        chunk_index = 0
        
        while current_pos < text_length:
            # Calculate end position
            end_pos = min(current_pos + self._chunk_size, text_length)
            
            # Try to break at sentence boundary if not at end
            if end_pos < text_length:
                # Look for sentence endings in the last part of the chunk
                search_start = max(current_pos, end_pos - 100)
                remaining_text = text[search_start:end_pos + 100]
                
                # Find last sentence break
                sentence_breaks = [m.end() for m in re.finditer(r'[.!?]\s+', remaining_text)]
                if sentence_breaks:
                    # Adjust end_pos to the last sentence break
                    last_break = sentence_breaks[-1]
                    end_pos = search_start + last_break
            
            # Extract chunk text
            chunk_text = text[current_pos:end_pos]
            
            chunks_with_pos.append(ChunkWithPosition(
                text=chunk_text,
                start_offset=current_pos,
                end_offset=end_pos,
                chunk_index=chunk_index
            ))
            
            # Move to next chunk with overlap
            current_pos = end_pos - self._chunk_overlap
            if current_pos <= chunks_with_pos[-1].start_offset:
                current_pos = end_pos  # Avoid infinite loop
            
            chunk_index += 1
        
        logger.info(f"Split text into {len(chunks_with_pos)} chunks")
        return chunks_with_pos
    
    def split_text(self, text: str) -> List[str]:
        """Override to maintain compatibility"""
        chunks = self.split_text_with_positions(text)
        return [chunk.text for chunk in chunks]
