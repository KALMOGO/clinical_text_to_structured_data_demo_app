import os
import sys


# Ensure the project's `src` directory is on sys.path so imports resolve
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SRC  = os.path.join(ROOT, 'src')
sys.path.insert(0, SRC)


from data_anonymization import MedicalTextAnonymizer


# Real French medical text example
FRENCH_MEDICAL_TEXT = """Madame Sophie Dubois, née le 15 mars 1978 (46 ans), habitant au 25 rue Victor Hugo à Lyon (69002), 
a été admise le 10 janvier 2024 pour un déséquilibre glycémique sévère. 
La patiente est suivie pour un diabète de type 2 depuis 2015, sous traitement par Metformine 1000 mg 2x/j. 
Son médecin traitant, le Docteur Martin Leroy, peut être joint au 04 72 34 56 78. 
Contact d'urgence : son époux Pierre Dubois (tél : 06 12 34 56 89). 
Numéro de sécurité sociale : 1 78 03 45 123 456. 
Antécédents familiaux : père (Jacques Moreau) décédé d'infarctus à 65 ans, mère (Marie Moreau) diabétique. 
La patiente rapporte une hyperglycémie persistante depuis une semaine avec polyurie, polydipsie et asthénie. 
Examens biologiques : HbA1c à 9.2%, glycémie à jeun 2.80 g/L. 
Adressée par le Dr. Leroy pour réajustement thérapeutique. 
Coordonnées complètes : sophie.dubois@email.com, 25 rue Victor Hugo 69002 Lyon."""


def test_anonymizer_with_french_medical_text():
    """Test anonymizer with real French medical text containing PII"""
    anonymizer = MedicalTextAnonymizer(
        chunk_size=500,
        chunk_overlap=100,
        confidence_threshold=0.5
    )

    result = anonymizer.anonymize_text(FRENCH_MEDICAL_TEXT)

    # Verify results structure
    assert 'original_text' in result
    assert 'anonymized_text' in result
    assert 'entities' in result
    assert 'statistics' in result

    # Verify anonymization occurred (text changed)
    assert result['anonymized_text'] != result['original_text']

    # Verify entities were detected and anonymized
    assert result['statistics']['total_entities'] > 0
    assert len(result['entities']) > 0

    # Verify anonymized text contains placeholders
    anonymized = result['anonymized_text']
    entity_types = result['statistics']['entity_counts']
    
    # Check for common anonymization patterns
    if entity_types:
        for entity_type in entity_types.keys():
            placeholder = f"[{entity_type}]"
            # At least one entity type should have its placeholder in the text
            if placeholder in anonymized:
                assert entity_types[entity_type] > 0

    # Print results for inspection
    print("\n=== ANONYMIZATION TEST RESULTS ===")
    anonymizer.display_results(result, show_dectected_entities=True, stat=True)
