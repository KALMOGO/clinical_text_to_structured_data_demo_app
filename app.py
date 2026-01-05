import streamlit as st
import json
import sys
import os
import time
import pandas as pd
from io import StringIO
import PyPDF2
import asyncio

from src.data_anonymization import MedicalTextAnonymizer
from src.extraction import process_csv
from src.structured_results import json_to_mesh_mapped_dataframe
from src.extraction import run_async
from src.extraction import split_obser_extraction
from src.extraction.convert_medical_history import convert_medical_history
from src.extraction import ComorbidityICD10Converter
from src.extraction import LifestyleExtractor


# Ensure the project's `src` directory is on sys.path so imports resolve
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SRC  = os.path.join(ROOT, 'src')
sys.path.insert(0, SRC)



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

    # Call the fine-tuned model to extract lifestyle, treatment, comorbidities
    # Placeholder for model inference code
    payload = {"text": anonymized_text}
    async_result_xml = asyncio.run(run_async(payload))

    ### TODO: Create obs_labelled.csv file from the model extration output
    patient_id = "227"  # Placeholder patient ID # 

    data = {
        'PatientID': patient_id,
        'labellised_observation': async_result_xml
    }
    obs_labelled_df = pd.DataFrame([data])
    
    # Create obs_labelled.csv
    split_obser_extraction(obs_labelled_df)

    # preprocess  comorbidities
    convert_medical_history()

    INPUT_PATH = "src/extraction/extraction_dataset/obs_labelled.csv"
    OUTPUT_PATH = "src/extraction/extraction_dataset/preprocessed"
    process_csv(INPUT_PATH, OUTPUT_PATH)

    df = pd.read_csv(INPUT_PATH)
    #print(df.head())

    # Placeholder: return dummy XML
    return async_result_xml


def create_comorbidities_ic10_df():
    converter = ComorbidityICD10Converter()

    # CSV processing
    df = converter.process_csv(
        input_file="src/extraction/extraction_dataset/comorbidities_output.csv",
        output_file="comorbidites_icd10.csv",
    )
    return df

def create_lifestyle_df():
    extractor = LifestyleExtractor()

    # CSV processing
    df = extractor.process_csv(
        input_csv="src/extraction/extraction_dataset/lifestyle.csv",
        output_csv="lifestyle_extracted.csv",
    )

    return df


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

# Utility function to extract text from PDF
def extract_text_from_pdf(file):
    pdf_reader = PyPDF2.PdfReader(file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text


def display_json(json_file_path):
    with open(json_file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    MAX_OBJECTS = 30

    st.info(f"Display limited to the first {MAX_OBJECTS} JSON objects.")

    # Case 1: JSON is a list
    if isinstance(data, list):
        limited_data = data[:MAX_OBJECTS]
        st.json(limited_data)

    # Case 2: JSON is a dict
    elif isinstance(data, dict):
        limited_data = dict(list(data.items())[:MAX_OBJECTS])
        st.json(limited_data)

    else:
        st.warning("Unsupported JSON format.")

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
                start = time.time() # Time measurement start
                output_display, st.session_state.anonymized_text = anonymize_text(st.session_state.raw_text)
                end = time.time() # Time measurement end
            st.success(f"Anonymization complete.  {end - start:.2f} seconds taken.")

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
                start = time.time() # Time measurement start
                # Extract information to XML with AI model and convert to JSON
                st.session_state.xml_output = extract_information(st.session_state.anonymized_text)
                st.session_state.json_output = convert_xml_to_json(st.session_state.xml_output)

                # Process JSON to dataframes for structured results lifestyle, treatment, comorbidities
                st.session_state.lifestyle_df = create_lifestyle_df()
                st.session_state.treatment_df = json_to_mesh_mapped_dataframe(
                json_path="src/extraction/extraction_dataset/preprocessed/usual_treatment.json",
                mesh_data_path="src/structured_results/dictionnaries/dict_med.csv",
                output_path="src/structured_results/output"
                )
                st.session_state.comorbidities_df = create_comorbidities_ic10_df()
                end = time.time() # Time measurement end

            st.success(f"Extraction complete. {end - start:.2f} seconds taken.")
            
        if st.session_state.xml_output:
            with st.expander("Extraction Results (XML)"):
                st.code(st.session_state.xml_output, language="xml")

        if st.session_state.json_output:
            with st.expander("JSON Output Lifestyle"):
                json_file_path = "src/extraction/extraction_dataset/preprocessed/lifestyle.json"
                display_json(json_file_path)
            
            with st.expander("JSON Output Treatment"):
                json_file_path = "src/extraction/extraction_dataset/preprocessed/usual_treatment.json"
                display_json(json_file_path)

            with st.expander("JSON Output Comorbidities"):
                json_file_path = "src/extraction/extraction_dataset/preprocessed/medical_history.json"
                display_json(json_file_path)

elif step == "Results":
    st.header("Structured Results")
    if st.session_state.lifestyle_df.empty:
        st.warning("Please run extraction first.")
    else:
        tab1, tab2, tab3 = st.tabs(["Usual Treatment", "Comorbidities", "Lifestyle"])
        
        with tab1:
            col1, col2, col3 = st.columns([4, 1, 1])
            with col1:
                st.subheader("Usual Treatment")
            with col2:
                csv = st.session_state.treatment_df.to_csv(index=False)
                st.download_button(
                    "Download CSV",
                    csv,
                    "treatment.csv",
                    "text/csv"
                )
            with col3:
                json_str = st.session_state.treatment_df.to_json(orient="records")
                st.download_button(
                    "DownloadJSON",
                    json_str,
                    "treatment.json",
                    "application/json"
                )
            
            edited_df = st.data_editor(
                st.session_state.treatment_df,
                num_rows="dynamic",
                width="stretch"
            )
            # st.dataframe()
            st.session_state.treatment_df = edited_df

        with tab2:
            col1, col2, col3 = st.columns([4, 1, 1])
            with col1:
                st.subheader("Comorbidities")

            
            with col2:
                csv = st.session_state.comorbidities_df.to_csv(index=False)
                st.download_button(
                    "Download CSV",
                    csv,
                    "comorbidities.csv",
                    "text/csv"
                )
            with col3:
                json_str = st.session_state.comorbidities_df.to_json(orient="records")
                st.download_button(
                    "DownloadJSON",
                    json_str,
                    "comorbidities.json",
                    "application/json"
                )
            
            edited_df = st.data_editor(
                st.session_state.comorbidities_df,
                num_rows="dynamic",
                width="stretch"
            )
            # st.dataframe()
            st.session_state.comorbidities_df = edited_df

        with tab3:
            col1, col2, col3 = st.columns([4, 1, 1])
            with col1:
                st.subheader("Lifestyle")

            
            with col2:
                csv = st.session_state.lifestyle_df.to_csv(index=False)
                st.download_button(
                    "Download CSV",
                    csv,
                    "lifestyle.csv",
                    "text/csv"
                )
            with col3:
                json_str = st.session_state.lifestyle_df.to_json(orient="records")
                st.download_button(
                    "DownloadJSON",
                    json_str,
                    "lifestyle.json",
                    "application/json"
                )
            
            edited_df = st.data_editor(
                st.session_state.lifestyle_df,
                num_rows="dynamic",
                width="stretch"
            )
            # st.dataframe()
            st.session_state.lifestyle_df = edited_df

