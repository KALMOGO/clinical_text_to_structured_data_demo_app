"""
Extract structured lifestyle information from clinical text
using DeepSeek via LangChain
"""

import os
import json
import re
import time
from typing import Dict, Optional

import pandas as pd
from dotenv import load_dotenv
from tqdm import tqdm

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser


class LifestyleExtractor:
    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "deepseek-chat",
        temperature: float = 0.1,
        max_tokens: int = 500,
        sleep_time: float = 0.1,
    ):
        """
        Initialize lifestyle extractor using DeepSeek + LangChain
        """
        load_dotenv()

        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        if not self.api_key:
            raise ValueError("DEEPSEEK_API_KEY not found")

        self.sleep_time = sleep_time

        self.llm = ChatOpenAI(
            api_key=self.api_key,
            base_url="https://api.deepseek.com/v1",
            model=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        self.prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                "Tu es un assistant médical qui extrait des informations structurées. "
                "Tu réponds toujours avec un JSON valide uniquement."
            ),
            (
                "human",
                """Voici un texte décrivant le mode de vie d'un patient :

{lifestyle_text}

Extrait les informations suivantes et réponds UNIQUEMENT avec un objet JSON valide :

{{
  "tabac_actif": "oui" | "non" | "inconnu",
  "tabac_quantite": "paquets/année" | "inconnu",
  "alcool_actif": "oui" | "non" | "inconnu",
  "alcool_quantite": "grammes/jour" | "inconnu",
  "autres_drogues": "oui" | "non" | "inconnu",
  "autonomie": "autonome" | "limité" | "grabataire" | "inconnu",
  "sport": "oui" | "non" | "inconnu",
  "vit_seul": "oui" | "non" | "inconnu",
  "aide_domicile": "oui" | "non" | "inconnu",
  "institutionnalise": "oui" | "non" | "inconnu"
}}

Règles importantes :
- 10PA = 10 paquets/année
- 3/4 cg/j = convertir en PA (1 paquet = 20 cigarettes)
- OH = alcool
- 1 verre = 10g alcool, bouteille vin = 80g, alcool fort = 220g
- "grabataire" = alité
- "autonome à domicile" = autonome
- "peu autonome" = limité
- Si non mentionné → "inconnu"
"""
            ),
        ])

        self.chain = self.prompt | self.llm | StrOutputParser()

    @staticmethod
    def _extract_json(text: str) -> Optional[Dict]:
        """Extract JSON object from LLM output"""
        json_pattern = r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}"
        for match in re.finditer(json_pattern, text, re.DOTALL):
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass
        return None

    def extract_from_text(self, lifestyle_text: str) -> Dict:
        """Extract lifestyle info from a single text"""
        try:
            response = self.chain.invoke({"lifestyle_text": lifestyle_text})
            result = self._extract_json(response)

            if result:
                return result

            return {"erreur": "JSON extraction failed", "raw_response": response}

        except Exception as e:
            return {"erreur": str(e)}

    def process_csv(
        self,
        input_csv: str,
        output_csv: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Process CSV and return DataFrame with extracted lifestyle data
        """
        df = pd.read_csv(input_csv, encoding="utf-8")

        df = df.dropna(subset=["lifestyle"])
        df = df[df["lifestyle"].str.strip() != ""]

        results = []

        for _, row in df.iterrows():
            extracted = self.extract_from_text(row["lifestyle"])

            if "erreur" not in extracted:
                result = {
                    "PatientID": row["PatientID"],
                    "tabac_oui_non": extracted.get("tabac_actif", "inconnu"),
                    "tabac_quantite_PA": extracted.get("tabac_quantite", "inconnu"),
                    "alcool_oui_non": extracted.get("alcool_actif", "inconnu"),
                    "alcool_quantite_g_j": extracted.get("alcool_quantite", "inconnu"),
                    "autres_drogues": extracted.get("autres_drogues", "inconnu"),
                    "autonomie": extracted.get("autonomie", "inconnu"),
                    "sport": extracted.get("sport", "inconnu"),
                    "vit_seul": extracted.get("vit_seul", "inconnu"),
                    "aide_domicile": extracted.get("aide_domicile", "inconnu"),
                    "institutionnalise": extracted.get("institutionnalise", "inconnu"),
                }
            else:
                result = {
                    "PatientID": row["PatientID"],
                    "tabac_oui_non": "erreur",
                    "tabac_quantite_PA": "erreur",
                    "alcool_oui_non": "erreur",
                    "alcool_quantite_g_j": "erreur",
                    "autres_drogues": "erreur",
                    "autonomie": "erreur",
                    "sport": "erreur",
                    "vit_seul": "erreur",
                    "aide_domicile": "erreur",
                    "institutionnalise": "erreur",
                }

            results.append(result)
            time.sleep(self.sleep_time)

        results_df = pd.DataFrame(results)

        # if output_csv:
        #     results_df.to_csv(output_csv, index=False, encoding="utf-8-sig")

        return results_df


# extractor = LifestyleExtractor()

# # Single text
# text = "Patient fumeur à 10PA, consommation OH occasionnelle, autonome à domicile"
# print(extractor.extract_from_text(text))

# # CSV processing
# df = extractor.process_csv(
#     input_csv="sample500.csv",
#     output_csv="lifestyle_extracted.csv",
# )
