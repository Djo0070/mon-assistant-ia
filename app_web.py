import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv
import os
from datetime import datetime

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

st.set_page_config(page_title="Mon Assistant IA", page_icon="🤖")
st.title("🤖 Mon Assistant Personnel")
st.caption("Pose-moi toutes tes questions !")

# Initialisation de l'historique
if "messages" not in st.session_state:
    st.session_state.messages = []

# Afficher l'historique
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Zone de saisie
if prompt := st.chat_input("Ta question..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.chat_message("assistant"):
        with st.spinner("Réflexion..."):
            model = genai.GenerativeModel('gemini-2.5-flash')
            response = model.generate_content(prompt)
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
# Sauvegarder la conversation à la fin

modes = {
    "normal": "Tu es un assistant serviable qui répond en français.",
    "prof": "Tu es un professeur patient qui explique tout simplement.",
    "poete": "Tu réponds toujours en rimes et de manière poétique.",
    "chef": "Tu es un chef cuisinier français qui donne des recettes détaillées.",
    "humoriste": "Tu réponds avec humour et fais des blagues.",
    "philosophe": "Tu réponds de manière profonde et philosophique."
}

print("Choisis un mode :")
for i, (mode, desc) in enumerate(modes.items(), 1):
    print(f"{i}. {mode} : {desc}")

choix = input("Ton choix (1-6) : ")
mode_choisi = list(modes.keys())[int(choix)-1]

# Configure le modèle avec la personnalité choisie
model = genai.GenerativeModel(
    'gemini-2.5-flash',
    system_instruction=modes[mode_choisi]
)

import requests
import json
from datetime import datetime

def meteo(ville):
    """Donne la météo d'une ville"""
    # Utilise une API gratuite (ex: wttr.in)
    response = requests.get(f"https://wttr.in/{ville}?format=%t+%c+%w")
    return f"Météo à {ville} : {response.text}"

def calculatrice(expression):
    """Calcule une expression mathématique"""
    try:
        resultat = eval(expression)
        return f"Résultat : {resultat}"
    except:
        return "Expression invalide"

def rappel(texte):
    """Crée un rappel"""
    with open("rappels.txt", "a") as f:
        f.write(f"{datetime.now()}: {texte}\n")
    return "Rappel enregistré !"

def recherche_wikipedia(sujet):
    """Recherche sur Wikipedia"""
    url = f"https://fr.wikipedia.org/api/rest_v1/page/summary/{sujet}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data.get('extract', 'Pas trouvé')
    return "Pas trouvé sur Wikipedia"

import speech_recognition as sr

def ecouter():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("🎤 Parle maintenant...")
        audio = r.listen(source)
    
    try:
        texte = r.recognize_google(audio, language='fr-FR')
        print(f"👤 Toi : {texte}")
        return texte
    except:
        print("❌ Pas compris")
        return None

# Dans ta boucle, remplace input() par :
user_input = ecouter()
if not user_input:
    pass

import pyttsx3

# Initialise la voix
engine = pyttsx3.init()
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[0].id)  # Voix française

def parler(texte):
    print(f"🤖 : {texte}")
    engine.say(texte)
    engine.runAndWait()

# Au lieu de print(), utilise parler()
parler(response.text)

import json
from datetime import datetime

class ConversationLogger:
    def __init__(self):
        self.historique = []
    
    def ajouter(self, role, message):
        self.historique.append({
            "role": role,
            "message": message,
            "time": datetime.now().strftime("%H:%M:%S")
        })
    
    def sauvegarder(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # Sauvegarde en JSON
        with open(f"conversation_{timestamp}.json", "w") as f:
            json.dump(self.historique, f, indent=2)
        
        # Sauvegarde en texte lisible
        with open(f"conversation_{timestamp}.txt", "w") as f:
            for msg in self.historique:
                f.write(f"[{msg['time']}] {msg['role']}: {msg['message']}\n")
        
        print(f"💾 Conversations sauvegardées !")
    
    def charger(self, fichier):
        with open(fichier, 'r') as f:
            self.historique = json.load(f)
        print(f"📂 {len(self.historique)} messages chargés")

# Utilisation
logger = ConversationLogger()
logger.ajouter("user", user_input)
logger.ajouter("assistant", response.text)
# À la fin :
logger.sauvegarder()