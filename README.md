# Assistant de réglementation pharmaceutique — Maroc (chatbot RAG)

Axe 4 du PFE « Réforme du système de régulation pharmaceutique au Maroc ».
Le chatbot répond aux questions de réglementation pharmaceutique à partir :
1. de vos documents de référence (dossier `documents/` ou téléversement dans la page) ;
2. en option, de recherches en ligne orientées vers les **sites officiels** (Bulletin officiel, AMMPS, Ministère de la Santé, OMS, EMA, EUR-Lex…) ; les liens hors liste sont signalés à part.

Le modèle d'IA est hébergé par **Groq** (clé API gratuite). Chaque réponse cite ses sources : `[D1]` pour un passage de vos documents, lien cliquable pour une source web.

## Démarrage rapide (Windows)
1. Installer Python 3.12 (cocher **Add python.exe to PATH**).
2. Double-cliquer sur `installer.bat` (une seule fois).
3. Créer une clé gratuite sur https://console.groq.com/keys, puis copier `.streamlit/secrets.toml.example` en `.streamlit/secrets.toml` et y coller la clé (`gsk_…`).
4. Double-cliquer sur `lancer_chatbot.bat` : la page s'ouvre sur http://localhost:8501.

Sans clé API, l'application fonctionne en **mode démonstration** : elle affiche les passages trouvés, sans réponse rédigée.

## Organisation du code
| Fichier | Rôle |
|---|---|
| `config.py` | Tous les réglages : modèle Groq, sites officiels, taille des passages |
| `rag/lecture.py` | Étape 1 — lire les PDF / Word / TXT, page par page |
| `rag/decoupage.py` | Étape 2 — découper en passages de ~200 mots |
| `rag/index.py` | Étapes 3-4 — indexer (mots-clés BM25 + sens) et retrouver les passages pertinents |
| `rag/assistant.py` | Étape 5 — rédiger la réponse avec le modèle Groq, recherche web en option, tri des liens officiels |
| `app.py` | La page web (Streamlit) |

## Mise en ligne
GitHub (sans le fichier `secrets.toml`) puis Streamlit Community Cloud : la clé se colle dans *Advanced settings → Secrets*.
Voir le guide PDF, étapes 16 et 17.

## Avertissement
Outil d'aide à la recherche documentaire : il ne remplace ni le texte publié au Bulletin officiel, ni un avis de l'AMMPS.
