import pandas as pd
import numpy as np
import re

def split_obser_extraction(data):

    data['lbl_obs'] = data['labellised_observation'].str.extract(
        r'```xml\s*(.*?)\s*```', 
        flags=re.DOTALL
    )[0]

    data.drop(columns=['labellised_observation'], inplace=True)
    data.set_index('PatientID', inplace=True)

    data['usual_treatment'] = data['lbl_obs'].str.extract(r'<usual_treatment>(.*?)</usual_treatment>', flags=re.DOTALL)[0]
    usual_treatment = data.drop(columns=['lbl_obs'])
    usual_treatment.to_csv("src/extraction/extraction_dataset/usual_treatment.csv")

    data['medical_history'] = data['lbl_obs'].str.extract(r'<medical_history>(.*?)</medical_history>', flags=re.DOTALL)[0]
    medical_history = data.drop(columns=['lbl_obs','usual_treatment'])
    medical_history.to_csv("src/extraction/extraction_dataset/medical_history.csv")


    data['lifestyle'] = data['lbl_obs'].str.extract(r'<lifestyle>(.*?)</lifestyle>', flags=re.DOTALL)[0]
    lifestyle = data.drop(columns=['lbl_obs','usual_treatment','medical_history'])
    lifestyle.to_csv("src/extraction/extraction_dataset/lifestyle.csv")

    data.to_csv("src/extraction/extraction_dataset/obs_labelled.csv")