# List of the PHI in France

## Sources: 

* **RGPD — article 9** 
* **Code de la santé publique**
* **Loi Informatique et Libertés**
* **Guides CNIL sur les données de santé**

## 1. **Données d’identification personnelle**

* Nom, prénom (v)
* Date et lieu de naissance ()
* Adresse postale
* Numéro de téléphone
* Adresse email
* Identifiant patient (IPP)
* Numéro de sécurité sociale (NIR)

* Photos permettant d’identifier la personne
* Biométrie (empreintes, reconnaissance faciale) utilisée en contexte de santé


## 2. **Données médicales**

* Dossiers médicaux électroniques (DMP / DPI)
* Comptes rendus médicaux
* Diagnostic, symptômes, antécédents
* Pathologies actuelles/chroniques
* Plans de soins et traitements
* Prescriptions / ordonnances
* Résultats d’examens biologiques (sang, urine, PCR, etc.)
* Résultats d’imagerie (IRM, scanner, radio, écho)
* Observations de professionnels de santé
* Mesures cliniques (tension, fréquence cardiaque, IMC…)
* Vaccinations
* Données de suivi en télé-surveillance ou télémédecine


## 3. **Données administratives liées au parcours de soins**

* Dates d’hospitalisation et de consultations
* Informations d’admission et de sortie
* Service hospitalier, médecin traitant
* Historique des actes médicaux (CCAM)
* Données du remboursement (Assurance Maladie)
* Données de facturation en lien avec un acte de santé

## 4. **Données sociales et de dépendance**

* Degré d’autonomie (GIR / dépendance)
* Handicap (moteur, mental, sensoriel…)
* Informations relatives à l’ALD (affection de longue durée)
* Données médico-sociales (ESMS : EHPAD, IME, etc.)


# 5. **Données génétiques**

* Tests ADN
* Analyses génétiques
* Susceptibilités ou risques héréditaires

# 6. **Données biométriques en lien avec la santé**

* ECG, EEG, EMG
* Signaux physiologiques enregistrés par capteurs
* Reconnaissance vocale utilisée pour analyser des troubles


## 7. **Données issues d’applications ou objets connectés santé**

* Applications de santé (Diabète, cardio, sommeil…)
* Montres connectées (rythme cardiaque, saturation O2)
* Capteurs glycémiques
* Données d’activité physique si utilisées en santé

## 8. **Données de santé mentale**

* Antécédents psychiatriques
* Suivi psychologique
* Diagnostic psychologique ou psychiatrique
* Traitements psychotropes

## 9. **Données de reproduction et sexualité**

* IVG, PMA, infertilité
* Contraception
* IST / dépistages VIH
* Suivi gynécologique et obstétrical

## 10. **Données d’urgence et de sécurité**

* Allergies graves
* Risque vital, code “alerte”
* Consentement ou directives anticipées
* Donneurs/dons d’organes


## 11. **Données indirectement révélatrices de santé**

* Rendez-vous dans un centre de cancérologie
* Entrée dans une unité psychiatrique
* Achat de médicament avec carte de fidélité
* Participation à un programme de rééducation


## Pipeline Flow:

INPUT TEXT 
  ↓
[1] Split into chunks (for handling long texts)
  ↓
[2] LangChain Runnable Parallel Chains (for speed)
  ↓
[3] Each chunk → iiiorg/piiranha-v1-detect-personal-information model
  ↓
[4] Intermediate output → Jean-Baptiste/camembert-ner-with-dates model
  ↓
[5] Combine results from all chunks
  ↓
[6] Map detected entities back to original INPUT text positions
  ↓
ANONYMIZED OUTPUT TEXT