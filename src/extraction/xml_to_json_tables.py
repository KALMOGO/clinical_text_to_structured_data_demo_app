#!/usr/bin/env python3
"""
Script de conversion XML vers JSON pour observations médicales
Convertit les colonnes XML du fichier CSV en fichiers JSON séparés
"""

import csv
import xml.etree.ElementTree as ET
import json
import argparse
import os
from typing import Dict, Any, Optional


def xml_element_to_dict(element: ET.Element) -> Any:
    """
    Convertit récursivement un élément XML en dictionnaire Python.

    Args:
        element: Élément XML à convertir

    Returns:
        Dictionnaire, liste ou string selon la structure XML
    """
    # Récupérer les attributs de l'élément
    result = {}
    if element.attrib:
        result.update(element.attrib)

    # Récupérer le texte de l'élément
    text = element.text.strip() if element.text else None

    # Récupérer les éléments enfants
    children = list(element)

    if not children:
        # Pas d'enfants : retourner le texte ou un dict avec attributs
        if not result:
            return text if text else ""
        if text:
            result["_text"] = text
        return result

    # Traiter les éléments enfants
    children_dict = {}
    for child in children:
        child_data = xml_element_to_dict(child)

        # Si l'enfant existe déjà, le convertir en liste
        if child.tag in children_dict:
            if not isinstance(children_dict[child.tag], list):
                children_dict[child.tag] = [children_dict[child.tag]]
            children_dict[child.tag].append(child_data)
        else:
            children_dict[child.tag] = child_data

    # Combiner attributs et enfants
    if result:
        result.update(children_dict)
        if text:
            result["_text"] = text
        return result

    return children_dict


def xml_to_dict(xml_string: str) -> Optional[Dict[str, Any]]:
    """
    Parse une chaîne XML et la convertit en dictionnaire.
    Encapsule le XML dans une balise <root> temporaire si nécessaire.

    Args:
        xml_string: Chaîne XML à parser

    Returns:
        Dictionnaire représentant la structure XML, ou None en cas d'erreur
    """
    if not xml_string or not xml_string.strip():
        return None

    try:
        # Encapsuler le XML dans une balise <root> temporaire
        wrapped_xml = f"<root>{xml_string}</root>"

        # Parser le XML
        root = ET.fromstring(wrapped_xml)

        # Convertir en dictionnaire
        result = xml_element_to_dict(root)

        return result

    except ET.ParseError as e:
        #print(f"Erreur de parsing XML: {e}")
        return None
    except Exception as e:
        #print(f"Erreur inattendue: {e}")
        return None


def process_csv(input_file: str, output_dir: str) -> None:
    """
    Lit le fichier CSV et génère 4 fichiers JSON distincts.

    Args:
        input_file: Chemin du fichier CSV source
        output_dir: Dossier de sortie pour les fichiers JSON
    """

    # Initialiser les dictionnaires pour chaque colonne XML
    data_lbl_obs = {}
    data_usual_treatment = {}
    data_medical_history = {}
    data_lifestyle = {}

    # Compteurs pour le suivi
    total_rows = 0
    errors = 0

    # print(f"Lecture du fichier CSV: {input_file}")
    # print("Traitement en cours...")

    try:
        with open(input_file, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)

            for row in reader:
                total_rows += 1

                # Afficher la progression tous les 1000 patients
                # if total_rows % 1000 == 0:
                #     print(f"  Patients traités: {total_rows}")

                patient_id = row['PatientID']

                # Traiter chaque colonne XML
                # 1. lbl_obs
                if row['lbl_obs']:
                    lbl_obs_dict = xml_to_dict(row['lbl_obs'])
                    if lbl_obs_dict:
                        data_lbl_obs[patient_id] = lbl_obs_dict
                    else:
                        errors += 1
                        #print(f"  Erreur patient {patient_id}: lbl_obs invalide")

                # 2. usual_treatment
                if row['usual_treatment']:
                    usual_treatment_dict = xml_to_dict(row['usual_treatment'])
                    if usual_treatment_dict:
                        data_usual_treatment[patient_id] = usual_treatment_dict
                    else:
                        errors += 1

                # 3. medical_history
                if row['medical_history']:
                    medical_history_dict = xml_to_dict(row['medical_history'])
                    if medical_history_dict:
                        data_medical_history[patient_id] = medical_history_dict
                    else:
                        errors += 1

                # 4. lifestyle
                if row['lifestyle']:
                    lifestyle_dict = xml_to_dict(row['lifestyle'])
                    if lifestyle_dict:
                        data_lifestyle[patient_id] = lifestyle_dict
                    else:
                        errors += 1

    except FileNotFoundError:
        #print(f"ERREUR: Fichier introuvable: {input_file}")
        return
    except Exception as e:
        #print(f"ERREUR lors de la lecture du CSV: {e}")
        return

    # print(f"\nTraitement terminé:")
    # print(f"  Total patients traités: {total_rows}")
    # print(f"  Erreurs de parsing: {errors}")

    # Créer le dossier de sortie si nécessaire
    os.makedirs(output_dir, exist_ok=True)

    # Sauvegarder les 4 fichiers JSON
    # print(f"\nSauvegarde des fichiers JSON dans: {output_dir}")

    files_to_save = [
        ('lbl_obs.json', data_lbl_obs),
        ('usual_treatment.json', data_usual_treatment),
        ('medical_history.json', data_medical_history),
        ('lifestyle.json', data_lifestyle)
    ]

    for filename, data in files_to_save:
        output_path = os.path.join(output_dir, filename)
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            # print(f"  [OK] {filename} - {len(data)} patients")
        except Exception as e:
            raise 
            #print(f"  [ERREUR] Erreur lors de la sauvegarde de {filename}: {e}")

    # print("\nConversion terminée avec succès!")
