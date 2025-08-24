from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import random
import time

# -------------------- Character List --------------------
characters = [
    {"name":"Makima","rarity":"Epic","anime":"Chainsaw Man","image":"https://i.postimg.cc/tJvdgR4z/images-4.jpg"},
    {"name":"Naruto Uzumaki ( Adult )","rarity":"Legendary","anime":"Naruto Shippuden","image":"https://i.postimg.cc/G21X0p48/images-3.jpg"},
    {"name":"Naruto Uzumaki ( Kid )","rarity":"Uncommon","anime":"Naruto","image":"https://i.postimg.cc/Fzq4HRcC/images.jpg"},
    {"name":"Ayanokoji Kiyotaka","rarity":"Epic","anime":"Classroom of the Elite","image":"https://i.postimg.cc/76Rzw3BF/images-1.jpg"},
    {"name":"Obito Uchiha ( Mask )","rarity":"Epic","anime":"Naruto Shippuden","image":"https://i.postimg.cc/SNQKDTmD/nwf0k-512.jpg"},
    {"name":"Goku","rarity":"Epic","anime":"Dragon Ball","image":"https://i.postimg.cc/V6jv558N/images-2.jpg"},
    {"name":"Levi Ackerman","rarity":"Epic","anime":"Attack on Titan","image":"https://i.postimg.cc/KY2dxYJf/Levi-Ackermann-Anime-character-image.png"},
    {"name":"Monkey D. Luffy","rarity":"Legendary","anime":"One Piece","image":"https://i.postimg.cc/q7jqKqDB/images-3.jpg"},
    {"name":"Izuku Midoriya","rarity":"Epic","anime":"My Hero Academia","image":"https://i.postimg.cc/BQy4dytg/DEKU.png"},
    {"name":"Saitama","rarity":"Epic","anime":"One Punch Man","image":"https://i.postimg.cc/VNNyvWS6/saitama-one-punch-man-anime-gloves-wallpaper-1-p276-poster-smoky-original-imag7qxqa2bs5gyb.jpg"},
    {"name":"Tanjiro Kamado","rarity":"Uncommon","anime":"Demon Slayer","image":"https://i.postimg.cc/5tt0Jvb5/IMG-20250818-024223-289.jpg"},
    {"name":"Gojo Satoru","rarity":"Epic","anime":"Jujutsu Kaisen","image":"https://i.postimg.cc/FzNwtbQN/images-4.jpg"},
    {"name":"Zenitsu Agatsuma","rarity":"Uncommon","anime":"Demon Slayer","image":"https://i.postimg.cc/FRy2GB5p/images-6.jpg"},
    {"name":"Nezuko Kamado","rarity":"Uncommon","anime":"Demon Slayer","image":"https://i.postimg.cc/Xvc8PSqr/images-7.jpg"},
    {"name":"Hinata Hyuga","rarity":"Uncommon","anime":"Naruto Shippuden","image":"https://i.postimg.cc/QCWKR1mf/Hinata-Part-II.png"},
    {"name":"Krillin","rarity":"Uncommon","anime":"Dragon Ball","image":"https://i.postimg.cc/d3y3GWVy/images.png"},
    {"name":"Muzan Kibutsuji","rarity":"Epic","anime":"Demon Slayer","image":"https://i.postimg.cc/D0w316dc/images.jpg"},
    {"name":"Madara Uchiha","rarity":"Legendary","anime":"Naruto Shippuden","image":"https://i.postimg.cc/htg6mpDQ/images-1.jpg"}
]

# -------------------- In-Memory Storage --------------------
# For production, replace with a database (SQLite / Mongo / Redis)
chat_msg_count = {}
current_spawn = {}
recent_spawns = {}
user_collections = {}
user_balances = {}

SPAWN_THRESHOLD = 20  # spawn every 20 messages
LAST_N = 15

# -------------------- Start Command --------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("➕ ADD ME TO YOUR GROUP", url="https://t.me/DEVILxGRABBERBot?startgroup=true")]
    ]
    await update.message.reply_text(
        "🎯 *Welcome!*\n\nThis bot will *track messages*, *rank members*, and *reward top performers*! 🏆\n\n💡 *Tip:* Add me to your group to start tracking and competing for prizes!",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# -------------------- Message Tracking & Spawn --------------------
async def track_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    # increment message count
    chat_msg_count[chat_id] = chat_msg_count.get(chat_id, 0) + 1

    # check spawn
    if chat_id not in current_spawn and chat_msg_count[chat_id] >= SPAWN_THRESHOLD:
        chat_msg_count[chat_id] = 0  # reset

        # recent history
        recentHistory = recent_spawns.get(chat_id, [])
        recentNames = [c["name"] for c in recentHistory[-LAST_N:]]

        possibleCharacters = [c for c in characters if c["name"] not in recentNames]
        if not possibleCharacters:
            possibleCharacters = characters

        character = random.choice(possibleCharacters)
        current_spawn[chat_id] = {"character": character, "time": time.time()}

        recentHistory.append(character)
        recent_spawns[chat_id] = recentHistory

        await context.bot.send_photo(
            chat_id=chat_id,
            photo=character["image"],
            caption=f"✨A 🌟{character['rarity']} Character Appears!\n🔍 Use /guess <name> to claim!"
        )

# -------------------- Guess Command --------------------
async def guess(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    username = update.effective_user.full_name

    if chat_id not in current_spawn:
        await update.message.reply_text("❌ No character is currently spawned. Wait for the next one!")
        return

    args = " ".join(context.args).lower() if context.args else ""
    if not args:
        await update.message.reply_text("❌ Please guess the character name!\nUsage: /guess <name>")
        return

    spawned = current_spawn[chat_id]["character"]
    full_name = spawned["name"].lower()
    first_name = full_name.split()[0]
    last_name = full_name.split()[-1] if len(full_name.split()) > 1 else ""

    if args == full_name or args == first_name or (last_name and args == last_name):
        # Time taken
        diff = time.time() - current_spawn[chat_id]["time"]
        minutes = int(diff // 60)
        seconds = int(diff % 60)
        timeTaken = f"{minutes}m {seconds}s"

        # Add to collection
        collection = user_collections.get(user_id, [])
        collection.append({
            "name": spawned["name"],
            "rarity": spawned["rarity"],
            "anime": spawned["anime"],
            "time": timeTaken
        })
        user_collections[user_id] = collection

        # Coins
        rarity = spawned["rarity"].lower()
        coinsEarned = 10 if rarity == "legendary" else 5 if rarity == "epic" else 3 if rarity == "uncommon" else 1
        user_balances[user_id] = user_balances.get(user_id, 0) + coinsEarned

        # Clear spawn
        del current_spawn[chat_id]

        # Send messages
        await update.message.reply_text(f"🎉 Congratulations! You earned {coinsEarned} coins!\n💰 Your new balance is {user_balances[user_id]} coins.")
        await update.message.reply_text(
            f"🌟 [{username}](tg://user?id={user_id}) captured a new character! 🎊\n\n"
            f"📛 NAME: {spawned['name']}\n"
            f"🌈 ANIME: {spawned['anime']}\n"
            f"✨ RARITY: {spawned['rarity']}\n"
            f"⏱ TIME TAKEN: {timeTaken}",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text("❌ Wrong guess! Try again before someone else claims it.")

# -------------------- Run Bot --------------------
app = ApplicationBuilder().token("8283550260:AAGRRC1JS7qhVx2W-acy92mYxa8Rx70brh0").build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("guess", guess))
app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), track_messages))

app.run_polling()  # use run_polling() for testing, replace with webhook for production