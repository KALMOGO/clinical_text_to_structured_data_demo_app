"""
Convert comorbidities in free text to ICD-10 codes
using DeepSeek via LangChain
"""

import os
import json
import re
from typing import Dict, Optional

import pandas as pd
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser


class ComorbidityICD10Converter:
    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "deepseek-chat",
        temperature: float = 0.3,
        max_tokens: int = 1000,
    ):
        """
        Initialize the ICD-10 converter

        Args:
            api_key: DeepSeek API key (optional, loaded from env if None)
            model_name: DeepSeek model name
        """
        load_dotenv()

        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        if not self.api_key:
            raise ValueError("DEEPSEEK_API_KEY not found")

        self.llm = ChatOpenAI(
            api_key=self.api_key,
            base_url="https://api.deepseek.com/v1",
            model=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        self.prompt_template = ChatPromptTemplate.from_messages([
            (
                "system",
                "Tu es un expert médical spécialisé en codage CIM-10.",
            ),
            (
                "human",
                """Analyse le texte médical suivant et extrais le ou les codes CIM-10.

Texte médical: {comorbidity}

Réponds UNIQUEMENT avec un objet JSON valide :

{{
    "comorbidite_originale": "texte original",
    "codes_cim10": [
        {{
            "code": "CODE_CIM10",
            "libelle": "Description",
            "confiance": "haute/moyenne/basse"
        }}
    ],
    "notes": "commentaires éventuels"
}}"""
            ),
        ])

        self.chain = self.prompt_template | self.llm | StrOutputParser()

    @staticmethod
    def extract_json_from_response(response: str) -> Optional[Dict]:
        """Extract JSON object from LLM response"""
        json_pattern = r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}"
        for match in re.finditer(json_pattern, response, re.DOTALL):
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass
        return None

    def convert_to_icd10(self, comorbidity: str) -> Dict:
        """Convert a comorbidity string to ICD-10"""
        try:
            response = self.chain.invoke({"comorbidity": comorbidity})
            result = self.extract_json_from_response(response)

            if result:
                return result

            return {
                "comorbidite_originale": comorbidity,
                "codes_cim10": [],
                "notes": response,
                "erreur": "JSON extraction failed",
            }

        except Exception as e:
            return {
                "comorbidite_originale": comorbidity,
                "codes_cim10": [],
                "notes": str(e),
                "erreur": "API error",
            }

    def process_csv(
        self,
        input_file: str,
        output_file: str = "comorbidities_with_icd10.csv",
    ) -> pd.DataFrame:
        """Process CSV file and add ICD-10 codes"""
        df = pd.read_csv(input_file)

        codes, libelles, confiances, notes, responses = [], [], [], [], []

        for _, row in df.iterrows():
            result = self.convert_to_icd10(row["Comorbidite"])

            if result.get("codes_cim10"):
                code = result["codes_cim10"][0]
                codes.append(code.get("code", "N/A"))
                libelles.append(code.get("libelle", "N/A"))
                confiances.append(code.get("confiance", "N/A"))
            else:
                codes.append("N/A")
                libelles.append("N/A")
                confiances.append("N/A")

            notes.append(result.get("notes", ""))
            responses.append(json.dumps(result, ensure_ascii=False))

        df["Code_CIM10"] = codes
        #df["Libelle_CIM10"] = libelles
        #df["Confiance"] = confiances
        #df["Notes"] = notes
        #df["Reponse_Complete"] = responses

        #df.to_csv(output_file, index=False, encoding="utf-8-sig")
        return df



# from icd10_converter import ComorbidityICD10Converter

# converter = ComorbidityICD10Converter()

# # Single text
# result = converter.convert_to_icd10("Diabète de type 2 avec complications")
# print(result)

# # CSV processing
# df = converter.process_csv(
#     input_file="comorbidites.csv",
#     output_file="comorbidites_icd10.csv",
# )