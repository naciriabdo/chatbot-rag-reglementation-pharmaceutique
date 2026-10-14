"""
lecture.py — ÉTAPE 1 du RAG : lire les documents et en extraire le texte.

Un PDF n'est pas du texte « brut » : il faut l'ouvrir avec une bibliothèque (pypdf)
qui sait récupérer le texte page par page. On garde le numéro de page, pour que
le chatbot puisse citer sa source (« Résultats PFE, p. 12 »).
"""
from pathlib import Path
import io
import re

from pypdf import PdfReader
from docx import Document


def _nettoyer(texte: str) -> str:
    """Supprime les espaces en trop et recolle les mots coupés en fin de ligne."""
    texte = texte.replace("­", "")                 # traits d'union invisibles
    texte = re.sub(r"-\n(\w)", r"\1", texte)            # mot coupé : « régle-\nmentation »
    texte = re.sub(r"[ \t]+", " ", texte)
    texte = re.sub(r"\n{3,}", "\n\n", texte)
    return texte.strip()


def lire_document(nom: str, contenu: bytes) -> list[dict]:
    """
    Renvoie une liste de pages : [{"source": nom, "page": 1, "texte": "..."}, ...]
    nom     : nom du fichier (sert à connaître le format et à citer la source)
    contenu : le fichier lui-même, sous forme d'octets
    """
    extension = Path(nom).suffix.lower()
    pages = []

    if extension == ".pdf":
        lecteur = PdfReader(io.BytesIO(contenu))
        for numero, page in enumerate(lecteur.pages, start=1):
            texte = _nettoyer(page.extract_text() or "")
            if texte:
                pages.append({"source": nom, "page": numero, "texte": texte})

    elif extension == ".docx":
        doc = Document(io.BytesIO(contenu))
        texte = "\n".join(p.text for p in doc.paragraphs)
        # Un fichier Word n'a pas de pages fixes : on le traite comme une seule « page »
        pages.append({"source": nom, "page": None, "texte": _nettoyer(texte)})

    elif extension in (".txt", ".md"):
        pages.append({"source": nom, "page": None, "texte": _nettoyer(contenu.decode("utf-8", errors="ignore"))})

    else:
        raise ValueError(f"Format non pris en charge : {extension} (formats acceptés : PDF, DOCX, TXT)")

    return pages
