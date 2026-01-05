# main.py
import os
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

load_dotenv()  # loads .env automatically

# ---------------------------------------------------------
# Load API key
# ---------------------------------------------------------
os.environ["OPENAI_API_KEY"] = os.getenv("DEEPSEEK_API_KEY") # type: ignore


# ---------------------------------------------------------
# Load prompt template from external file
# ---------------------------------------------------------
def load_prompt_template(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

# Define prompt template
template_text = load_prompt_template("src/extraction/prompt.txt")

prompt = PromptTemplate(
    input_variables=["text"],
    template=template_text
)

# Output parser
parser = StrOutputParser()


# ---------------------------------------------------------
# Configure DeepSeek model
# ---------------------------------------------------------
def get_llm(stream=False):
    return ChatOpenAI(
        model="deepseek-chat",
        base_url="https://api.deepseek.com/v1",
        temperature=0.7,
        streaming=stream,
    )


# ---------------------------------------------------------
# Retry logic for robustness
# ---------------------------------------------------------
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=4))
def run_sync(prompt_input):
    llm = get_llm(stream=False)
    chain = prompt | llm | parser
    return chain.invoke(prompt_input)


# ---------------------------------------------------------
# Streaming version
# ---------------------------------------------------------
async def run_stream(prompt_input):
    llm = get_llm(stream=True)
    chain = prompt | llm | parser

    print("\n=== STREAMING RESPONSE ===\n")

    async for chunk in chain.astream(prompt_input):
        print(chunk, end="", flush=True)

    print("\n")


# ---------------------------------------------------------
# Async version (non-streaming)
# ---------------------------------------------------------
async def run_async(prompt_input):
    llm = get_llm(stream=False)
    chain = prompt | llm | parser
    return await chain.ainvoke(prompt_input)


# ---------------------------------------------------------
# Example usage
# ---------------------------------------------------------
# if __name__ == "__main__":

#     user_text = """
#     Patient agé de 78ans adressé par salle de réveil après ACR hypoxique récupéré ATCD: - Rhumatisme chondrocalcinoique sous CTC au long cours
#      - IRC post lithiasique à répétition (sonde JJ multiples) avec DFG de base à 45-50 à diurèse conservée - 
#     LMNC stable avec anémie chronique sous EPO - Hyperthyroidie mal controlée - Diabète de type 2 
#     non insulinoréquérant non compliqué - Colectomie totale en 2006 - Cure d’éventration en 2008 - 
#     Péritonite en 2012 suite à lithotrithie TTT usuels: CORTANCYL 5mg 2-0-0 INEXIUM 40 0-0-1 PROPYLTHOURACYLE 50 1-1-0 
#     ADENURIC 80 1-0-0 KALEORID 1000 1-1-1 ARANESP le lundi IMODIUM à la demande GLUCOPHAGE ALD Pas d’allergie 
#     connue HDM: Patient hospitalisé en chir dig depuis 7 mois en raison d’une fistulisation à la peau du grêle. 
#     Au niveau chirurgicale: - Evolution lentement favorable de la fistule sous VAC + cicatrisation dirigée avec 
#     à ce jour une fistule en tête d’épingle du grêle d’où un maintien à jeun strict Au niveau médicale: 1) Evolution emaillée par plusieurs
#     épisodes septiques à point de départ pulmonaire, digestif, une candidose invasive, une infection à C.difficile
#     2) Un passage en ACFA bien tolérée ttt par BB- + décoagulation 3) Plusieurs épisodes septiques ttt par atb à large spectre à point de départ pulmonaire, digestif, urinaire. Une candidémie invasive ainsi
#     u’une infection à C.difficile Depuis 2 jours, apparition d’un syndrome infectieux avec fièvre 
#     à 39°C associé à un syndrome infla bio (GB = 15000, CRP en augmentation à 93). Après bodyTDM, 
#     2 points d’appel sont suspectés: - une pneumopahtie du LIDt - Un Picc line avec hémoc positive à CG+ - l’abdomen 
#     et le tractus urinaire sont dédouanés --> Introduction ATB (TIENAM/ZYVOXID/OFLOCET) et
#     ablation du Picc line le 1-08 Ce matin, détresse respi avec polypnée et Pa02 = 60 sous O2 6L/min motivant l’appel de l’anesthésiste.
#     A l’arrivée du MAR vers 9h15, patient en ACR à priori d’origine hypoxique: - Durée no flow = ?, à priori < 10 min - Durée low flow = 15min 
#     - Récupération rythme choquable (FV) après 12 min et 10mg d’adré - 1CEE permetttant récupération rythme sinusal efficace avec PAM > 65 Dans
#     les suites instabilité HD s’installant nécessitant introduction d’Adré IVSE jusqu’à 2.5mg/h. Patient transféré en salle de réveil
#     en attendant une place de réanimation. A l’arrivée en réa, le patient présente:
#     1) un ACR récupéré avec signe de vie: myosis serré, VS après récupération ACR mais avec BIS = 3 sous Dip V15.
#     D’étiologie probablement hypoxique avec un nouvel angioTDM objectivant une pneumopathie du LIDt.
#     TDM cérébrale sans particularité. Pas de signe d’EP Pas de signe d’infarctus myocardique 
#     2) Un SIRS post ischémie reperfusion compliqué: - défaillance HD avec PAM = 65 sous Adré à 2.5mg/h, ACFA rapide à 120 bpm,
#     lactate = 11.6 - défaillance rénale avec oligurie et acutisation IR (créat = 330, urée = 37) - défaillance HD à minima avec cytolyse à 2N, bili = 28, TP = 42% 
#     - coagulopathie: TP =42%, TCA = 58, Plq = 18000 Pas de défaillance cardiaque avec à l’ETT: 
#     - Bon VG, FE = 70% sous Adré, ITV sous ao = 13 - Pressions remplissages basses: E< A E/E’ = 7 
#     - Bon VD, pas d’HTAP Pas de défaillance respi avec P/F > 250, compliance normale --> remplissage par 1500mL cristalloides + introduction NAD permettant sevrage Adré sous 4 mg/h CORDARONE en bolus permettant RSR 
#     3) Un syndrome infectieux en rapport avec un pneumopathie chez ce grand dénutri En somme patient de 78ans dénutri,
#     corticothérapé au long cours avec hémopathie chronique,
#     ayant présenté un ACR hypoxique sur pneumopathie compliqué défaillance HD/ rénale/hépatique/ coagulopathie CAT:
#     1) 24h d’hypothermie 2) Epreuve de réveil dans 24h 3) en attendant pas de réa d’un nouvel ACR, pas de dialyse
#     """

#     payload = {"text": user_text}

#     # 1. Sync with retries
#     # print("\n=== SYNC RESULT ===\n")
#     # result = run_sync(payload)
#     # print(result)

#     # 2. Streaming
#     #asyncio.run(run_stream(payload))

#     # 3. Async non-streaming
#     # print("\n=== ASYNC RESULT ===\n")
#     async_result = asyncio.run(run_async(payload))
    
