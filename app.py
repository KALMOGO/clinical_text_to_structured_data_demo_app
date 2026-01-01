import streamlit as st
import pandas as pd
import json
from io import StringIO
import PyPDF2
import os
import sys


# Ensure the project's `src` directory is on sys.path so imports resolve
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SRC  = os.path.join(ROOT, 'src')
sys.path.insert(0, SRC)


from src.data_anonymization import MedicalTextAnonymizer

st.markdown(
    """
    <style>
    [data-testid="stSidebar"] {
        background-color: #1f4ed8;  /* Blue */
        color: white;
        font-weight: bold;
    }

     [data-testid="stSidebar"] * {
        color: white;
    }

    .st-emotion-cache-4rsbii, .st-emotion-cache-14vh5up  {
        background-color: #eff3ff;  
    }

    .st-emotion-cache-15nprkh, .st-emotion-cache-15nprkh{
        background-color: #ffffff;      
        box-shadow: 0 4px 8px 0 rgba(0, 0, 0, 0.2), 0 6px 20px 0 rgba(0, 0, 0, 0.19);

    }

    .st-emotion-cache-1lsfsc6, .st-dr, .st-dr {
        background-color: #ffffff;
    }

    </style>
    """,
    unsafe_allow_html=True
)

# Placeholder functions for the NLP pipeline
def anonymize_text(text):
    """
    TODO: Insert CamemBERT anonymization code here
    """
    # Anonymization using the MedicalTextAnonymizer pipeline
    anonymizer = MedicalTextAnonymizer(
        chunk_size=500,
        chunk_overlap=100,
        confidence_threshold=0.5
    )
    # Get anonymization results
    results = anonymizer.anonymize_text(text)
    
    # Result formatting for display
    output = anonymizer.display_results(
        results,
        show_dectected_entities=True,
        stat=True
    )

    anonymized_text = results["anonymized_text"]

    return output, anonymized_text

def extract_information(anonymized_text):
    """
    TODO: Insert XML extraction using fine tuned model here
    """
    # Define the prompt for the fine-tuned model
    prompt = ""
    prompt_path = "prompt.txt" 
    ""
    # Load prompt from file
    if os.path.exists(prompt_path):
        with open(prompt_path, "r", encoding="utf-8") as f:
            prompt = f.read()
    else:      
        raise FileNotFoundError("Prompt file not found: prompts/extraction_prompt.txt")
    print(prompt)

    # Call the fine-tuned model to extract lifestyle, treatment, comorbidities
    ... # Placeholder for model inference code


    # Placeholder: return dummy XML
    return "<xml><patient><name>John Doe</name><age>30</age></patient></xml>"

def convert_xml_to_json(xml):
    """
    TODO: Insert XML → JSON conversion code here
    """
    # Placeholder: return dummy JSON
    return {
        "patient": {
            "name": "John Doe",
            "age": 30,
            "lifestyle": {"smoking": "yes", "alcohol": "no"},
            "usual_treatment": ["med1", "med2"],
            "comorbidities": ["diabetes", "hypertension"]
        }
    }

def map_atc(treatment_list):
    """
    TODO: Insert ATC mapping for usual treatment here
    """
    # Placeholder: return as is
    return treatment_list

def map_mesh(comorbidities_list):
    """
    TODO: Insert MeSH mapping for comorbidities here
    """
    # Placeholder: return as is
    return comorbidities_list

def classify_lifestyle(json_data):
    """
    TODO: Insert BERT classification for lifestyle here
    """
    # Placeholder: extract from json
    lifestyle = json_data.get("patient", {}).get("lifestyle", {})
    return lifestyle

# Utility function to extract text from PDF
def extract_text_from_pdf(file):
    pdf_reader = PyPDF2.PdfReader(file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text


# Page configuration
st.set_page_config(page_title="Clinical NLP Extraction Demo – Public Health AI", layout="wide")

# Initialize session state
if 'raw_text' not in st.session_state:
    st.session_state.raw_text = None
    st.session_state.anonymized_text = None
    st.session_state.xml_output = None
    st.session_state.json_output = None
    st.session_state.lifestyle_df = pd.DataFrame()
    st.session_state.treatment_df = pd.DataFrame()
    st.session_state.comorbidities_df = pd.DataFrame()

# Sidebar navigation
with st.sidebar:
    st.title("Navigation")
    step = st.radio("Select Step", ["Upload text", "Anonymization", "Extraction", "Results"])

# Main content based on selected step
if step == "Upload text":
    st.header("Upload Raw Clinical Text")
    uploaded_file = st.file_uploader("Upload .txt or .pdf file", type=["txt", "pdf"])
    if uploaded_file is not None:
        if uploaded_file.type == "text/plain":
            st.session_state.raw_text = StringIO(uploaded_file.getvalue().decode("utf-8")).read()
        elif uploaded_file.type == "application/pdf":
            st.session_state.raw_text = extract_text_from_pdf(uploaded_file)
        with st.expander("Preview Raw Text"):
            st.text_area("Raw Text", st.session_state.raw_text, height=300, disabled=True)

elif step == "Anonymization":
    st.header("Anonymization")
    if st.session_state.raw_text is None:
        st.warning("Please upload text first.")
    else:
        output_display = "" # Results of the anonymization process to display
        if st.button("Run Anonymization"):
            with st.spinner("Anonymizing..."):
                output_display, st.session_state.anonymized_text = anonymize_text(st.session_state.raw_text)
            st.success("Anonymization complete.")

        if st.session_state.anonymized_text:
            with st.expander("Anonymized Text"):
                st.code(output_display, language="text")
                # st.text_area("Anonymized Text", st.session_state.anonymized_text, height=300, disabled=True)

elif step == "Extraction":
    st.header("Information Extraction")
    if st.session_state.anonymized_text is None:
        st.warning("Please run anonymization first.")
    else:
        if st.button("Run Extraction"):
            with st.spinner("Extracting..."):
                st.session_state.xml_output = extract_information(st.session_state.anonymized_text)

                st.session_state.json_output = convert_xml_to_json(st.session_state.xml_output)


                # Process JSON to dataframes
                lifestyle_data = classify_lifestyle(st.session_state.json_output)
                st.session_state.lifestyle_df = pd.DataFrame([lifestyle_data]) if lifestyle_data else pd.DataFrame()
                treatment_list = st.session_state.json_output.get("patient", {}).get("usual_treatment", [])
                st.session_state.treatment_df = pd.DataFrame({"Treatment": map_atc(treatment_list)})
                comorbidities_list = st.session_state.json_output.get("patient", {}).get("comorbidities", [])
                st.session_state.comorbidities_df = pd.DataFrame({"Comorbidity": map_mesh(comorbidities_list)})
            st.success("Extraction complete.")
        if st.session_state.xml_output:
            with st.expander("XML Output"):
                st.code(st.session_state.xml_output, language="xml")
        if st.session_state.json_output:
            with st.expander("JSON Output"):
                st.json(st.session_state.json_output)

elif step == "Results":
    st.header("Structured Results")
    if st.session_state.lifestyle_df.empty:
        st.warning("Please run extraction first.")
    else:
        tab1, tab2, tab3 = st.tabs(["Lifestyle", "Usual Treatment", "Comorbidities"])
        with tab1:
            st.subheader("Lifestyle")
            st.dataframe(st.session_state.lifestyle_df)
            csv = st.session_state.lifestyle_df.to_csv(index=False)
            st.download_button("Download CSV", csv, "lifestyle.csv", "text/csv")
            json_str = st.session_state.lifestyle_df.to_json(orient="records")
            st.download_button("Download JSON", json_str, "lifestyle.json", "application/json")
        with tab2:
            st.subheader("Usual Treatment")
            st.dataframe(st.session_state.treatment_df)
            csv = st.session_state.treatment_df.to_csv(index=False)
            st.download_button("Download CSV", csv, "treatment.csv", "text/csv")
            json_str = st.session_state.treatment_df.to_json(orient="records")
            st.download_button("Download JSON", json_str, "treatment.json", "application/json")
        with tab3:
            st.subheader("Comorbidities")
            st.dataframe(st.session_state.comorbidities_df)
            csv = st.session_state.comorbidities_df.to_csv(index=False)
            st.download_button("Download CSV", csv, "comorbidities.csv", "text/csv")
            json_str = st.session_state.comorbidities_df.to_json(orient="records")
            st.download_button("Download JSON", json_str, "comorbidities.json", "application/json")