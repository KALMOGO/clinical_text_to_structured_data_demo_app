from dataclasses import dataclass


@dataclass
class Entity:
    """Entity with global position tracking"""
    text: str
    entity_type: str
    score: float
    start_pos: int
    end_pos: int
    chunk_index: int = -1
    model_source: str = ""
    
    def overlaps_with(self, other: 'Entity') -> bool:
        return not (self.end_pos <= other.start_pos or self.start_pos >= other.end_pos)
    
    def contains(self, other: 'Entity') -> bool:
        return self.start_pos <= other.start_pos and self.end_pos >= other.end_pos
    
    def __repr__(self):
        return f"Entity('{self.text}', {self.entity_type}, pos={self.start_pos}-{self.end_pos})"


@dataclass
class ChunkWithPosition:
    """Chunk with its position in the original text"""
    text: str
    start_offset: int
    end_offset: int
    chunk_index: int