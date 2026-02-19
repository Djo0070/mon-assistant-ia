import streamlit as st
import google.generativeai as genai
import os
from dotenv import load_dotenv
from datetime import datetime
import time
from PIL import Image
import io
import requests

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
# CHARGEMENT DE LA CLÉ API
# ============================================
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    st.error("🔑 Clé API non trouvée ! Vérifie ton fichier .env")
    st.stop()

genai.configure(api_key=api_key)

# ============================================
# STYLE CSS AMÉLIORÉ
# ============================================
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #0A1929 0%, #1E3A8A 100%);
    }
    
    h1, h2, h3 {
        color: white !important;
        font-weight: 700 !important;
    }
    
    /* SUPPRIMER LES AVATARS */
    [data-testid="chat-avatar"] {
        display: none !important;
    }
    
    /* MESSAGES UTILISATEUR */
    [data-testid="chat-message-user"] {
        display: flex;
        justify-content: flex-end !important;
        margin: 10px 0 !important;
    }
    
    [data-testid="chat-message-user"] [data-testid="chat-message-content"] {
        background: linear-gradient(135deg, #3B82F6, #1E4A8A) !important;
        color: white !important;
        border-radius: 20px 20px 5px 20px !important;
        padding: 12px 18px !important;
        max-width: 70% !important;
        box-shadow: 0 4px 15px rgba(59, 130, 246, 0.3) !important;
    }
    
    /* MESSAGES ASSISTANT */
    [data-testid="chat-message-assistant"] [data-testid="chat-message-content"] {
        background: rgba(20, 30, 40, 0.95) !important;
        color: white !important;
        border-radius: 20px 20px 20px 5px !important;
        padding: 12px 18px !important;
        max-width: 70% !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
    }
    
    /* ZONE DE SAISIE */
    .stChatInputContainer {
        background: rgba(20, 30, 40, 0.8) !important;
        border: 2px solid #3B82F6 !important;
        border-radius: 30px !important;
        padding: 5px 15px !important;
    }
    
    .stChatInputContainer input {
        color: white !important;
    }
    
    /* BADGES PREMIUM */
    .premium-badge {
        background: linear-gradient(45deg, #FFD700, #FFA500);
        color: #0A1929;
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: bold;
        margin-left: 10px;
        display: inline-block;
    }
    
    /* CARTES DE FONCTIONNALITÉS */
    .feature-card {
        background: rgba(30, 58, 138, 0.3);
        border: 1px solid #3B82F6;
        border-radius: 15px;
        padding: 20px;
        margin: 10px;
        text-align: center;
        backdrop-filter: blur(10px);
    }
    
    .feature-card h3 {
        color: white;
        margin-bottom: 10px;
    }
    
    .feature-card p {
        color: #90CAF9;
        font-size: 14px;
    }
    
    .price-tag {
        font-size: 28px;
        font-weight: bold;
        color: #FFD700;
        margin: 15px 0;
    }
    
    /* OFFRE LIMITÉE */
    .limited-offer {
        background: linear-gradient(45deg, #FF0000, #FF6B6B);
        color: white;
        padding: 5px 10px;
        border-radius: 20px;
        font-size: 12px;
        animation: pulse 2s infinite;
        text-align: center;
    }
    
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.7; }
        100% { opacity: 1; }
    }
    
    /* BOUTONS */
    .stButton button {
        background: linear-gradient(45deg, #1E3A8A, #3B82F6);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 8px 20px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(59, 130, 246, 0.4);
    }
    
    /* BARRES DE PROGRESSION */
    .stProgress > div > div {
        background: linear-gradient(90deg, #FFD700, #FFA500) !important;
    }
    
    /* BANDEAU D'OFFRE */
    .offer-banner {
        background: linear-gradient(45deg, #FFD700, #FFA500);
        color: #0A1929;
        padding: 10px;
        border-radius: 10px;
        text-align: center;
        font-weight: bold;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# FONCTIONS DE GESTION DES LIMITES
# ============================================
def check_subscription(user_email):
    """Vérifie le statut d'abonnement (simulé)"""
    # Dans la vraie vie, vérifier dans une base de données
    if user_email and "premium" in user_email.lower():
        return "premium"
    return "free"

def check_limits(user_email):
    """Vérifie et met à jour les limites du compte gratuit"""
    if "free_usage" not in st.session_state:
        st.session_state.free_usage = {
            "messages": 0,
            "images": 0,
            "voice": 0,
            "files": 0,
            "start_date": datetime.now().strftime("%Y-%m-%d"),
            "first_visit": datetime.now()
        }
    
    # Reset quotidien
    today = datetime.now().strftime("%Y-%m-%d")
    if st.session_state.free_usage["start_date"] != today:
        st.session_state.free_usage = {
            "messages": 0,
            "images": 0,
            "voice": 0,
            "files": 0,
            "start_date": today,
            "first_visit": st.session_state.free_usage["first_visit"]
        }
    
    return st.session_state.free_usage

def update_usage(feature):
    """Met à jour le compteur d'utilisation"""
    if feature in st.session_state.free_usage:
        st.session_state.free_usage[feature] += 1

def can_use_feature(feature, limit):
    """Vérifie si l'utilisateur peut utiliser une fonctionnalité"""
    if check_subscription(st.session_state.get("user_email", "")) == "premium":
        return True, "premium"
    
    usage = st.session_state.free_usage.get(feature, 0)
    remaining = max(0, limit - usage)
    
    if usage >= limit:
        return False, remaining
    return True, remaining

def save_conversation(messages):
    """Sauvegarde la conversation"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"conversation_{timestamp}.txt"
    with open(filename, "w", encoding="utf-8") as f:
        for msg in messages:
            f.write(f"{msg['role']}: {msg['content']}\n")
    return filename

def analyze_image(image_bytes, prompt):
    """Analyse une image avec Gemini"""
    try:
        img = Image.open(io.BytesIO(image_bytes))
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content([prompt, img])
        return response.text
    except Exception as e:
        return f"Erreur d'analyse: {e}"

# ============================================
# SIDEBAR - MENU LATÉRAL
# ============================================
with st.sidebar:
    # BANDEAU MARKETING (pour les gratuits)
    if check_subscription(st.session_state.get("user_email", "")) != "premium":
        st.markdown("""
        <div class='offer-banner'>
            🔥 OFFRE SPÉCIALE -30% 🔥<br>
            Plus que <span style='font-size: 20px;'>87</span> places !
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<h1 style='text-align: center;'>🚀 ANEYOND</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #90CAF9;'>Beyond AI</p>", unsafe_allow_html=True)
    
    st.divider()
    
    # MENU DE NAVIGATION
    menu = st.radio(
        "Navigation",
        ["💬 Chat", "🎨 Images", "💎 Premium", "📊 Stats"],
        label_visibility="collapsed",
        key="menu"
    )
    
    st.divider()
    
    # COMPTE UTILISATEUR
    st.markdown("### 👤 Mon compte")
    user_email = st.text_input("Email", placeholder="votre@email.com", key="user_email")
    
    # AFFICHAGE DES LIMITES POUR LES GRATUITS
    if check_subscription(user_email) != "premium" and user_email:
        usage = check_limits(user_email)
        days_used = (datetime.now() - usage["first_visit"]).days
        days_left = max(0, 7 - days_used)
        
        st.markdown("#### 🎁 Version Gratuite")
        
        # Barre de progression messages
        msg_progress = min(usage["messages"]/50, 1.0)
        st.progress(msg_progress, text=f"💬 Messages: {usage['messages']}/50")
        
        # Barre de progression images
        img_progress = min(usage["images"]/10, 1.0)
        st.progress(img_progress, text=f"🎨 Images: {usage['images']}/10")
        
        # Jours d'essai restants
        if days_left > 0:
            st.info(f"⏱️ {days_left} jours d'essai restants")
        else:
            st.warning("⚠️ Période d'essai terminée")
        
        # BOUTON PREMIUM BIEN VISIBLE
        st.markdown("---")
        if st.button("🚀 **DEVENIR PREMIUM**", use_container_width=True, type="primary"):
            st.session_state.menu = "💎 Premium"
            st.rerun()
    
    elif user_email:
        st.success("✨ Compte Premium Actif")
        st.balloons()

# ============================================
# PAGE CHAT AVEC LIMITES
# ============================================
if menu == "💬 Chat":
    st.markdown("<h1 style='text-align: center;'>💬 Assistant Intelligent</h1>", unsafe_allow_html=True)
    
    # VÉRIFICATION DES LIMITES
    if check_subscription(user_email) != "premium":
        usage = check_limits(user_email)
        days_used = (datetime.now() - usage["first_visit"]).days
        
        # Blocage si période d'essai terminée
        if days_used >= 7:
            st.warning("""
            ### ⏰ Période d'essai terminée !
            
            Merci d'avoir testé **ANEYOND** ! Pour continuer à profiter de l'assistant :
            
            - 🚀 **Messages illimités**
            - 🎨 **Génération d'images**
            - 🎤 **Commandes vocales**
            - 📎 **Upload de fichiers**
            
            🔥 **Seulement 9.99€/mois** (au lieu de 14.99€)
            """)
            if st.button("🔥 DÉCOUVRIR L'OFFRE PREMIUM", type="primary"):
                st.session_state.menu = "💎 Premium"
                st.rerun()
            st.stop()
        
        # Blocage si limite de messages atteinte
        if usage["messages"] >= 50:
            st.warning("""
            ### 📊 Limite quotidienne atteinte !
            
            Tu as utilisé tes 50 messages gratuits aujourd'hui.
            
            ✨ **Passe en Premium** pour des messages illimités :
            - Messages sans limite
            - Images illimitées
            - Support prioritaire
            """)
            if st.button("⚡ PASSER PREMIUM MAINTENANT", type="primary"):
                st.session_state.menu = "💎 Premium"
                st.rerun()
            st.stop()
        
        # Afficher les compteurs
        col1, col2, col3 = st.columns(3)
        with col1:
            st.info(f"💬 {usage['messages']}/50 messages")
        with col2:
            st.info(f"🎨 {usage['images']}/10 images")
        with col3:
            st.info(f"⏱️ {7-days_used} jours d'essai")
    
    # MESSAGE DE BIENVENUE
    if "messages" not in st.session_state:
        st.session_state.messages = []
        st.session_state.chat = genai.GenerativeModel('gemini-2.5-flash').start_chat(history=[])
        st.session_state.messages.append({
            "role": "assistant",
            "content": "👋 Bienvenue sur **ANEYOND** ! Je suis ton assistant. Pose-moi toutes tes questions !"
        })
    
    # AFFICHAGE DES MESSAGES
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # ZONE DE SAISIE
    prompt = st.chat_input("💭 Tapez votre message...")
    
    if prompt:
        # Met à jour le compteur
        if check_subscription(user_email) != "premium":
            update_usage("messages")
        
        # Message utilisateur
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Réponse assistant
        with st.chat_message("assistant"):
            with st.spinner("✨ Réflexion..."):
                try:
                    response = st.session_state.chat.send_message(prompt)
                    st.markdown(response.text)
                    st.session_state.messages.append({"role": "assistant", "content": response.text})
                    
                    # Message marketing après 10 messages
                    if check_subscription(user_email) != "premium" and usage["messages"] == 10:
                        st.success("""
                        ### 🌟 Tu aimes ANEYOND ?
                        
                        Passe en Premium maintenant et débloque :
                        - ✨ **Messages illimités**
                        - 🎨 **Images illimitées**
                        - 🎤 **Reconnaissance vocale**
                        
                        🔥 **-30% pour les 100 premiers !**
                        """)
                        
                except Exception as e:
                    st.error(f"❌ Erreur: {e}")
        
        st.rerun()
    
    # BOUTON NOUVELLE DISCUSSION
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        if st.button("🗑️ Nouvelle discussion", use_container_width=True):
            st.session_state.messages = [{
                "role": "assistant",
                "content": "👋 Bienvenue sur **ANEYOND** ! Je suis ton assistant. Pose-moi toutes tes questions !"
            }]
            st.session_state.chat = genai.GenerativeModel('gemini-2.5-flash').start_chat(history=[])
            st.rerun()

# ============================================
# PAGE IMAGES AVEC LIMITES
# ============================================
elif menu == "🎨 Images":
    st.markdown("<h1 style='text-align: center;'>🎨 Génération d'Images</h1>", unsafe_allow_html=True)
    
    # VÉRIFICATION DES LIMITES
    if check_subscription(user_email) != "premium":
        can_use, remaining = can_use_feature("images", 10)
        
        if not can_use:
            st.warning("""
            ### 🎨 Limite d'images atteinte !
            
            Tu as utilisé tes 10 images gratuites.
            
            ✨ **Passe en Premium** pour :
            - Images illimitées
            - Haute résolution
            - Styles multiples
            """)
            if st.button("🚀 PASSER PREMIUM", type="primary"):
                st.session_state.menu = "💎 Premium"
                st.rerun()
            st.stop()
        else:
            st.info(f"🎨 Images restantes aujourd'hui : {remaining}")
    
    # INTERFACE DE GÉNÉRATION D'IMAGES
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📝 Description")
        prompt = st.text_area("Décrivez l'image que vous voulez", height=150, key="image_prompt")
        style = st.selectbox("Style", ["Réaliste", "Artistique", "Manga", "Peinture"])
        
        if st.button("🚀 Générer l'image", type="primary"):
            if prompt:
                with st.spinner("🎨 Génération en cours..."):
                    time.sleep(2)  # Simulation
                    
                    # Met à jour le compteur
                    if check_subscription(user_email) != "premium":
                        update_usage("images")
                    
                    # Image simulée
                    st.session_state.generated_image = "https://via.placeholder.com/1024x1024.png?text=" + prompt.replace(" ", "+")
                    st.success("✅ Image générée !")
    
    with col2:
        if 'generated_image' in st.session_state:
            st.markdown("### 🖼️ Résultat")
            st.image(st.session_state.generated_image, use_column_width=True)
            
            # Message marketing pour les gratuits
            if check_subscription(user_email) != "premium" and st.session_state.free_usage["images"] == 5:
                st.info("""
                💡 **Tu aimes générer des images ?**
                
                Avec Premium, génère des images illimitées en haute résolution !
                """)

# ============================================
# PAGE PREMIUM - MARKETING
# ============================================
elif menu == "💎 Premium":
    st.markdown("<h1 style='text-align: center;'>✨ Passez à la vitesse supérieure</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #90CAF9;'>Débloquez tout le potentiel d'ANEYOND</p>", unsafe_allow_html=True)
    
    # COMPTEUR DE PLACES (fausse urgence)
    st.markdown("""
    <div style='text-align: center; margin-bottom: 30px;'>
        <span class='limited-offer'>🔥 PLUS QUE 87 PLACES À -30% 🔥</span>
    </div>
    """, unsafe_allow_html=True)
    
    # COMPARAISON DES OFFRES
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class='feature-card'>
            <h3>🆓 Gratuit</h3>
            <div class='price-tag'>0€</div>
            <p>✓ 50 messages/jour</p>
            <p>✓ 10 images/jour</p>
            <p>✓ Chat basique</p>
            <p style='color: #FF6B6B;'>✗ Pas de vocal</p>
            <p style='color: #FF6B6B;'>✗ Pas de fichiers</p>
            <p style='color: #FF6B6B;'>✗ Support standard</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class='feature-card' style='border: 2px solid #FFD700; transform: scale(1.05);'>
            <h3>⭐ Premium</h3>
            <div class='price-tag'>9.99€<span style='font-size: 14px;'>/mois</span></div>
            <p>✓ Messages illimités</p>
            <p>✓ Images illimitées</p>
            <p>✓ Commandes vocales</p>
            <p>✓ Upload de fichiers</p>
            <p>✓ Analyse d'images</p>
            <p>✓ Support prioritaire</p>
            <p>✓ Export PDF</p>
            <p style='color: #FFD700;'>🔥 -30% aujourd'hui</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🚀 **CHOISIR PREMIUM**", key="premium_btn", use_container_width=True, type="primary"):
            st.balloons()
            st.success("""
            ✅ **Redirection vers le paiement sécurisé...**
            
            (Simulation - Dans la vraie vie, intégration Stripe)
            """)
    
    with col3:
        st.markdown("""
        <div class='feature-card'>
            <h3>👑 Annuel</h3>
            <div class='price-tag'>99.99€<span style='font-size: 14px;'>/an</span></div>
            <p>✓ 2 mois offerts</p>
            <p>✓ Tout le Premium</p>
            <p>✓ API dédiée</p>
            <p>✓ Formation incluse</p>
            <p>✓ Stockage cloud</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("👑 **CHOISIR ANNUEL**", key="annual_btn", use_container_width=True):
            st.balloons()
            st.success("✅ Redirection vers le paiement sécurisé...")
    
    # TÉMOIGNAGES
    st.markdown("---")
    st.markdown("<h2 style='text-align: center;'>💬 Ils ont déjà sauté le pas</h2>", unsafe_allow_html=True)
    
    col_t1, col_t2, col_t3 = st.columns(3)
    with col_t1:
        st.markdown("""
        <div style='background: rgba(255,255,255,0.1); padding: 20px; border-radius: 10px;'>
            ⭐⭐⭐⭐⭐<br>
            "ANEYOND a révolutionné ma façon de travailler. La génération d'images est incroyable !"
            <br><br>- Marie, Designer
        </div>
        """, unsafe_allow_html=True)
    
    with col_t2:
        st.markdown("""
        <div style='background: rgba(255,255,255,0.1); padding: 20px; border-radius: 10px;'>
            ⭐⭐⭐⭐⭐<br>
            "Pour 9.99€/mois, c'est le meilleur rapport qualité-prix du marché. Je l'utilise tous les jours !"
            <br><br>- Thomas, Chef de projet
        </div>
        """, unsafe_allow_html=True)
    
    with col_t3:
        st.markdown("""
        <div style='background: rgba(255,255,255,0.1); padding: 20px; border-radius: 10px;'>
            ⭐⭐⭐⭐⭐<br>
            "L'analyse d'images est bluffante. J'ai pris l'abonnement annuel sans hésiter."
            <br><br>- Sophie, Entrepreneur
        </div>
        """, unsafe_allow_html=True)
    
    # FOIRE AUX QUESTIONS
    st.markdown("---")
    st.markdown("<h2 style='text-align: center;'>❓ Questions fréquentes</h2>", unsafe_allow_html=True)
    
    with st.expander("💰 Puis-je annuler à tout moment ?"):
        st.write("Oui ! Vous pouvez annuler votre abonnement quand vous voulez. Sans engagement.")
    
    with st.expander("🔒 Comment fonctionne le paiement ?"):
        st.write("Paiement sécurisé par Stripe. Vos informations bancaires ne sont jamais stockées.")
    
    with st.expander("🎁 Que se passe-t-il après l'essai gratuit ?"):
        st.write("Après 7 jours, vous pouvez continuer avec la version gratuite limitée ou passer Premium.")

# ============================================
# PAGE STATISTIQUES
# ============================================
elif menu == "📊 Stats":
    st.markdown("<h1 style='text-align: center;'>📊 Vos statistiques</h1>", unsafe_allow_html=True)
    
    usage = st.session_state.get("free_usage", {"messages": 0, "images": 0})
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Messages", usage["messages"], "+5 aujourd'hui" if usage["messages"] > 0 else "0")
    
    with col2:
        st.metric("Images", usage["images"], "0")
    
    with col3:
        days_used = (datetime.now() - usage.get("first_visit", datetime.now())).days
        st.metric("Jours d'utilisation", days_used, "+1")
    
    with col4:
        st.metric("Mots économisés", usage["messages"] * 50, "👍")
    
    # GRAPHIQUE SIMULÉ
    st.markdown("### 📈 Activité")
    chart_data = {"Lun": 5, "Mar": 8, "Mer": 12, "Jeu": 7, "Ven": 15, "Sam": 10, "Dim": 6}
    st.bar_chart(chart_data)
    
    # MESSAGE MARKETING POUR LES GRATUITS
    if check_subscription(user_email) != "premium":
        st.info("""
        💡 **Passez en Premium** pour voir :
        - Statistiques détaillées
        - Historique complet
        - Graphiques avancés
        - Export des données
        """)

# ============================================
# FOOTER
# ============================================
st.divider()
col1, col2, col3 = st.columns(3)
with col2:
    st.markdown("<p style='text-align: center; color: #90CAF9;'>🚀 ANEYOND - Beyond AI | © 2026</p>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #90CAF9; font-size: 12px;'>7 jours d'essai • Sans engagement • Paiement sécurisé</p>", unsafe_allow_html=True)