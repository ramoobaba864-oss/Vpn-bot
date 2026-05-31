import logging
import json
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, ConversationHandler
)

BOT_TOKEN = "8883106625:AAFHJTKdIkNiBHF58D6-JWmeMoOhDDEtX_M"
ADMIN_IDS = [7331708536]
DATA_FILE = "data.json"
ADMINS_FILE = "admins.json"

WAITING_SPONSOR_NAME, WAITING_SPONSOR_USERNAME = range(2)

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)


def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"vpn_codes": [], "used_codes": {}, "users": {}, "sponsors": []}


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_admins():
    if os.path.exists(ADMINS_FILE):
        with open(ADMINS_FILE, "r") as f:
            return json.load(f).get("admins", ADMIN_IDS)
    return list(ADMIN_IDS)


def save_admins(admins):
    with open(ADMINS_FILE, "w") as f:
        json.dump({"admins": admins}, f)


def get_sponsors():
    return load_data().get("sponsors", [])


def is_admin(user_id):
    return user_id in load_admins()


async def check_subscriptions(user_id, bot):
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


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    data = load_data()
    user_id = str(user.id)
    if user_id not in data["users"]:
        data["users"][user_id] = {"name": user.full_name, "username": user.username or "", "vpn_count": 0}
        save_data(data)

    sponsors = get_sponsors()
    if not sponsors:
        await show_main_menu(update, context)
        return

    not_subscribed = await check_subscriptions(user.id, context.bot)
    if not_subscribed:
        keyboard = []
        row = []
        for ch in not_subscribed:
            row.append(InlineKeyboardButton(f"📢 {ch['name']} ↗", url=f"https://t.me/{ch['id'].lstrip('@')}"))
            if len(row) == 2:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)
        keyboard.append([InlineKeyboardButton("✅ Agza boldum, barla!", callback_data="check_sub")])
        await update.message.reply_text(
            "Salam men @cynex_vpn kanalynyñ boty📌\n\n"
            "Men size 7/24 işleýän vpn kodlaryny berýän🔒\n\n"
            "Siziñ etmeli işiñiz diñe sponsorlarymyza agza bolmak✅\n\n"
            "Boda kanal goşdurmak üçin: @Attackaltt✅️\n\n"
            "⬇️ Aşakdaky kanallara agza bol:",
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
    text = "🌐 *VPN BOT-a hoş geldiñiz!*\n\nBu bot arkaly mugt VPN kodlaryny alyp bilersiñiz.\n\nAşakdaky düwmelerden birini saý:"
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    else:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")


async def show_admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    sponsors = get_sponsors()
    total_codes = len(data["vpn_codes"])
    keyboard = [
        [
            InlineKeyboardButton("➕ Sponsor goş", callback_data="admin_add_sponsor"),
            InlineKeyboardButton("📋 Sponsorlar", callback_data="admin_sponsors"),
        ],
        [InlineKeyboardButton("➕ VPN Kod goş", callback_data="admin_add_code_msg")],
        [InlineKeyboardButton("🗑 VPN Kodlar", callback_data="admin_list_codes")],
        [InlineKeyboardButton("👤 Admin goş", callback_data="admin_add_admin")],
        [InlineKeyboardButton("📊 Statistika", callback_data="admin_stats")],
    ]
    text = (
        f"🛠 *Admin Paneli*\n\n"
        f"👥 Ulanyjylar: {len(data['users'])}\n"
        f"📢 Sponsor kanallar: {len(sponsors)}\n"
        f"🔑 Umumy kod: {total_codes}"
    )
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    else:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")


async def admin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Siz admin däl!")
        return
    await show_admin_panel(update, context)


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    data = load_data()

    if query.data == "check_sub":
        not_subscribed = await check_subscriptions(user.id, context.bot)
        if not_subscribed:
            names = "\n".join([f"• {ch['name']}" for ch in not_subscribed])
            await query.answer(f"❌ Heniz agza bolmadyk:\n{names}", show_alert=True)
        else:
            await show_main_menu(update, context)

    elif query.data == "get_vpn":
        not_subscribed = await check_subscriptions(user.id, context.bot)
        if not_subscribed:
            await query.answer("❌ Ilki kanallara agza bol!", show_alert=True)
            return
        if not data["vpn_codes"]:
            await query.edit_message_text("😔 *Häzirki wagtda VPN kod ýok.*\n\nBiraz soň gaýdyp gel.", parse_mode="Markdown")
            return
        code = data["vpn_codes"][0]
        keyboard = [[InlineKeyboardButton("🏠 Baş menýu", callback_data="main_menu")]]
        await query.edit_message_text(
            f"✅ *Seniñ VPN Kodun:*\n\n```\n{code}\n```\n\n📋 Kody kopyala we VPN programmañda ullan!",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

    elif query.data == "my_info":
        user_id = str(user.id)
        keyboard = [[InlineKeyboardButton("🏠 Baş menýu", callback_data="main_menu")]]
        await query.edit_message_text(
            f"👤 *Seniñ maglumatlaryn:*\n\n🆔 ID: `{user.id}`\n👤 Ady: {user.full_name}",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

    elif query.data == "main_menu":
        await show_main_menu(update, context)

    elif query.data == "admin_panel":
        if not is_admin(user.id):
            await query.answer("❌ Siz admin däl!", show_alert=True)
            return
        await show_admin_panel(update, context)

    elif query.data == "admin_sponsors":
        sponsors = get_sponsors()
        if not sponsors:
            keyboard = [
                [InlineKeyboardButton("➕ Sponsor goş", callback_data="admin_add_sponsor")],
                [InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_panel")],
            ]
            await query.edit_message_text("📭 *Heniz sponsor kanal ýok.*", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
            return
        text = "📢 *Sponsor Kanallar:*\n\n"
        keyboard = []
        for i, sp in enumerate(sponsors):
            text += f"{i+1}. {sp['name']} — `{sp['id']}`\n"
            keyboard.append([InlineKeyboardButton(f"🗑 {sp['name']} sil", callback_data=f"del_sponsor_{i}")])
        keyboard.append([InlineKeyboardButton("➕ Täze sponsor goş", callback_data="admin_add_sponsor")])
        keyboard.append([InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_panel")])
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

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
            await query.edit_message_text("📭 *Sponsor kanal ýok.*", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        else:
            text = "📢 *Sponsor Kanallar:*\n\n"
            keyboard = []
            for i, sp in enumerate(sponsors):
                text += f"{i+1}. {sp['name']} — `{sp['id']}`\n"
                keyboard.append([InlineKeyboardButton(f"🗑 {sp['name']} sil", callback_data=f"del_sponsor_{i}")])
            keyboard.append([InlineKeyboardButton("➕ Täze sponsor goş", callback_data="admin_add_sponsor")])
            keyboard.append([InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_panel")])
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif query.data == "admin_add_code_msg":
        if not is_admin(user.id):
            await query.answer("❌ Siz admin däl!", show_alert=True)
            return
        context.user_data["waiting_vpn_code"] = True
        keyboard = [[InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_panel")]]
        await query.edit_message_text(
            "➕ *VPN Kod Goşmak*\n\nKodlary ýaz (boşluk bilen):\n\nMysal:\n`KOD1 KOD2 KOD3`",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

    elif query.data == "admin_list_codes":
        if not is_admin(user.id):
            await query.answer("❌ Siz admin däl!", show_alert=True)
            return
        codes = data["vpn_codes"]
        if not codes:
            keyboard = [[InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_panel")]]
            await query.edit_message_text("📭 *Heniz VPN kod ýok.*", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
            return
        text = "🔑 *VPN Kodlar:*\n\n"
        keyboard = []
        for i, code in enumerate(codes):
            short = code[:25] + "..." if len(code) > 25 else code
            text += f"{i+1}. `{short}`\n"
            keyboard.append([InlineKeyboardButton(f"🗑 {i+1}. kody sil", callback_data=f"del_code_{i}")])
        keyboard.append([InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_panel")])
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif query.data.startswith("del_code_"):
        if not is_admin(user.id):
            await query.answer("❌ Siz admin däl!", show_alert=True)
            return
        idx = int(query.data.split("_")[-1])
        if idx < len(data["vpn_codes"]):
            data["vpn_codes"].pop(idx)
            save_data(data)
            await query.answer("✅ Kod aýryldy!", show_alert=True)
        codes = data["vpn_codes"]
        if not codes:
            keyboard = [[InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_panel")]]
            await query.edit_message_text("📭 *Heniz VPN kod ýok.*", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
            return
        text = "🔑 *VPN Kodlar:*\n\n"
        keyboard = []
        for i, code in enumerate(codes):
            short = code[:25] + "..." if len(code) > 25 else code
            text += f"{i+1}. `{short}`\n"
            keyboard.append([InlineKeyboardButton(f"🗑 {i+1}. kody sil", callback_data=f"del_code_{i}")])
        keyboard.append([InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_panel")])
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif query.data == "admin_add_admin":
        if not is_admin(user.id):
            await query.answer("❌ Siz admin däl!", show_alert=True)
            return
        context.user_data["waiting_new_admin"] = True
        keyboard = [[InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_panel")]]
        await query.edit_message_text(
            "👤 *Täze Admin Goşmak*\n\nTäze adminiñ *Telegram ID-sini* ýaz:\n_(mysal: 123456789)_",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

    elif query.data == "admin_stats":
        sponsors = get_sponsors()
        total_codes = len(data["vpn_codes"])
        keyboard = [[InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_panel")]]
        await query.edit_message_text(
            f"📊 *Bot Statistikasy:*\n\n"
            f"👥 Ulanyjylar: {len(data['users'])}\n"
            f"📢 Sponsor kanallar: {len(sponsors)}\n"
            f"🔑 Umumy kod: {total_codes}",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )


async def add_sponsor_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id):
        return ConversationHandler.END
    await query.edit_message_text(
        "📢 *Täze Sponsor Goşmak*\n\n1️⃣ Kanalyñ *adyny* ýaz:\n\n/cancel — ýatyr",
        parse_mode="Markdown"
    )
    return WAITING_SPONSOR_NAME


async def sponsor_get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return ConversationHandler.END
    context.user_data["new_sponsor_name"] = update.message.text.strip()
    await update.message.reply_text(
        f"✅ Ad: *{context.user_data['new_sponsor_name']}*\n\n2️⃣ Kanalyñ *username-ini* ýaz:\n_(mysal: @kanal)_\n\n/cancel — ýatyr",
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
        f"✅ *Sponsor goşuldy!*\n\n📢 Ad: {name}\n🔗 Username: `{username}`\n\n⚠️ Botuy kanalyñ admini edip goý!",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    return ConversationHandler.END


async def cancel_conv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Ýatyryldy.")
    return ConversationHandler.END


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    if context.user_data.get("waiting_new_admin"):
        context.user_data["waiting_new_admin"] = False
        try:
            new_id = int(update.message.text.strip())
            admins = load_admins()
            if new_id not in admins:
                admins.append(new_id)
                save_admins(admins)
                keyboard = [[InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_panel")]]
                await update.message.reply_text(
                    f"✅ *Täze admin goşuldy!*\n🆔 ID: `{new_id}`",
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode="Markdown"
                )
            else:
                await update.message.reply_text("⚠️ Bu ulanyjy eýýäm admin!")
        except ValueError:
            await update.message.reply_text("❌ Nädogry ID! Diñe san ýaz.")
        return

    if context.user_data.get("waiting_vpn_code"):
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


async def add_vpn_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    if not context.args:
        await update.message.reply_text("📝 *Ulanmak:* `/addcode KOD1 KOD2`", parse_mode="Markdown")
        return
    data = load_data()
    added = 0
    for code in context.args:
        if code not in data["vpn_codes"]:
            data["vpn_codes"].append(code)
            added += 1
    save_data(data)
    await update.message.reply_text(f"✅ *{added} sany kod goşuldy!*\n📦 Umumy: {len(data['vpn_codes'])}", parse_mode="Markdown")


async def clear_vpn_codes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    data = load_data()
    count = len(data["vpn_codes"])
    data["vpn_codes"] = []
    data["used_codes"] = {}
    save_data(data)
    await update.message.reply_text(f"🗑 *{count} sany kod pozuldy!*", parse_mode="Markdown")


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
            await context.bot.send_message(chat_id=int(uid), text=f"📢 *Admin habary:*\n\n{message}", parse_mode="Markdown")
            sent += 1
        except Exception:
            failed += 1
    await update.message.reply_text(f"✅ Ugradyldy: {sent}\n❌ Başartmady: {failed}")


def main():
    app = Application.builder().token(BOT_TOKEN).build()

    sponsor_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(add_sponsor_start, pattern="^admin_add_sponsor$")],
        states={
            WAITING_SPONSOR_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, sponsor_get_name)],
            WAITING_SPONSOR_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, sponsor_get_username)],
        },
        fallbacks=[CommandHandler("cancel", cancel_conv)],
    )

    app.add_handler(sponsor_conv)
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_cmd))
    app.add_handler(CommandHandler("addcode", add_vpn_code))
    app.add_handler(CommandHandler("clearcode", clear_vpn_codes))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    print("🤖 Bot işläp başlady...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
