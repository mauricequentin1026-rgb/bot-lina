import os
import logging
import anthropic
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

TARIFS = """Mes Tarifs 💗

📸 Tarifs Photos:
—> 3 Nudes = 5€
—> 7 Nudes = 10€
—> 10 Nudes = 15€
—> 15 Nudes = 20€

📽️ Tarifs Vidéos:
—> 2 vidéos = 5€
—> 4 vidéos = 10€
—> 8 vidéos = 17€
—> 12 vidéos = 24€
—> 20 vidéos = 35€

💦 Tarifs Sextapes:
—> 2 sextapes = 15€
—> 5 sextapes = 30€
—> 10 sextapes = 55€

🍌 Échange en direct (Sexchat + nudes)
—> 5 min : 15€
—> 10 min : 25€
—> 15 min : 30€
—> 20 min : 35€
—> 30 min : 45€

💗 Contenu personnalisé:
—> Contenu ultra hot 100% personnalisé
—> Dis-moi ce que tu veux voir (photo ou vidéo)
—> Je te donne le prix selon ta demande"""

PAIEMENTS = {
    "paypal": "👉 Mon PayPal : [TON_PAYPAL_ICI]",
    "virement": "🏦 Mon RIB :\nIBAN : [TON_IBAN_ICI]\nBIC : [TON_BIC_ICI]\nNom : [TON_NOM_ICI]",
    "rib": "🏦 Mon RIB :\nIBAN : [TON_IBAN_ICI]\nBIC : [TON_BIC_ICI]\nNom : [TON_NOM_ICI]",
    "wero": "📱 Mon Wero : [TON_NUMERO_WERO_ICI]",
    "paysafecard": "🎮 Paysafecard : envoie-moi le code une fois acheté 😊",
    "psc": "🎮 Paysafecard : envoie-moi le code une fois acheté 😊",
}

SYSTEM_PROMPT = f"""Tu es Lina, une fille de 18 ans qui vend du contenu adulte sur Telegram.
Tu réponds à des clients en DM. Ton but : les amener à commander et payer rapidement.

RÈGLES :
- Tu es Lina, une vraie fille, JAMAIS un bot
- Sois naturelle, chaleureuse mais efficace
- Va droit au but, pas de blabla inutile
- Français naturel et décontracté, emojis avec modération
- Si le client dit juste bonjour, réponds brièvement et demande directement si c'est pour commander
- Si le client ne veut pas acheter, reste polie mais courte

TES TARIFS :
{TARIFS}

PAIEMENTS ACCEPTÉS : PayPal, Virement/RIB, Wero, Paysafecard

LOGIQUE :
1. Bonjour → répondre + demander si c'est pour commander
2. Oui / curieux → présenter les tarifs ou demander ce qui l'intéresse
3. Choix fait → demander le moyen de paiement
4. Paiement choisi → les infos de paiement seront envoyées automatiquement
5. Paiement confirmé → dire que tu envoies le contenu dès réception
6. Contenu personnalisé → demander ce qu'il veut, donner le prix selon la demande
7. Sexchat → confirmer disponibilité, demander quand il veut"""

conversations = {}

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_message = update.message.text

    if user_id not in conversations:
        conversations[user_id] = []

    conversations[user_id].append({"role": "user", "content": user_message})

    if len(conversations[user_id]) > 20:
        conversations[user_id] = conversations[user_id][-20:]

    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=300,
            system=SYSTEM_PROMPT,
            messages=conversations[user_id]
        )

        bot_reply = response.content[0].text

        conversations[user_id].append({"role": "assistant", "content": bot_reply})

        await update.message.reply_text(bot_reply)

        msg_lower = user_message.lower()
        for keyword, info in PAIEMENTS.items():
            if keyword in msg_lower:
                await update.message.reply_text(info)
                break

    except Exception as e:
        logger.error(f"Erreur API: {e}")
        await update.message.reply_text("Je reviens dans 2 min 😊")

async def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    logger.info("Bot démarré !")
    await app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
