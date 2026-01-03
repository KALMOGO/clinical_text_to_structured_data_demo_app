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
template_text = load_prompt_template("./prompt.txt")

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
if __name__ == "__main__":

    user_text = """
    Madame [NAME], née [DATE]), habitant au [ADDRESS] rue [ADDRESS] à [LOCATION] [ADDRESS] 
    a été admise [DATE] pour un déséquilibre glycémique sévère. 
    La patiente est suivie pour un diabète de type 2 depuis [DATE] sous traitement par [MISC] 1000 mg 2x/j. 
    Son médecin traitant, le [NAME], peut être joint au [PHONE] 
    Contact d'urgence : son époux [NAME] (tél : [PHONE]). 
    Numéro de sécurité sociale : [ID] 
    Antécédents familiaux : père [NAME]) décédé d'infarctus [DATE], mère [NAME]) diabétique. 
    La patiente rapporte une hyperglycémie persistante depuis [DATE] avec polyurie, polydipsie et asthénie. 
    Examens biologiques : HbA1c à 9.2%, glycémie à jeun 2.80 g/L. 
    Adressée par le [NAME] pour réajustement thérapeutique. 
    Coordonnées complètes : [EMAIL], [ADDRESS] [LOCATION] [NAME] [LOCATION].
    """

    payload = {"text": user_text}

    # 1. Sync with retries
    print("\n=== SYNC RESULT ===\n")
    result = run_sync(payload)
    print(result)

    # 2. Streaming
    asyncio.run(run_stream(payload))

    # 3. Async non-streaming
    print("\n=== ASYNC RESULT ===\n")
    async_result = asyncio.run(run_async(payload))
    print(async_result)
