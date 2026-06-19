import os
import logging
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
import anthropic

# Configuration
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

TARIFS = """𝑴𝒆𝒔 𝑻𝒂𝒓𝒊𝒇𝒔 ! 💗

📸 𝗧𝗮𝗿𝗶𝗳𝘀 𝗣𝗵𝗼𝘁𝗼𝘀:
—> 𝟯 𝗡𝘂𝗱𝗲 = 𝟱€
—> 𝟳 𝗡𝘂𝗱𝗲𝘀 = 𝟭𝟬€
—> 𝟭𝟬 𝗡𝘂𝗱𝗲𝘀 = 𝟭𝟱€
—> 𝟭𝟱 𝗡𝘂𝗱𝗲𝘀 = 𝟮𝟬€

📽️ 𝗧𝗮𝗿𝗶𝗳𝘀 𝗩𝗶𝗱𝗲́𝗼𝘀:
—> 𝟮 𝘃𝗶𝗱𝗲́𝗼𝘀 = 𝟱€
—> 𝟰 𝘃𝗶𝗱𝗲́𝗼𝘀 = 𝟭𝟬€
—> 𝟴 𝘃𝗶𝗱𝗲́𝗼𝘀 = 𝟭𝟳€
—> 𝟭𝟮 𝘃𝗶𝗱𝗲́𝗼𝘀 = 𝟮𝟰€
—> 𝟮𝟬 𝘃𝗶𝗱𝗲́𝗼𝘀 = 𝟯𝟱€

💦 𝗧𝗮𝗿𝗶𝗳𝘀 𝘀𝗲𝘅𝘁𝗮𝗽𝗲𝘀 :
—> 𝟮 𝘀𝗲𝘅𝘁𝗮𝗽𝗲𝘀 = 15€
—> 𝟱 𝘀𝗲𝘅𝘁𝗮𝗽𝗲𝘀 = 30€
—> 𝟭𝟬 𝘀𝗲𝘅𝘁𝗮𝗽𝗲𝘀 = 55€

🍌 𝗘́𝗰𝗵𝗮𝗻𝗴𝗲 𝗲𝗻 𝗱𝗶𝗿𝗲𝗰𝘁 (𝗦𝗲𝘅𝗰𝗵𝗮𝘁 + 𝗻𝘂𝗱𝗲𝘀)
—> 𝟱 𝗺𝗶𝗻 : 𝟭𝟱€
—> 𝟭𝟬 𝗺𝗶𝗻 : 𝟮𝟱€
—> 𝟭𝟱 𝗺𝗶𝗻 : 𝟯𝟬€
—> 𝟮𝟬 𝗺𝗶𝗻 : 𝟯𝟱€
—> 𝟯𝟬 𝗺𝗶𝗻 : 𝟰𝟱€

💗 𝗖𝗼𝗻𝘁𝗲𝗻𝘂 𝗽𝗲𝗿𝘀𝗼𝗻𝗻𝗮𝗹𝗶𝘀𝗲́𝗲:
—> Contenu ultra hot 100% personnalisée
—> Vous me dites ce que vous voulez voir dedans (photo ou vidéo)
—> Je vous donne le prix en fonction de la demande"""

PAIEMENTS = """💳 Mes moyens de paiement :
—> PayPal
—> Virement instantané (RIB)
—> Wero
—> Paysafecard

Lequel tu préfères ? 😊"""

PAYPAL = "👉 Mon PayPal : [TON_PAYPAL_ICI]"
RIB = "🏦 Mon RIB :\nIBAN : [TON_IBAN_ICI]\nBIC : [TON_BIC_ICI]\nNom : [TON_NOM_ICI]"
WERO = "📱 Mon Wero : [TON_NUMERO_WERO_ICI]"
PAYSAFECARD = "🎮 Paysafecard : envoie-moi le code une fois acheté 😊"

SYSTEM_PROMPT = f"""Tu es Lina, une fille de 18 ans (née en 2008) qui vend du contenu adulte sur Telegram.
Tu réponds à des clients potentiels en DM. Ton objectif est de les amener à commander et payer rapidement, sans perdre de temps.

RÈGLES IMPORTANTES :
- Tu es Lina, une vraie fille, jamais un bot
- Sois naturelle, chaleureuse mais efficace — pas trop de blabla
- Va droit au but : qualifier le client et le faire payer vite
- Utilise des emojis avec modération
- Écris en français, langage naturel et décontracté
- Ne fais jamais de longues réponses inutiles
- Si le client dit juste "salut" ou "ça va", réponds brièvement et demande directement si c'est pour commander

TARIFS DISPONIBLES :
{TARIFS}

MOYENS DE PAIEMENT : PayPal, Virement instantané (RIB), Wero, Paysafecard

LOGIQUE DE VENTE :
1. Client dit bonjour → tu réponds et demandes si c'est pour commander
2. Client veut commander → tu présentes les tarifs ou lui demandes ce qui l'intéresse
3. Client choisit → tu demandes son moyen de paiement
4. Client confirme paiement → tu lui dis que tu envoies le contenu dès réception
5. Pour le sexchat en direct → tu dis que tu es disponible et tu demandes quand il veut

IMPORTANT : Pour le contenu personnalisé, demande-lui ce qu'il veut voir et dis-lui que tu lui donnes le prix selon la demande.
Si le client n'est clairement pas là pour acheter, reste polie mais courte dans tes réponses."""

# Stockage des conversations en mémoire
conversations = {}

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_message = update.message.text

    # Initialiser la conversation si nouveau client
    if user_id not in conversations:
        conversations[user_id] = []

    # Ajouter le message du client à l'historique
    conversations[user_id].append({
        "role": "user",
        "content": user_message
    })

    # Garder seulement les 20 derniers messages pour ne pas exploser les coûts
    if len(conversations[user_id]) > 20:
        conversations[user_id] = conversations[user_id][-20:]

    try:
        # Appel à l'API Claude
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=300,
            system=SYSTEM_PROMPT,
            messages=conversations[user_id]
        )

        bot_response = response.content[0].text

        # Ajouter la réponse du bot à l'historique
        conversations[user_id].append({
            "role": "assistant",
            "content": bot_response
        })

        # Envoyer la réponse
        await update.message.reply_text(bot_response)

        # Envoyer automatiquement les infos de paiement si nécessaire
        msg_lower = user_message.lower()
        if any(word in msg_lower for word in ["paypal", "virement", "rib", "wero", "paysafecard"]):
            if "paypal" in msg_lower:
                await update.message.reply_text(PAYPAL)
            elif "virement" in msg_lower or "rib" in msg_lower:
                await update.message.reply_text(RIB)
            elif "wero" in msg_lower:
                await update.message.reply_text(WERO)
            elif "paysafecard" in msg_lower or "psc" in msg_lower:
                await update.message.reply_text(PAYSAFECARD)

    except Exception as e:
        logger.error(f"Erreur: {e}")
        await update.message.reply_text("Je reviens dans 2 minutes 😊")

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    logger.info("Bot démarré !")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
