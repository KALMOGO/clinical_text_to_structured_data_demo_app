import logging
from typing import List, Dict, Any
from collections import defaultdict
from langchain_core.runnables import RunnableParallel, RunnableLambda

from .core.entities import ChunkWithPosition, Entity
from .core.text_splitter import PositionAwareTextSplitter
from .models.piranha import PiranhaPIIModel
from .models.camembert import CamembertNERWithDatesModel
from .processors.entity_merger import EntityMerger
from .processors.text_anonymizer import TextAnonymizer

logger = logging.getLogger(__name__)


class MedicalTextAnonymizer:
    """Main anonymization system"""

    def __init__(self,
                 chunk_size: int = 500,
                 chunk_overlap: int = 100,
                 confidence_threshold: float = 0.5):

        logger.info("Initializing Medical Text Anonymizer...")

        self.text_splitter = PositionAwareTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )

        self.piranha_model = PiranhaPIIModel()
        self.camembert_model = CamembertNERWithDatesModel()
        self.entity_merger = EntityMerger()
        self.anonymizer = TextAnonymizer()
        self.confidence_threshold = confidence_threshold

        logger.info("Medical Text Anonymizer initialized successfully")

    def _process_chunk_with_both_models(self, chunk: ChunkWithPosition) -> List[Entity]:
        """Process a single chunk with both models in parallel"""
        entities_piranha = self.piranha_model.detect_entities_in_chunk(chunk)
        entities_camembert = self.camembert_model.detect_entities_in_chunk(
            chunk)

        all_entities = entities_piranha + entities_camembert
        logger.info(
            f"Chunk {chunk.chunk_index}: Found {len(entities_piranha)} (Piranha) + {len(entities_camembert)} (CamemBERT) = {len(all_entities)} entities")

        return all_entities  # type: ignore

    def anonymize_text(self, text: str) -> Dict[str, Any]:
        """
        Main anonymization pipeline

        Args:
            text: Original medical text

        Returns:
            Dictionary with anonymized text and metadata
        """
        logger.info(f"Starting anonymization of text ({len(text)} chars)")

        # Step 1: Split text into chunks with positions
        chunks = self.text_splitter.split_text_with_positions(text)

        # Step 2: Create parallel processing chain
        chunk_processors = {
            f"chunk_{chunk.chunk_index}": RunnableLambda(
                lambda _input, chunk=chunk: self._process_chunk_with_both_models(
                    chunk)  # type: ignore
            )
            for chunk in chunks
        }

        parallel_chain = RunnableParallel(**chunk_processors)  # type: ignore

        # Step 3: Execute parallel processing
        logger.info(f"Processing {len(chunks)} chunks in parallel...")
        results = parallel_chain.invoke({})

        # Step 4: Flatten all entities
        all_entities = []
        for chunk_result in results.values():
            all_entities.extend(chunk_result)

        logger.info(f"Total entities detected: {len(all_entities)}")

        # Step 5: Merge overlapping entities
        merged_entities = self.entity_merger.merge_entities(
            all_entities,
            confidence_threshold=self.confidence_threshold
        )

        # Step 6: Anonymize text
        anonymized_text = self.anonymizer.anonymize(text, merged_entities)

        # Step 7: Prepare metadata
        entity_stats = defaultdict(int)
        for entity in merged_entities:
            entity_stats[entity.entity_type] += 1

        return {
            'original_text': text,
            'anonymized_text': anonymized_text,
            'entities': [
                {
                    'text': e.text,
                    'type': e.entity_type,
                    'start': e.start_pos,
                    'end': e.end_pos,
                    'score': e.score,
                    'model': e.model_source
                }
                for e in merged_entities
            ],
            'statistics': {
                'total_entities': len(merged_entities),
                'entity_counts': dict(entity_stats),
                'chunks_processed': len(chunks)
            }
        }


    def display_results(
        self,
        results: Dict[str, Any],
        show_dectected_entities: bool = False,
        stat: bool = False
    ) -> str:
        """Return anonymization results as a formatted string"""

        lines = []

        sep = "=" * 80

        lines.append("\n" + sep)
        lines.append("ORIGINAL TEXT:")
        lines.append(sep)
        lines.append(results["original_text"])

        lines.append("\n" + sep)
        lines.append("ANONYMIZED TEXT:")
        lines.append(sep)
        lines.append(results["anonymized_text"])

        if stat:
            lines.append("\n" + sep)
            lines.append("STATISTICS:")
            lines.append(sep)
            lines.append(
                f"Total entities found: {results['statistics']['total_entities']}"
            )
            lines.append(
                f"Chunks processed: {results['statistics']['chunks_processed']}"
            )
            lines.append("\nEntity counts by type:")
            for entity_type, count in results["statistics"]["entity_counts"].items():
                lines.append(f"  {entity_type}: {count}")

        if show_dectected_entities:
            lines.append("\n" + sep)
            lines.append("DETECTED ENTITIES:")
            lines.append(sep)
            for entity in results["entities"]:
                lines.append(
                    f"{entity['type']:12} | "
                    f"{entity['text']:30} | "
                    f"Score: {entity['score']:.3f} | "
                    f"Model: {entity['model']}"
                )

        return "\n".join(lines)

