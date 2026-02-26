import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv
from datetime import datetime
import time
from PIL import Image, ImageDraw
import io
import requests
import os
import base64
import pyrebase

# ============================================
# CONFIGURATION DE LA PAGE
# ============================================
st.set_page_config(
    page_title="ANEYOND - Beyond AI",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================
# CHARGEMENT DES CLÉS API
# ============================================
load_dotenv()
gemini_key = os.getenv("GEMINI_API_KEY")
stability_key = os.getenv("STABILITY_API_KEY")

if not gemini_key:
    st.error("🔑 Clé API Gemini non trouvée ! Vérifie ton fichier .env")
    st.stop()

genai.configure(api_key=gemini_key)

# ============================================
# FIREBASE AUTHENTIFICATION
# ============================================
firebase_config = {
    "apiKey": "AIzaSyDScQJzkYR0zeY4fvfBnYDwYp98MoOu3nI",
    "authDomain": "anyend-3bbc5.firebaseapp.com",
    "projectId": "anyend-3bbc5",
    "storageBucket": "anyend-3bbc5.firebasestorage.app",
    "messagingSenderId": "183468946632",
    "appId": "1:183468946632:web:88aeb5d8a0daa42362192d",
    "databaseURL": "https://anyend-3bbc5.firebaseio.com"  # nécessaire pour pyrebase
}
firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()

# ============================================
# STYLE CSS (inspiré de ChatGPT)
# ============================================
st.markdown("""
<style>
    /* Fond général */
    .stApp {
        background: linear-gradient(135deg, #0A1929 0%, #1E3A8A 100%);
        color: white;
    }
    
    /* Sidebar - style ChatGPT */
    [data-testid="stSidebar"] {
        background-color: #1E1E1E;
        border-right: 1px solid #333;
    }
    [data-testid="stSidebar"] .stMarkdown {
        color: #ECECF1;
    }
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
        color: #FFFFFF !important;
    }
    [data-testid="stSidebar"] .stRadio > div {
        gap: 0px;
    }
    [data-testid="stSidebar"] .stRadio label {
        background-color: transparent;
        color: #ECECF1;
        padding: 10px 15px;
        border-radius: 5px;
        font-weight: 500;
        transition: background 0.2s;
    }
    [data-testid="stSidebar"] .stRadio label:hover {
        background-color: #2D2D2D;
    }
    [data-testid="stSidebar"] .stRadio label[data-baseweb="radio"]:has(input:checked) {
        background-color: #2D2D2D;
        border-left: 4px solid #3B82F6;
    }
    
    /* Suppression des avatars */
    [data-testid="chat-avatar"] {
        display: none !important;
    }
    
    /* Bulles de message */
    [data-testid="chat-message-user"] {
        display: flex;
        justify-content: flex-end !important;
        margin: 10px 0;
    }
    [data-testid="chat-message-user"] [data-testid="chat-message-content"] {
        background: linear-gradient(135deg, #3B82F6, #1E4A8A) !important;
        color: white !important;
        border-radius: 20px 20px 5px 20px !important;
        padding: 12px 18px !important;
        max-width: 70% !important;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
    }
    [data-testid="chat-message-assistant"] [data-testid="chat-message-content"] {
        background: rgba(20, 30, 40, 0.95) !important;
        color: white !important;
        border-radius: 20px 20px 20px 5px !important;
        padding: 12px 18px !important;
        max-width: 70% !important;
        border: 1px solid rgba(255,255,255,0.1);
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
    }
    
    /* Boutons */
    .stButton button {
        background: linear-gradient(45deg, #1E3A8A, #3B82F6);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 10px 25px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(59,130,246,0.4);
    }
    
    /* Offre limitée */
    .limited-offer {
        background: linear-gradient(45deg, #FFD700, #FFA500);
        color: #0A1929;
        padding: 12px;
        border-radius: 50px;
        text-align: center;
        font-weight: bold;
        animation: pulse 2s infinite;
        margin: 20px 0;
    }
    @keyframes pulse {
        0% { opacity: 1; transform: scale(1); }
        50% { opacity: 0.9; transform: scale(1.02); }
        100% { opacity: 1; transform: scale(1); }
    }
    
    /* Progress bars */
    .stProgress > div > div {
        background: linear-gradient(90deg, #FFD700, #FFA500) !important;
    }
    
    /* Pied de page */
    .footer {
        text-align: center;
        color: #90CAF9;
        font-size: 14px;
        margin-top: 50px;
        padding: 20px;
        border-top: 1px solid rgba(255,255,255,0.1);
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# FONCTIONS DE GESTION DES LIMITES (par utilisateur)
# ============================================
def get_usage_key(user_id):
    """Retourne la clé de session pour un utilisateur donné"""
    return f"usage_{user_id}"

def check_limits(user_id):
    """Initialise ou récupère les limites de l'utilisateur"""
    key = get_usage_key(user_id)
    if key not in st.session_state:
        st.session_state[key] = {
            "messages": 0,
            "images": 0,
            "start_date": datetime.now().strftime("%Y-%m-%d"),
            "first_visit": datetime.now()
        }
    return st.session_state[key]

def update_usage(user_id, feature):
    """Met à jour le compteur d'une fonctionnalité"""
    key = get_usage_key(user_id)
    if key in st.session_state:
        st.session_state[key][feature] += 1

def can_use_feature(user_id, feature, limit):
    """Vérifie si l'utilisateur peut encore utiliser une fonctionnalité"""
    usage = check_limits(user_id)
    remaining = max(0, limit - usage[feature])
    return usage[feature] < limit, remaining

def check_subscription(user_id):
    """À remplacer par une vraie vérification en base de données"""
    return "free"

# ============================================
# FONCTION DE SECOURS (image de fallback)
# ============================================
def create_fallback_image(prompt, error_msg=""):
    img = Image.new('RGB', (1024, 1024), color='#0A1929')
    draw = ImageDraw.Draw(img)
    draw.rectangle([(50, 50), (974, 974)], outline="#3B82F6", width=5)
    draw.text((512, 200), "🚀 ANEYOND", fill="#FFD700", anchor="mm")
    draw.text((512, 400), f"「 {prompt} 」", fill="white", anchor="mm")
    draw.text((512, 500), error_msg, fill="#FF6B6B", anchor="mm")
    return img

# ============================================
# FONCTION DE GÉNÉRATION D'IMAGE (Stability AI)
# ============================================
def generate_image(prompt, style="Réaliste", size="1024x1024"):
    try:
        if not stability_key:
            return create_fallback_image(prompt, "Clé Stability AI manquante")

        style_map = {
            "Réaliste": "photorealistic, highly detailed",
            "Artistique": "artistic, impressionist style",
            "Manga": "anime style, manga",
            "Peinture": "oil painting, canvas texture",
            "3D": "3D render, cinema4d, blender",
            "Dessin animé": "cartoon, pixar style"
        }
        style_text = style_map.get(style, "")
        enhanced_prompt = f"{prompt}, {style_text}" if style_text else prompt

        url = "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image"
        headers = {
            "Authorization": f"Bearer {stability_key}",
            "Content-Type": "application/json"
        }
        body = {
            "text_prompts": [{"text": enhanced_prompt}],
            "cfg_scale": 7,
            "height": 1024,
            "width": 1024,
            "samples": 1,
            "steps": 30,
        }

        response = requests.post(url, headers=headers, json=body, timeout=60)

        if response.status_code == 200:
            data = response.json()
            image_data = base64.b64decode(data["artifacts"][0]["base64"])
            return Image.open(io.BytesIO(image_data))
        else:
            error_msg = f"Erreur Stability AI {response.status_code}"
            try:
                error_details = response.json()
                if "message" in error_details:
                    error_msg += f": {error_details['message']}"
            except:
                pass
            return create_fallback_image(prompt, error_msg)

    except Exception as e:
        return create_fallback_image(prompt, str(e))

# ============================================
# FONCTION D'EXPORT DE CONVERSATION
# ============================================
def export_conversation(messages):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    content = ""
    for msg in messages:
        role = "Vous" if msg["role"] == "user" else "ANEYOND"
        content += f"{role}: {msg['content']}\n\n"
    return content, f"conversation_{timestamp}.txt"

# ============================================
# SIDEBAR (avec authentification Firebase)
# ============================================
with st.sidebar:
    st.markdown("## 🚀 ANEYOND")
    st.markdown("#### Beyond AI")
    st.divider()

    menu = st.radio(
        "Navigation",
        ["💬 Chat", "🎨 Images", "💎 Premium", "📊 Stats"],
        label_visibility="collapsed"
    )

    st.divider()

    st.markdown("### 👤 Mon compte")

    if "user" not in st.session_state:
        # Non connecté : onglets Connexion / Inscription
        tab1, tab2 = st.tabs(["🔑 Connexion", "📝 Inscription"])

        with tab1:
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Mot de passe", type="password", key="login_password")
            if st.button("Se connecter", use_container_width=True):
                try:
                    user = auth.sign_in_with_email_and_password(email, password)
                    st.session_state.user = user
                    st.rerun()
                except Exception as e:
                    st.error(f"Erreur : {e}")

        with tab2:
            new_email = st.text_input("Email", key="signup_email")
            new_password = st.text_input("Mot de passe", type="password", key="signup_password")
            if st.button("S'inscrire", use_container_width=True):
                try:
                    user = auth.create_user_with_email_and_password(new_email, new_password)
                    st.success("Compte créé ! Connectez-vous.")
                except Exception as e:
                    st.error(f"Erreur : {e}")
    else:
        # Connecté
        user_id = st.session_state.user['localId']
        user_email = st.session_state.user['email']
        st.write(f"Connecté : **{user_email}**")

        if check_subscription(user_id) != "premium":
            usage = check_limits(user_id)
            days_used = (datetime.now() - usage["first_visit"]).days
            days_left = max(0, 7 - days_used)

            st.markdown("#### 🎁 Version gratuite")
            st.progress(min(usage["messages"]/50, 1.0), text=f"💬 {usage['messages']}/50 messages")
            st.progress(min(usage["images"]/10, 1.0), text=f"🎨 {usage['images']}/10 images")

            if days_left > 0:
                st.info(f"⏱️ {days_left} jours d'essai restants")
            else:
                st.warning("⚠️ Période d'essai terminée")
        else:
            st.success("✨ Compte Premium actif")

        if st.button("🚪 Se déconnecter", use_container_width=True):
            del st.session_state.user
            st.rerun()

# ============================================
# PAGE CHAT
# ============================================
if menu == "💬 Chat":
    st.markdown("<h1 style='text-align: center;'>💬 Assistant Intelligent</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #90CAF9;'>Posez-moi toutes vos questions</p>", unsafe_allow_html=True)

    # Récupération de l'utilisateur connecté (si existant)
    user_id = None
    if "user" in st.session_state:
        user_id = st.session_state.user['localId']
        usage = check_limits(user_id)
        if usage["messages"] >= 50:
            st.warning("Limite de messages atteinte. Passez en Premium.")
            if st.button("✨ PASSER PREMIUM", type="primary"):
                st.session_state.menu = "💎 Premium"
                st.rerun()
            st.stop()

    # Initialisation de la conversation
    if "messages" not in st.session_state:
        st.session_state.messages = [{
            "role": "assistant",
            "content": "👋 Bonjour ! Je suis **ANEYOND**. Comment puis-je vous aider ?"
        }]
        st.session_state.chat = genai.GenerativeModel('gemini-2.5-flash').start_chat(history=[])

    # Affichage des messages
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Zone de saisie
    if prompt := st.chat_input("💭 Votre message..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.chat_message("assistant"):
            with st.spinner("✨ Réflexion..."):
                try:
                    response = st.session_state.chat.send_message(prompt)
                    st.markdown(response.text)
                    st.session_state.messages.append({"role": "assistant", "content": response.text})
                    if user_id:
                        update_usage(user_id, "messages")
                except Exception as e:
                    st.error(f"❌ Erreur: {e}")
        st.rerun()

    # Boutons d'action
    col1, col2, col3 = st.columns([1,1,1])
    with col1:
        if st.button("🗑️ Nouvelle discussion", use_container_width=True):
            st.session_state.messages = [{
                "role": "assistant",
                "content": "👋 Bonjour ! Je suis **ANEYOND**. Comment puis-je vous aider ?"
            }]
            st.session_state.chat = genai.GenerativeModel('gemini-2.5-flash').start_chat(history=[])
            st.rerun()
    with col2:
        if st.button("📥 Exporter l'historique", use_container_width=True):
            if st.session_state.messages:
                content, filename = export_conversation(st.session_state.messages)
                st.download_button(
                    label="📄 Télécharger le fichier",
                    data=content,
                    file_name=filename,
                    mime="text/plain"
                )
            else:
                st.info("Aucune conversation à exporter")

# ============================================
# PAGE IMAGES
# ============================================
elif menu == "🎨 Images":
    st.markdown("<h1 style='text-align: center;'>🎨 Génération d'Images</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #90CAF9;'>Décrivez une image et cliquez sur Générer</p>", unsafe_allow_html=True)

    user_id = None
    if "user" in st.session_state:
        user_id = st.session_state.user['localId']
        can_use, remaining = can_use_feature(user_id, "images", 10)
        if not can_use:
            st.warning("Limite d'images atteinte. Passez en Premium.")
            if st.button("✨ PASSER PREMIUM", type="primary"):
                st.session_state.menu = "💎 Premium"
                st.rerun()
            st.stop()
        else:
            st.success(f"🎨 **{remaining} images restantes** aujourd'hui")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 📝 Description")
        suggestions = [
            ("🐱 Chat", "un chat noir aux yeux verts"),
            ("🐶 Chien", "un golden retriever jouant à la balle"),
            ("🏎️ Voiture", "une Lamborghini rouge"),
            ("🌅 Paysage", "coucher de soleil sur la plage"),
            ("🏰 Fantasy", "un château médiéval")
        ]
        cols = st.columns(5)
        for i, (emoji, text) in enumerate(suggestions):
            with cols[i]:
                if st.button(emoji, key=f"sugg_{i}"):
                    st.session_state.prompt = text

        prompt = st.text_area(
            "Décrivez l'image",
            value=st.session_state.get('prompt', ''),
            height=120,
            placeholder="Ex: une Lamborghini rouge à New York",
            key="image_prompt"
        )

        col_style, col_size = st.columns(2)
        with col_style:
            style = st.selectbox("🎨 Style", ["Réaliste", "Artistique", "Manga", "Peinture", "3D", "Dessin animé"])
        with col_size:
            size = st.selectbox("📐 Taille", ["1024x1024", "512x512", "1792x1024"])

        if st.button("🚀 **GÉNÉRER L'IMAGE**", type="primary", use_container_width=True):
            if prompt:
                with st.spinner("🎨 Création en cours... (20-30 secondes)"):
                    image = generate_image(prompt, style, size)
                    st.session_state.generated_image = image
                    st.session_state.last_prompt = prompt
                    st.session_state.last_style = style
                    if user_id:
                        update_usage(user_id, "images")
                    st.rerun()

    with col2:
        if 'generated_image' in st.session_state:
            st.markdown("### 🖼️ Résultat")
            st.image(st.session_state.generated_image, use_column_width=True)
            with st.expander("📋 Détails"):
                st.write(f"**Prompt :** {st.session_state.last_prompt}")
                st.write(f"**Style :** {st.session_state.last_style}")

            buf = io.BytesIO()
            st.session_state.generated_image.save(buf, format="PNG")
            byte_im = buf.getvalue()
            st.download_button(
                "💾 Télécharger l'image",
                byte_im,
                f"aneyond_{int(time.time())}.png",
                "image/png",
                use_container_width=True
            )
            if st.button("🔄 Nouvelle image", use_container_width=True):
                del st.session_state.generated_image
                st.rerun()
        else:
            st.info("👈 Décris une image et clique sur Générer")

# ============================================
# PAGE PREMIUM
# ============================================
elif menu == "💎 Premium":
    st.markdown("<h1 style='text-align: center;'>✨ Passez à la vitesse supérieure</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #90CAF9;'>Débloquez toutes les fonctionnalités</p>", unsafe_allow_html=True)
    st.markdown("""
    <div class='limited-offer'>
        🔥 OFFRE SPÉCIALE : -30% POUR LES 100 PREMIERS 🔥
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <div style='background: rgba(30,58,138,0.3); backdrop-filter: blur(10px); border: 1px solid #3B82F6; border-radius: 20px; padding: 20px; text-align: center;'>
            <h3>🆓 Gratuit</h3>
            <div style='font-size: 36px; font-weight: 700; color: #FFD700;'>0€</div>
            <p>✓ 50 messages/jour<br>✓ 10 images/jour</p>
            <p style='color: #FF6B6B;'>✗ Pas de sauvegarde</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div style='background: rgba(30,58,138,0.3); backdrop-filter: blur(10px); border: 2px solid #FFD700; border-radius: 20px; padding: 20px; text-align: center; transform: scale(1.02);'>
            <h3>⭐ Premium</h3>
            <div style='font-size: 36px; font-weight: 700; color: #FFD700;'>9.99€<span style='font-size:14px;'>/mois</span></div>
            <p>✓ Messages illimités<br>✓ Images illimitées<br>✓ Sauvegarde des conversations<br>✓ Tous les styles</p>
            <p style='color: #FFD700;'>🔥 -30% aujourd'hui</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🚀 **CHOISIR PREMIUM**", use_container_width=True, type="primary"):
            st.balloons()
            st.success("✅ Redirection vers le paiement sécurisé...")

    with col3:
        st.markdown("""
        <div style='background: rgba(30,58,138,0.3); backdrop-filter: blur(10px); border: 1px solid #3B82F6; border-radius: 20px; padding: 20px; text-align: center;'>
            <h3>👑 Annuel</h3>
            <div style='font-size: 36px; font-weight: 700; color: #FFD700;'>99.99€<span style='font-size:14px;'>/an</span></div>
            <p>✓ 2 mois offerts<br>✓ Tout le Premium<br>✓ Support prioritaire</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("👑 **CHOISIR ANNUEL**", use_container_width=True):
            st.balloons()
            st.success("✅ Redirection...")

# ============================================
# PAGE STATISTIQUES
# ============================================
elif menu == "📊 Stats":
    st.markdown("<h1 style='text-align: center;'>📊 Vos statistiques</h1>", unsafe_allow_html=True)

    if "user" in st.session_state:
        user_id = st.session_state.user['localId']
        usage = check_limits(user_id)
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Messages envoyés", usage["messages"])
        with col2:
            st.metric("Images générées", usage["images"])
        with col3:
            days = (datetime.now() - usage["first_visit"]).days
            st.metric("Jours d'utilisation", days)

        st.markdown("### 📈 Activité récente")
        chart_data = {"Lun": 5, "Mar": 8, "Mer": 12, "Jeu": 7, "Ven": 15, "Sam": 10, "Dim": 6}
        st.bar_chart(chart_data)

        if check_subscription(user_id) != "premium":
            st.info("💡 Passez Premium pour des statistiques détaillées et l'historique complet.")
    else:
        st.info("Connectez-vous pour voir vos statistiques.")

# ============================================
# PIED DE PAGE
# ============================================
st.markdown("---")
st.markdown("<p style='text-align: center; color: #90CAF9;'>🚀 ANEYOND - Beyond AI | © 2026</p>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #90CAF9; font-size: 12px;'>7 jours d'essai • Sans engagement • Paiement sécurisé</p>", unsafe_allow_html=True)
