import re
import unicodedata
import ast
import pandas as pd

# Keywords indicating non-drug concepts
NON_DRUG_KEYWORDS = {
    "TRITHERAPIE", "THERAPIE", "ANTI", "ANTIBIOTIQUE",
    "SOINS", "TRAITEMENT", "ANTIVIRAL", "ANTIVIH"
}

def normalize(text: str) -> str:
    text = unicodedata.normalize("NFD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"\s+", " ", text).strip().upper()
    
def split_and_clean_drug_name(raw) -> list[str]:
    cleaned = []

    # CASE: raw is a list
    if isinstance(raw, list):
        for item in raw:
            cleaned.extend(split_and_clean_drug_name(item))
        return list(dict.fromkeys(cleaned))

    # CASE: raw is a string
    if not isinstance(raw, str) or not raw.strip():
        return []

    raw = normalize(raw)
    # Remove parentheses
    raw = re.sub(r"\([^)]*\)", "", raw)

    # Remove dosage patterns
    raw = re.sub(r"\b\d+(\.\d+)?\s*(MG|ML|UG|UI|IU|G|DOSE|%)\b.*", "", raw)
    raw = re.sub(r"\b\d+\s*/\s*\d+(\.\d+)?\b", "", raw)

    # Remove trailing numbers
    raw = re.sub(r"\b\d+\b$", "", raw).strip()

    # Handle brackets []
    if "[" in raw and "]" in raw:
        content = re.findall(r"\[(.*?)\]", raw)

        raw = " ".join(content)

    # Split on drug separators
    parts = re.split(r"\s*(?:\+|/)\s*", raw)

    for part in parts:
        part = part.strip()
        if not part:
            continue

        words = part.split()

        # Filter non-drug concepts
        if any(w in NON_DRUG_KEYWORDS for w in words):
            continue

        # Remove hyphens inside drug names
        part = part.replace("-", "")

        drug = part.split()[0]

        if len(drug) >= 3 and not drug.isdigit():
            cleaned.append(drug)

    return list(dict.fromkeys(cleaned))


def clean_drug_df(df):
    #Trait special value in the treament df

    # Detect rows where name_simp contains a list-like string
    df_no_bracket = df[df["name_simp"].str.contains("['", regex=False)].copy()

    # Convert string → Python list
    df_no_bracket["name_simp"] = df_no_bracket["name_simp"].apply(ast.literal_eval)
    df_exploded_ = df_no_bracket.explode("name_simp")

    # Explode the list
    df_exploded_["name_simp"] = df_exploded_["name_simp"].str.strip()


    df_clean = df[~df["name_simp"].str.contains("['", regex=False)]

    # Merge exploded rows back
    df_clean = pd.concat([df_clean, df_exploded_], ignore_index=True)

    #  Apply drug cleaning function
    df_clean["drug_cleaned"] = df_clean["name_simp"].apply(split_and_clean_drug_name)

    # Explode cleaned drugs 
    df_exploded_clean = ( 
        df_clean .explode("drug_cleaned") 
        .dropna(subset=["drug_cleaned"]) 
        .drop(columns=["name_simp"]) 
        .rename(columns={"drug_cleaned": "name_simp"}) )

    return df_exploded_clean