import logging
import json
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, ConversationHandler
)

# ==================== SAZLAMALAR ====================
BOT_TOKEN = "8883106625:AAFHJTKdIkNiBHF58D6-JWmeMoOhDDEtX_M"  # @BotFather-dan al
ADMIN_IDS = [7331708536]           # Seniñ Telegram ID-iñ
DATA_FILE = "data.json"
# ConversationHandler states
WAITING_SPONSOR_NAME, WAITING_SPONSOR_USERNAME = range(2)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


# ==================== MAGLUMAT DOLANDYRYŞY ====================
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "vpn_codes": [],
        "used_codes": {},
        "users": {},
        "sponsors": []
    }


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_sponsors():
    data = load_data()
    return data.get("sponsors", [])


# ==================== KÖMEKÇI FUNKSIÝALAR ====================
async def check_subscriptions(user_id: int, bot) -> list:
    sponsors = get_sponsors()
    not_subscribed = []
    for channel in sponsors:
        try:
            member = await bot.get_chat_member(channel["id"], user_id)
            if member.status in ["left", "kicked", "banned"]:
                not_subscribed.append(channel)
        except Exception:
            not_subscribed.append(channel)
    return not_subscribed


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


# ==================== ULANYJY BUÝRUKLARY ====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    data = load_data()

    user_id = str(user.id)
    if user_id not in data["users"]:
        data["users"][user_id] = {
            "name": user.full_name,
            "username": user.username or "",
            "vpn_count": 0
        }
        save_data(data)

    sponsors = get_sponsors()
    if not sponsors:
        await show_main_menu(update, context)
        return

    not_subscribed = await check_subscriptions(user.id, context.bot)
    if not_subscribed:
        keyboard = []
        for ch in not_subscribed:
            keyboard.append([InlineKeyboardButton(
                f"📢 {ch['name']} - Agza bol",
                url=f"https://t.me/{ch['id'].lstrip('@')}"
            )])
        keyboard.append([InlineKeyboardButton("✅ Agza boldum, barla!", callback_data="check_sub")])
        await update.message.reply_text(
            "🔒 *VPN kod almak üçin aşakdaky kanallara agza bol:*\n\n"
            "Agza bolandan soň '✅ Agza boldum' düwmesine bas!",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        return

    await show_main_menu(update, context)


async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🔑 VPN Kod Al", callback_data="get_vpn")],
        [InlineKeyboardButton("📊 Meniñ maglumatlarym", callback_data="my_info")],
    ]
    text = (
        "🌐 *VPN BOT-a hoş geldiñiz!*\n\n"
        "Bu bot arkaly mugt VPN kodlaryny alyp bilersiñiz.\n\n"
        "Aşakdaky düwmelerden birini saý:"
    )
    if update.callback_query:
        await update.callback_query.edit_message_text(
            text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown"
        )


# ==================== BUTTON HANDLER ====================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    data = load_data()

    # ── Abunalyk barla ──
    if query.data == "check_sub":
        not_subscribed = await check_subscriptions(user.id, context.bot)
        if not_subscribed:
            names = "\n".join([f"• {ch['name']}" for ch in not_subscribed])
            await query.answer(f"❌ Heniz agza bolmadyk:\n{names}", show_alert=True)
        else:
            await show_main_menu(update, context)

    # ── VPN kod al ──
    elif query.data == "get_vpn":
        not_subscribed = await check_subscriptions(user.id, context.bot)
        if not_subscribed:
            await query.answer("❌ Ilki kanallara agza bol!", show_alert=True)
            return
        user_id = str(user.id)
        used = data["used_codes"].get(user_id, [])
        available = [c for c in data["vpn_codes"] if c not in used]
        if not available:
            await query.edit_message_text(
                "😔 *Häzirki wagtda VPN kod ýok.*\n\nBiraz soň gaýdyp gel.",
                parse_mode="Markdown"
            )
            return
        code = available[0]
        data["used_codes"].setdefault(user_id, []).append(code)
        data["users"][user_id]["vpn_count"] = data["users"][user_id].get("vpn_count", 0) + 1
        save_data(data)
        keyboard = [[InlineKeyboardButton("🏠 Baş menýu", callback_data="main_menu")]]
        await query.edit_message_text(
            f"✅ *Seniñ VPN Kodun:*\n\n```\n{code}\n```\n\n"
            f"📋 Kody kopyala we VPN programmañda ullan!\n⚠️ Bu kod diñe bir gezek berilýär.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

    # ── Maglumat ──
    elif query.data == "my_info":
        user_id = str(user.id)
        vpn_count = data["users"].get(user_id, {}).get("vpn_count", 0)
        keyboard = [[InlineKeyboardButton("🏠 Baş menýu", callback_data="main_menu")]]
        await query.edit_message_text(
            f"👤 *Seniñ maglumatlaryn:*\n\n"
            f"🆔 ID: `{user.id}`\n👤 Ady: {user.full_name}\n🔑 Alnan VPN kod: {vpn_count} sany",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

    # ── Baş menýu ──
    elif query.data == "main_menu":
        await show_main_menu(update, context)

    # ════════════════════════════════════════
    #           ADMIN PANEL DÜWMELERI
    # ════════════════════════════════════════

    elif query.data == "admin_panel":
        await show_admin_panel(update, context)

    # ── Sponsor sanawyny gör ──
    elif query.data == "admin_sponsors":
        sponsors = get_sponsors()
        if not sponsors:
            keyboard = [
                [InlineKeyboardButton("➕ Sponsor goş", callback_data="admin_add_sponsor")],
                [InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_panel")],
            ]
            await query.edit_message_text(
                "📭 *Heniz sponsor kanal ýok.*\n\nIlkinji sponsory goş!",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
            return

        text = "📢 *Sponsor Kanallar:*\n\n"
        keyboard = []
        for i, sp in enumerate(sponsors):
            text += f"{i+1}. {sp['name']} — `{sp['id']}`\n"
            keyboard.append([InlineKeyboardButton(
                f"🗑 {sp['name']} sil", callback_data=f"del_sponsor_{i}"
            )])
        keyboard.append([InlineKeyboardButton("➕ Täze sponsor goş", callback_data="admin_add_sponsor")])
        keyboard.append([InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_panel")])
        await query.edit_message_text(
            text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown"
        )

    # ── Sponsor sil ──
    elif query.data.startswith("del_sponsor_"):
        idx = int(query.data.split("_")[-1])
        sponsors = get_sponsors()
        if idx < len(sponsors):
            removed = sponsors.pop(idx)
            data["sponsors"] = sponsors
            save_data(data)
            await query.answer(f"✅ '{removed['name']}' aýryldy!", show_alert=True)
        sponsors = get_sponsors()
        if not sponsors:
            keyboard = [
                [InlineKeyboardButton("➕ Sponsor goş", callback_data="admin_add_sponsor")],
                [InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_panel")],
            ]
            await query.edit_message_text(
                "📭 *Sponsor kanal ýok.*",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
        else:
            text = "📢 *Sponsor Kanallar:*\n\n"
            keyboard = []
            for i, sp in enumerate(sponsors):
                text += f"{i+1}. {sp['name']} — `{sp['id']}`\n"
                keyboard.append([InlineKeyboardButton(
                    f"🗑 {sp['name']} sil", callback_data=f"del_sponsor_{i}"
                )])
            keyboard.append([InlineKeyboardButton("➕ Täze sponsor goş", callback_data="admin_add_sponsor")])
            keyboard.append([InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_panel")])
            await query.edit_message_text(
                text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown"
            )

    # ── VPN Kod goş (düwme bilen) ── ✅ DÜZELTILDI
    elif query.data == "admin_add_code_msg":
        if not is_admin(user.id):
            await query.answer("❌ Siz admin däl!", show_alert=True)
            return
        context.user_data["waiting_vpn_code"] = True
        keyboard = [[InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_panel")]]
        await query.edit_message_text(
            "➕ *VPN Kod Goşmak*\n\n"
            "Kodlary ýaz (her setirde bir kod ýa-da boşluk bilen):\n\n"
            "Mysal:\n`KOD1\nKOD2\nKOD3`",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

    # ── Admin statistika ──
    elif query.data == "admin_stats":
        sponsors = get_sponsors()
        total_codes = len(data["vpn_codes"])
        used_count = sum(len(v) for v in data["used_codes"].values())
        keyboard = [[InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_panel")]]
        await query.edit_message_text(
            f"📊 *Bot Statistikasy:*\n\n"
            f"👥 Ulanyjylar: {len(data['users'])}\n"
            f"📢 Sponsor kanallar: {len(sponsors)}\n"
            f"🔑 Umumy kod: {total_codes}\n"
            f"✅ Ulanylan: {used_count}\n"
            f"🟢 Galdy: {total_codes - used_count}",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )


# ==================== VPN KOD GIRIZME HANDLER ==================== ✅ TÄZE
async def handle_vpn_code_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    if not context.user_data.get("waiting_vpn_code"):
        return

    context.user_data["waiting_vpn_code"] = False
    codes = update.message.text.strip().split()
    data = load_data()
    added = 0
    for code in codes:
        if code not in data["vpn_codes"]:
            data["vpn_codes"].append(code)
            added += 1
    save_data(data)

    keyboard = [[InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_panel")]]
    await update.message.reply_text(
        f"✅ *{added} sany kod goşuldy!*\n📦 Umumy: {len(data['vpn_codes'])}",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


# ==================== ADMIN PANEL GÖRKEZIJI ====================
async def show_admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    sponsors = get_sponsors()
    total_codes = len(data["vpn_codes"])
    used_codes = sum(len(v) for v in data["used_codes"].values())

    keyboard = [
        [
            InlineKeyboardButton("➕ Sponsor goş", callback_data="admin_add_sponsor"),
            InlineKeyboardButton("📋 Sponsorlar", callback_data="admin_sponsors"),
        ],
        [InlineKeyboardButton("➕ VPN Kod goş", callback_data="admin_add_code_msg")],
        [InlineKeyboardButton("📊 Statistika", callback_data="admin_stats")],
    ]
    text = (
        f"🛠 *Admin Paneli*\n\n"
        f"👥 Ulanyjylar: {len(data['users'])}\n"
        f"📢 Sponsor kanallar: {len(sponsors)}\n"
        f"🔑 Umumy kod: {total_codes}\n"
        f"🟢 Elýeterli kod: {total_codes - used_codes}"
    )

    if update.callback_query:
        await update.callback_query.edit_message_text(
            text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown"
        )


async def admin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Siz admin däl!")
        return
    await show_admin_panel(update, context)


# ==================== SPONSOR GOŞ (ConversationHandler) ====================
async def add_sponsor_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id):
        return ConversationHandler.END

    await query.edit_message_text(
        "📢 *Täze Sponsor Goşmak*\n\n"
        "1️⃣ Ilki kanalyñ *adyny* ýaz:\n"
        "_(mysal: Meniñ Kanalym)_\n\n"
        "/cancel — ýatyr",
        parse_mode="Markdown"
    )
    return WAITING_SPONSOR_NAME


async def sponsor_get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return ConversationHandler.END

    name = update.message.text.strip()
    context.user_data["new_sponsor_name"] = name

    await update.message.reply_text(
        f"✅ Ad: *{name}*\n\n"
        f"2️⃣ Indi kanalyñ *username-ini* ýaz:\n"
        f"_(mysal: @meniñkanalyñ ýa-da https://t.me/meniñkanal)_\n\n"
        f"/cancel — ýatyr",
        parse_mode="Markdown"
    )
    return WAITING_SPONSOR_USERNAME


async def sponsor_get_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return ConversationHandler.END

    raw = update.message.text.strip()
    if raw.startswith("https://t.me/"):
        username = "@" + raw.split("https://t.me/")[-1].rstrip("/")
    elif not raw.startswith("@"):
        username = "@" + raw
    else:
        username = raw

    name = context.user_data.get("new_sponsor_name", "Kanal")
    data = load_data()
    data.setdefault("sponsors", []).append({"id": username, "name": name})
    save_data(data)

    keyboard = [
        [InlineKeyboardButton("📋 Sponsorlar", callback_data="admin_sponsors")],
        [InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_panel")],
    ]
    await update.message.reply_text(
        f"✅ *Sponsor goşuldy!*\n\n"
        f"📢 Ad: {name}\n"
        f"🔗 Username: `{username}`\n\n"
        f"⚠️ Botuy kanalyñ admini edip goý!",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    return ConversationHandler.END


async def cancel_conv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Ýatyryldy.")
    return ConversationHandler.END


# ==================== VPN KOD GOŞ (command) ====================
async def add_vpn_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    if not context.args:
        await update.message.reply_text(
            "📝 *Ulanmak:* `/addcode KOD1 KOD2 KOD3`",
            parse_mode="Markdown"
        )
        return
    data = load_data()
    added = 0
    for code in context.args:
        if code not in data["vpn_codes"]:
            data["vpn_codes"].append(code)
            added += 1
    save_data(data)
    await update.message.reply_text(
        f"✅ *{added} sany kod goşuldy!*\n📦 Umumy: {len(data['vpn_codes'])}",
        parse_mode="Markdown"
    )


async def stats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    data = load_data()
    total_codes = len(data["vpn_codes"])
    used_count = sum(len(v) for v in data["used_codes"].values())
    await update.message.reply_text(
        f"📊 *Statistika:*\n\n"
        f"👥 Ulanyjylar: {len(data['users'])}\n"
        f"📢 Sponsorlar: {len(get_sponsors())}\n"
        f"🔑 Kodlar: {total_codes}\n"
        f"✅ Ulanylan: {used_count}\n"
        f"🟢 Galdy: {total_codes - used_count}",
        parse_mode="Markdown"
    )


async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    if not context.args:
        await update.message.reply_text("📢 *Ulanmak:* `/broadcast Habar`", parse_mode="Markdown")
        return
    message = " ".join(context.args)
    data = load_data()
    sent = failed = 0
    for uid in data["users"]:
        try:
            await context.bot.send_message(
                chat_id=int(uid),
                text=f"📢 *Admin habary:*\n\n{message}",
                parse_mode="Markdown"
            )
            sent += 1
        except Exception:
            failed += 1
    await update.message.reply_text(f"✅ Ugradyldy: {sent}\n❌ Başartmady: {failed}")


# ==================== ESASY ====================
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # Sponsor goşmak ConversationHandler
    sponsor_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(add_sponsor_start, pattern="^admin_add_sponsor$")],
        states={
            WAITING_SPONSOR_NAME:     [MessageHandler(filters.TEXT & ~filters.COMMAND, sponsor_get_name)],
            WAITING_SPONSOR_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, sponsor_get_username)],
        },
        fallbacks=[CommandHandler("cancel", cancel_conv)],
    )

    app.add_handler(sponsor_conv)
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_cmd))
    app.add_handler(CommandHandler("addcode", add_vpn_code))
    app.add_handler(CommandHandler("stats", stats_cmd))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CallbackQueryHandler(button_handler))
    # ✅ TÄZE: VPN kod girizme handler
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_vpn_code_input))

    print("🤖 Bot işläp başlady...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
