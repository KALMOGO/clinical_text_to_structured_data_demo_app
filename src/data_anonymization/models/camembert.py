from .base import PIIModel
from ..core.entities import Entity, ChunkWithPosition
from typing import List

class CamembertNERWithDatesModel(PIIModel):
    """Camembert NER model with date detection for French text"""
    
    def __init__(self):
        super().__init__("Jean-Baptiste/camembert-ner-with-dates")
        self.entity_mapping = {
            'PER': 'NAME',
            'LOC': 'LOCATION',
            'ORG': 'ORGANIZATION',
            'MISC': 'MISC',
            'DATE': 'DATE'
        }
        self.placeholder_tokens = ["ADDRESS", "LOCATION", "PHONE", "EMAIL", "DATE", "ID", "MISC", "NAME"]
    
    def detect_entities_in_chunk(self, chunk: ChunkWithPosition) -> List[Entity]:
        entities = super().detect_entities_in_chunk(chunk)
        
        cleaned_entities = []
        for entity in entities:
            word = entity.text.upper()
            
            if any(tok in word for tok in self.placeholder_tokens):
                continue
            
            entity.entity_type = self.entity_mapping.get(entity.entity_type, 'OTHER')
            cleaned_entities.append(entity)
        
        return cleaned_entities