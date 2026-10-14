"""
app.py — La page web du chatbot (interface construite avec Streamlit).

Lancer :  streamlit run app.py
Streamlit relit ce fichier de haut en bas à chaque action de l'utilisateur ;
ce qui doit être conservé entre deux actions est rangé dans st.session_state.
"""
import os

import streamlit as st

import config
from rag.lecture import lire_document
from rag.decoupage import decouper
from rag.index import Index
from rag.assistant import repondre

st.set_page_config(page_title="Assistant Réglementation Pharma Maroc", page_icon="💊", layout="wide")


# ----------------------------------------------------------------------------- clé API
def lire_cle_api() -> str:
    """Cherche la clé : 1) fichier secrets de Streamlit, 2) variable d'environnement, 3) saisie à l'écran."""
    try:
        if "GROQ_API_KEY" in st.secrets:
            return st.secrets["GROQ_API_KEY"]
    except Exception:
        pass
    return os.environ.get("GROQ_API_KEY", "") or st.session_state.get("cle_saisie", "")


# ----------------------------------------------------------------------------- index
@st.cache_resource(show_spinner="Préparation de la base documentaire…")
def charger_index() -> Index:
    """Exécuté une seule fois : charge l'index, ou le construit à partir du dossier documents/."""
    index = Index()
    if not index.charger():
        config.DOSSIER_DOCUMENTS.mkdir(exist_ok=True)
        for fichier in sorted(config.DOSSIER_DOCUMENTS.iterdir()):
            if fichier.suffix.lower() in (".pdf", ".docx", ".txt", ".md"):
                index.ajouter(decouper(lire_document(fichier.name, fichier.read_bytes())))
        index.sauvegarder()
    return index


index = charger_index()
if "messages" not in st.session_state:
    st.session_state.messages = []


# ----------------------------------------------------------------------------- barre latérale
with st.sidebar:
    st.title("💊 Réglementation Pharma")
    st.caption("Chatbot RAG — Axe 4 du PFE")

    cle_api = lire_cle_api()
    if cle_api:
        st.success("Clé API Groq détectée", icon="🔑")
    else:
        st.warning("Aucune clé API : mode démonstration (passages trouvés, sans réponse rédigée).", icon="⚠️")
        st.text_input("Coller votre clé API Groq (gsk_…)", type="password", key="cle_saisie")

    st.divider()
    st.subheader("📚 Base documentaire")
    fichiers = st.file_uploader("Ajouter des documents (PDF, Word, TXT)", type=["pdf", "docx", "txt", "md"],
                                accept_multiple_files=True)
    if fichiers and st.button("Analyser et indexer", type="primary", use_container_width=True):
        deja = set(index.sources())
        with st.spinner("Lecture, découpage et indexation…"):
            for f in fichiers:
                if f.name in deja:
                    continue
                passages = decouper(lire_document(f.name, f.getvalue()))
                index.ajouter(passages)
                st.toast(f"{f.name} : {len(passages)} passages indexés")
            index.sauvegarder()
        st.rerun()

    sources = index.sources()
    if sources:
        for nom, n in sources.items():
            st.markdown(f"- **{nom}** · {n} passages")
    else:
        st.info("Aucun document pour l'instant. Ajoutez vos textes de référence.")
    if index.modele is None:
        st.caption("Recherche par mots-clés seulement (modèle de sens indisponible).")

    st.divider()
    st.subheader("⚙️ Réglages")
    web = st.toggle("Chercher aussi sur Internet (sites officiels : BO, AMMPS, OMS, EMA)", value=False,
                    help="Plus lent et consomme davantage le quota gratuit. Les liens hors sites officiels sont signalés à part.")
    k = st.slider("Passages consultés par question", 3, 12, config.NB_PASSAGES)
    if st.button("Effacer la conversation", use_container_width=True):
        st.session_state.messages = []
        st.rerun()


# ----------------------------------------------------------------------------- erreurs compréhensibles
def message_erreur(e: Exception) -> str:
    """Traduit les erreurs de Groq en consignes claires pour l'utilisateur."""
    nom, texte = type(e).__name__, str(e)
    if "Authentication" in nom or "401" in texte:
        return "❌ Clé API refusée : vérifiez la clé Groq (elle commence par gsk_) ou créez-en une nouvelle."
    if "RateLimit" in nom or "429" in texte:
        return ("⏳ Quota gratuit de Groq momentanément atteint (nombre de requêtes ou de mots par minute). "
                "Patientez une minute, ou réduisez le nombre de passages / désactivez la recherche Internet.")
    if "413" in texte or "too large" in texte.lower():
        return "📏 Question trop volumineuse pour le quota gratuit : réduisez le nombre de passages consultés."
    if "Connection" in nom:
        return "🌐 Pas de connexion avec Groq : vérifiez votre accès Internet."
    return f"❌ Erreur lors de l'appel au modèle : {texte}"


# ----------------------------------------------------------------------------- affichage d'une réponse
def afficher_sources(message: dict):
    if message.get("passages"):
        with st.expander(f"📄 {len(message['passages'])} passages de vos documents"):
            for i, p in enumerate(message["passages"], start=1):
                page = f", p. {p['page']}" if p.get("page") else ""
                st.markdown(f"**[D{i}] {p['source']}{page}**")
                st.caption(p["texte"][:700] + ("…" if len(p["texte"]) > 700 else ""))
    if message.get("sources_web"):
        with st.expander(f"🌐 {len(message['sources_web'])} sources officielles consultées en ligne"):
            for s in message["sources_web"]:
                st.markdown(f"- [{s['titre']}]({s['url']})")
    if message.get("autres_liens"):
        with st.expander(f"⚠️ {len(message['autres_liens'])} liens hors sites officiels (à ne pas citer sans vérification)"):
            for s in message["autres_liens"]:
                st.markdown(f"- [{s['titre']}]({s['url']})")


# ----------------------------------------------------------------------------- page principale
st.title("Assistant de réglementation pharmaceutique — Maroc")
st.caption("Répond à partir de vos documents (et, en option, des sites officiels : Bulletin officiel, AMMPS, OMS, EMA), "
           "en citant ses sources. Outil d'aide : vérifiez toujours le texte officiel.")

question = st.chat_input("Posez votre question (ex. : que change la loi 27-26 pour la pharmacovigilance ?)")

if not st.session_state.messages and not question:
    st.markdown("##### Exemples de questions")
    exemples = [
        "Quelles sont les cinq conditions de l'AMM conditionnelle prévue par l'article 8 bis ?",
        "Quels sont les délais de libération officielle des lots de vaccins au Maroc ?",
        "Quelles dispositions de la loi 27-26 attendent encore des textes d'application ?",
        "Quelle différence entre le niveau ML3 de l'OMS et le statut WLA ?",
    ]
    colonnes = st.columns(2)
    for i, ex in enumerate(exemples):
        if colonnes[i % 2].button(ex, use_container_width=True):
            question = ex

for m in st.session_state.messages:
    with st.chat_message(m["role"], avatar="🧑‍⚕️" if m["role"] == "user" else "💊"):
        st.markdown(m["content"])
        if m["role"] == "assistant":
            afficher_sources(m)

if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user", avatar="🧑‍⚕️"):
        st.markdown(question)

    with st.chat_message("assistant", avatar="💊"):
        passages = index.rechercher(question, k=k)
        if not cle_api:
            texte = ("**Mode démonstration** — ajoutez votre clé API pour obtenir une réponse rédigée. "
                     f"Voici les {len(passages)} passages les plus pertinents trouvés dans vos documents :")
            resultat = {"texte": texte, "sources_web": [], "autres_liens": [], "recherches": []}
        else:
            with st.spinner("Recherche dans les documents" + (" et sur les sites officiels…" if web else "…")):
                historique = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages[:-1]]
                try:
                    resultat = repondre(question, passages, historique, cle_api, recherche_web=web)
                except Exception as e:
                    resultat = {"texte": message_erreur(e), "sources_web": [], "autres_liens": [], "recherches": []}
        message = {"role": "assistant", "content": resultat["texte"], "passages": passages,
                   "sources_web": resultat["sources_web"], "autres_liens": resultat["autres_liens"]}
        st.markdown(message["content"])
        if resultat["recherches"]:
            st.caption("Recherches web effectuées : " + " · ".join(resultat["recherches"]))
        afficher_sources(message)
    st.session_state.messages.append(message)
