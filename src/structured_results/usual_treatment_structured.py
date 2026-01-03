import json
import chardet
import pandas as pd
from typing import Generator, Dict, Any
from .utils import clean_drug_df


def is_valide_json_structure(data: Any):
    """
    Validate that JSON structure matches expected format.
    """
    # Check if data is a dict
    if not isinstance(data, dict):
        return False
    
    if not data:
        return False
    
    # Validate each patient entry
    # pass TODO: implement detailed validation if needed
    return True

# To normalize names handling accents and case
import unicodedata
def normalize_name(name):
    return (unicodedata.normalize('NFD', str(name or ''))
            .encode('ascii', 'ignore')
            .decode('ascii')
            .upper()
            .strip())

def stream_json_data(file_path: str) -> Generator[Dict[str, Any], None, None]:
    """
        Stream JSON data to avoid loading entire file into memory
        file_path: Path to the JSON file
        Yields dictionaries with 'ID' and 'medication' keys

        the JSON structure is expected to be:
        {
            "patient_id_1": {
                "medication": [
                    {"drug_name": "Medication A"},
                    {"drug_name": "Medication B"}
                ]
            },
            "patient_id_2": {      
                "medication": [
                    {"drug_name": "Medication C"}
                ]
            }
        }
    """

    # Open the JSON file and stream data
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Validate input json structure
    if not is_valide_json_structure(data):
        raise ValueError("""
                        Invalid file data structure
                        Expected format:
                            {
                                "patient_id_1": {
                                    "medication": [
                                        {"drug_name": "Medication A"},
                                        {"drug_name": "Medication B"}
                                    ]
                                },
                                "patient_id_2": {      
                                    "medication": [
                                        {"drug_name": "Medication C"}
                                    ]
                                }
                            }
                        """)

    for patient_id, patient_data in data.items():

        # Some patient medication data might be a string instead of a dict: PROBLEMATIC
        # if  isinstance(patient_data, str):
        #     print(patient_data) # Check the problematic entries
        #     yield {
        #             'ID': patient_id,
        #             'medication': patient_data
        #         }
        
        if  isinstance(patient_data, dict) and "medication" in patient_data:
            # medication should be a list
            medication = patient_data["medication"]
            if not isinstance(medication, list):
                continue  # Skip if medication is not a list

            for med in medication:
                if isinstance(med, dict):
                    # Some patient medication data might be missing 'drug_name' key: PROBLEMATIC
                    if 'drug_name' in med:
                        name_simp  =  normalize_name(med['drug_name'])
                    else:
                        #print(med) # Check  to see which ones are missing 'drug_name'
                        #name_simp = None
                        continue  # Skip entries without 'drug_name'

                # Handle case where medication is directly a string not a dict with 'drug_name' key
                elif isinstance(med, str):
                    name_simp = normalize_name(med)
                else:
                    # Some entries might be neither dict nor str: PROBLEMATIC
                    #print(med) # Check to see which ones are problematic
                    #name_simp = None
                    continue  # Skip problematic entries

                yield {
                    'id': patient_id,
                    'name_simp': name_simp
                }
            

def json_to_mesh_mapped_dataframe(
    json_path: str,
    mesh_data_path: str,
    output_path: str = "output"
) -> pd.DataFrame:
    """
    Convert JSON to DataFrame, save to CSV, map medications to MeSH/ATC codes,
    and save the mapped DataFrame.
    """

    # ---------- Helper: detect encoding ----------
    def detect_encoding(file_path):
        with open(file_path, "rb") as f:
            raw_data = f.read(100000)
        return chardet.detect(raw_data)["encoding"]

    # ---------- Step 1: JSON → DataFrame ----------
    df = pd.DataFrame(list(stream_json_data(json_path)))
    
    # clean the drug names
    df = clean_drug_df(df)

    usual_treatment_csv = f"{output_path}\\usual_treatment.csv"
    # df.to_csv(usual_treatment_csv, index=False)

    # ---------- Step 2: Load MeSH dictionary ----------
    mesh_encoding = detect_encoding(mesh_data_path)
    mesh_df = pd.read_csv(mesh_data_path, encoding=mesh_encoding)

    # ---------- Step 3: Merge on normalized medication name ----------
    merged_df = pd.merge(
        df,
        mesh_df[["name_simp", "ATC4"]],
        on="name_simp",
        how="left"
    )

    # ---------- Step 4: Save mapped result ----------
    mapped_csv = f"{output_path}\\patient_medication_mesh_mapping.csv"
    # merged_df.to_csv(mapped_csv, index=False)

    return merged_df
