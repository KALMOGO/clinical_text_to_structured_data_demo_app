## Extraction with Queewn Model pipeline

Texte médical brut (input)
         ↓
[Prompt Template] ← Fichier prompt.txt
         ↓
[Modèle DeepSeek] ← API DeepSeek (cloud)
         ↓
[Réponse brute du LLM]
         ↓
[StrOutputParser] ← Extrait le texte
         ↓
Résultat formaté (output)