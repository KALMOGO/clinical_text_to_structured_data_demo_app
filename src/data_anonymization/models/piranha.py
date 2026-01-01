from typing import List
from .base import PIIModel


class PiranhaPIIModel(PIIModel):
    """Piranha model for PII detection"""

    def __init__(self):
        super().__init__("iiiorg/piiranha-v1-detect-personal-information")
        self.entity_mapping = {
            'GIVENNAME': 'NAME',
            'SURNAME': 'NAME',
            'TELEPHONENUM': 'PHONE',
            'EMAIL': 'EMAIL',
            'DATEOFBIRTH': 'DATE',
            'SOCIALNUM': 'ID',
            'DRIVERLICENSENUM': 'ID',
            'IDCARDNUM': 'ID',
            'STREET': 'ADDRESS',
            'BUILDINGNUM': 'ADDRESS',
            'ZIPCODE': 'ADDRESS',
            'CITY': 'LOCATION',
            'COUNTRY': 'LOCATION'
        }

    def detect_entities_in_chunk(self, chunk) -> List:
        entities = super().detect_entities_in_chunk(chunk)

        for entity in entities:
            original_type = entity.entity_type
            entity.entity_type = self.entity_mapping.get(original_type, original_type)

        return entities
    
# from .base import PIIModel
# from ..core.entities import Entity, ChunkWithPosition
# from typing import List

# class PiranhaPIIModel(PIIModel):
#     """Piranha model for PII detection"""
    
#     def __init__(self):
#         super().__init__("iiiorg/piiranha-v1-detect-personal-information")
#         self.entity_mapping = {
#             'GIVENNAME': 'NAME',
#             'SURNAME': 'NAME',
#             'TELEPHONENUM': 'PHONE',
#             'EMAIL': 'EMAIL',
#             'DATEOFBIRTH': 'DATE',
#             'SOCIALNUM': 'ID',
#             'DRIVERLICENSENUM': 'ID',
#             'IDCARDNUM': 'ID',
#             'STREET': 'ADDRESS',
#             'BUILDINGNUM': 'ADDRESS',
#             'ZIPCODE': 'ADDRESS',
#             'CITY': 'LOCATION',
#             'COUNTRY': 'LOCATION'
#         }
    
#     def detect_entities_in_chunk(self, chunk: ChunkWithPosition) -> List[Entity]:
#         entities = super().detect_entities_in_chunk(chunk)
        
#         for entity in entities:
#             entity.entity_type = self.entity_mapping.get(
#                 entity.entity_type, 
#                 entity.entity_type
#             )
        
#         return entities