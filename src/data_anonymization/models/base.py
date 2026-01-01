import logging
from typing import List, Tuple
from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline
from ..core.entities import Entity, ChunkWithPosition

logger = logging.getLogger(__name__)


class PIIModel:
    """Base class for PII detection models with character-level position mapping"""
    
    def __init__(self, model_name: str, task: str = "ner"):
        self.model_name = model_name
        self.task = task
        self.pipeline = None
        self.tokenizer = None
        self._load_model()
    
    def _load_model(self):
        """Load the model pipeline"""
        try:
            logger.info(f"Loading model: {self.model_name}")
            
            model = AutoModelForTokenClassification.from_pretrained(self.model_name)

            # IMPORTANT FIX: disable fast tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                use_fast=False
            )
            self.tokenizer.model_max_length = 520

            self.pipeline = pipeline(
                self.task, # type: ignore
                model=model,
                aggregation_strategy="simple",
                tokenizer=self.tokenizer,
                device=-1
            ) # type: ignore

            logger.info(f"Model loaded successfully: {self.model_name}")

        except Exception as e:
            logger.error(f"Failed to load model {self.model_name}: {e}")
            raise

    
    def _get_char_positions(self, text: str, token_start: int, token_end: int) -> Tuple[int, int]:
        """
        Convert token positions to character positions
        This is CRITICAL for correct alignment
        """
        # Tokenize the text
        encoding = self.tokenizer(
            text, return_offsets_mapping=True,
            add_special_tokens=True)  # type: ignore
        
        offset_mapping = encoding['offset_mapping']
        
        # Handle special tokens and find character positions
        char_start = None
        char_end = None
        
        # Find the character start
        if token_start < len(offset_mapping):
            char_start = offset_mapping[token_start][0]
        
        # Find the character end
        if token_end <= len(offset_mapping):
            # token_end is exclusive, so we use token_end - 1 for the last token
            if token_end > 0:
                char_end = offset_mapping[token_end - 1][1]
        
        # Fallback: if we couldn't get proper positions
        if char_start is None:
            char_start = 0
        if char_end is None:
            char_end = len(text)
        
        return char_start, char_end
    
    def detect_entities_in_chunk(self, chunk: ChunkWithPosition) -> List[Entity]:
        """Detect entities in a chunk and return with global positions"""
        if not self.pipeline:
            raise RuntimeError("Model not loaded properly")
        
        try:
            raw_entities = self.pipeline(chunk.text)
            entities = []
            
            for entity_dict in raw_entities:
                # Get the actual text span
                entity_text = entity_dict['word']
                
                # CRITICAL FIX: Find the actual character position in the chunk
                # The entity_dict['start'] and entity_dict['end'] might be token-based
                # We need to find the actual character positions
                
                # Try to find the entity text in the chunk
                # Handle special characters that the tokenizer might have modified
                clean_entity = entity_text.replace('##', '').replace('▁', '').strip()
                
                # Search for the entity in the chunk text
                start_idx = chunk.text.find(clean_entity)
                
                # If not found, try with the original boundaries from the model
                if start_idx == -1:
                    # Use model's provided positions as fallback
                    local_start = entity_dict.get('start', 0)
                    local_end = entity_dict.get('end', len(chunk.text))
                    
                    # Validate these positions
                    if local_start >= len(chunk.text):
                        local_start = 0
                    if local_end > len(chunk.text):
                        local_end = len(chunk.text)
                    
                    # Extract text at these positions to verify
                    extracted_text = chunk.text[local_start:local_end]
                    
                    # If extracted text is reasonable, use it
                    if len(extracted_text) > 0 and len(extracted_text) < 200:
                        start_idx = local_start
                        clean_entity = extracted_text.strip()
                    else:
                        # Skip this entity if we can't locate it properly
                        logger.warning(f"Could not locate entity '{entity_text}' in chunk {chunk.chunk_index}")
                        continue
                
                # Calculate end position
                end_idx = start_idx + len(clean_entity)
                
                # Convert to global positions
                global_start = chunk.start_offset + start_idx
                global_end = chunk.start_offset + end_idx
                
                entity = Entity(
                    text=clean_entity,
                    entity_type=entity_dict.get('entity_group', 'UNKNOWN'),
                    score=entity_dict.get('score', 0.0),
                    start_pos=global_start,
                    end_pos=global_end,
                    chunk_index=chunk.chunk_index,
                    model_source=self.__class__.__name__
                )
                entities.append(entity)
            
            return entities
        except Exception as e:
            logger.error(f"Error detecting entities in chunk {chunk.chunk_index}: {e}")
            import traceback
            traceback.print_exc()
            return []
