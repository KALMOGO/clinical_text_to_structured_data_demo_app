import logging
from typing import List
from ..core.entities import Entity

logger = logging.getLogger(__name__)


class EntityMerger:
    """Merges entities from multiple sources and handles overlaps"""
    
    @staticmethod
    def merge_entities(entities: List[Entity], confidence_threshold: float = 0.5) -> List[Entity]:
        """
        Merge entities from different chunks and models
        - Remove duplicates from overlapping chunks
        - Resolve conflicts (prefer longer spans, higher confidence)
        - Filter by confidence threshold
        """
        # Filter by confidence
        filtered = [e for e in entities if e.score >= confidence_threshold]
        
        if not filtered:
            return []
        
        # Sort by start position, then by length (descending)
        sorted_entities = sorted(filtered, key=lambda e: (e.start_pos, -(e.end_pos - e.start_pos)))
        
        merged = []
        skip_indices = set()
        
        for i, entity in enumerate(sorted_entities):
            if i in skip_indices:
                continue
            
            # Check for overlaps with remaining entities
            conflicting = []
            for j in range(i + 1, len(sorted_entities)):
                if j in skip_indices:
                    continue
                
                other = sorted_entities[j]
                
                # If entities overlap
                if entity.overlaps_with(other):
                    conflicting.append((j, other))
            
            # Resolve conflicts
            if conflicting:
                # Keep the longest span, or highest confidence if same length
                best_entity = entity
                best_idx = i
                
                for idx, other in conflicting:
                    entity_len = entity.end_pos - entity.start_pos
                    other_len = other.end_pos - other.start_pos
                    
                    if other_len > entity_len or (other_len == entity_len and other.score > best_entity.score):
                        best_entity = other
                        best_idx = idx
                
                # Mark others for skipping
                skip_indices.add(i)
                for idx, _ in conflicting:
                    skip_indices.add(idx)
                skip_indices.discard(best_idx)
                
                if best_idx == i:
                    merged.append(entity)
            else:
                merged.append(entity)
        
        # Final sort by position
        merged.sort(key=lambda e: e.start_pos)
        
        logger.info(f"Merged {len(entities)} entities into {len(merged)} unique entities")
        return merged
