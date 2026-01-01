import logging
from typing import List
from ..core.entities import Entity

logger = logging.getLogger(__name__)




class TextAnonymizer:
    """Anonymizes text by replacing entities with placeholders"""
    
    @staticmethod
    def anonymize(original_text: str, entities: List[Entity]) -> str:
        """Replace entities with [LABEL] placeholders while preserving formatting"""
        if not entities:
            return original_text
        
        # Sort entities by position (reverse order for replacement)
        sorted_entities = sorted(entities, key=lambda e: e.start_pos, reverse=True)
        
        anonymized = original_text
        
        for entity in sorted_entities:
            placeholder = f"[{entity.entity_type}]"
            
            # Verify positions are within bounds
            if entity.start_pos < 0 or entity.end_pos > len(anonymized):
                logger.warning(f"Entity position out of bounds: {entity}")
                continue
            
            if entity.start_pos >= entity.end_pos:
                logger.warning(f"Invalid entity positions: {entity}")
                continue
            
            # Replace entity text with placeholder
            before = anonymized[:entity.start_pos]
            after = anonymized[entity.end_pos:]
            anonymized = before + placeholder + after
            
            # Log for debugging
            logger.debug(f"Replaced '{entity.text}' at {entity.start_pos}-{entity.end_pos} with {placeholder}")
        
        logger.info(f"Anonymized {len(entities)} entities")
        return anonymized
