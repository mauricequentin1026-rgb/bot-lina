import os
import logging
import anthropic
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
ADMIN_ID = int(os.environ["ADMIN_ID"])  # Ton ID Telegram personnel

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

# Stockage conversations et mode
conversations = {}
mode_humain = set()  # IDs des clients gérés manuellement par l'admin

async def notifier_admin(context, user_id, username, message, reponse_bot=None):
    """Envoie une notification à l'admin avec le message du client"""
    username_str = f"@{username}" if username else f"ID:{user_id}"
    texte = f"💬 *Nouveau message*\nClient: {username_str} (`{user_id}`)\n\n*Client:* {message}"
    if reponse_bot:
        texte += f"\n\n*Bot:* {reponse_bot}"
    texte += f"\n\n➡️ Prendre la main: `/humain {user_id}`"
    await context.bot.send_message(chat_id=ADMIN_ID, text=texte, parse_mode="Markdown")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username
    user_message = update.message.text

    # Ignorer les messages de l'admin au bot
    if user_id == ADMIN_ID:
        return

    # Mode humain — notifier l'admin sans répondre automatiquement
    if user_id in mode_humain:
        await notifier_admin(context, user_id, username, user_message)
        return

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

        # Envoyer infos paiement si nécessaire
        msg_lower = user_message.lower()
        for keyword, info in PAIEMENTS.items():
            if keyword in msg_lower:
                await update.message.reply_text(info)
                break

        # Notifier l'admin
        await notifier_admin(context, user_id, username, user_message, bot_reply)

    except Exception as e:
        logger.error(f"Erreur API: {e}")
        await update.message.reply_text("Je reviens dans 2 min 😊")

async def cmd_humain(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin prend la main sur une conversation"""
    if update.effective_user.id != ADMIN_ID:
        return
    if not context.args:
        await update.message.reply_text("Usage: /humain [user_id]")
        return
    client_id = int(context.args[0])
    mode_humain.add(client_id)
    await update.message.reply_text(f"✅ Mode humain activé pour `{client_id}`\nTu gères cette conv manuellement.\nPour repasser en auto: `/auto {client_id}`", parse_mode="Markdown")

async def cmd_auto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Repasser en mode automatique"""
    if update.effective_user.id != ADMIN_ID:
        return
    if not context.args:
        await update.message.reply_text("Usage: /auto [user_id]")
        return
    client_id = int(context.args[0])
    mode_humain.discard(client_id)
    await update.message.reply_text(f"✅ Mode auto réactivé pour `{client_id}`", parse_mode="Markdown")

async def cmd_repondre(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin envoie un message à un client via le bot"""
    if update.effective_user.id != ADMIN_ID:
        return
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /rep [user_id] [message]")
        return
    client_id = int(context.args[0])
    message = " ".join(context.args[1:])
    await context.bot.send_message(chat_id=client_id, text=message)
    await update.message.reply_text(f"✅ Message envoyé à `{client_id}`", parse_mode="Markdown")

async def cmd_statut(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Voir les conversations actives"""
    if update.effective_user.id != ADMIN_ID:
        return
    total = len(conversations)
    humains = len(mode_humain)
    await update.message.reply_text(f"📊 *Statut du bot*\n\nConversations actives: {total}\nMode humain: {humains}\nMode auto: {total - humains}", parse_mode="Markdown")

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CommandHandler("humain", cmd_humain))
    app.add_handler(CommandHandler("auto", cmd_auto))
    app.add_handler(CommandHandler("rep", cmd_repondre))
    app.add_handler(CommandHandler("statut", cmd_statut))
    logger.info("Bot démarré !")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
