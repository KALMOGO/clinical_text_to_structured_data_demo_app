import csv
import re
import os


input_file = 'src/extraction/extraction_dataset/medical_history.csv'
output_file = 'src/extraction/extraction_dataset/comorbidities_output.csv'


def convert_medical_history():

    with open(input_file, 'r', encoding='utf-8') as f_in, \
        open(output_file, 'w', encoding='utf-8', newline='') as f_out:

        reader = csv.DictReader(f_in)
        writer = csv.writer(f_out)

        # Écrire l'en-tête
        writer.writerow(['PatientID', 'Comorbidite'])

        for row in reader:
            patient_id = row['PatientID']
            medical_history = row['medical_history']

            # Extraire toutes les conditions entre les balises <condition></condition>
            conditions = re.findall(r'<condition>(.*?)</condition>', medical_history, re.DOTALL)

            # Écrire une ligne par condition
            for condition in conditions:
                # Nettoyer les espaces superflus
                condition = condition.strip()
                writer.writerow([patient_id, condition])
    
    # delete the input file after processing
    os.remove(input_file)

