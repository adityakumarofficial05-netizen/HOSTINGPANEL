# =========================================================
#                TELEGRAM VERIFY BOT
# =========================================================

BOT_TOKEN = "8600428923:AAHabAtu5LXFf0M3jpSx4xnH3qVvQGgEwTs"

OWNER_IDS = [
    5988303454
]

# =========================================================
# IMPORTS
# =========================================================

import json
import time
from pathlib import Path

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup
)

from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# =========================================================
# DATABASE
# =========================================================

DB_FILE = Path("database.json")

default_data = {

    "users": {},

    "admins": [],

    "slots": [

        {
            "name": "🔮 JOIN CHANNEL 1 🔮",
            "url": "https://t.me/channel1"
        },

        {
            "name": "🔮 JOIN CHANNEL 2 🔮",
            "url": "https://t.me/channel2"
        }

    ],

    "start_text": """👻 𝗛ᴇʏ 𝗨sᴇʀ  {name}

𝐉𝐎𝐈𝐍 𝐌𝐔𝐒𝐓 𝐀𝐋𝐋 𝐂𝐇𝐀𝐍𝐍𝐄𝐋𝐒 𝐀𝐍𝐃 𝐓𝐇𝐄𝐍 🦋 𝐂𝐋𝐀𝐈𝐌 𝐕𝐀𝐋𝐈 𝐌𝐎𝐃𝐒 𝐕𝟐𝟐 𝐕𝐄𝐑𝐒𝐈𝐎𝐍

𝗛𝗢𝗪 𝗧𝗢 𝗚𝗘𝗥𝗡𝗔𝗧𝗘 𝗞𝗘𝗬
{verify_link}""",

    "verify_photo_id": None,

    "voice_id": None,

    "verify_link": "https://t.me/yourchannel",

    "verify_button_name": "🎯 GENERATE KEY",

    "bot_on": True
}

if DB_FILE.exists():

    try:

        with open(DB_FILE, "r") as f:

            data = json.load(f)

    except:

        data = default_data

else:

    data = default_data


def save_db():

    with open(DB_FILE, "w") as f:

        json.dump(data, f, indent=2)


# =========================================================
# START KEYBOARD
# =========================================================

def get_start_keyboard():

    keyboard = []

    slots = data["slots"]

    for i in range(0, len(slots), 2):

        row = []

        row.append(

            InlineKeyboardButton(

                slots[i]["name"],

                url=slots[i]["url"]
            )
        )

        if i + 1 < len(slots):

            row.append(

                InlineKeyboardButton(

                    slots[i + 1]["name"],

                    url=slots[i + 1]["url"]
                )
            )

        keyboard.append(row)

    keyboard.append([

        InlineKeyboardButton(

            data.get(
                "verify_button_name",
                "🎯 GENERATE KEY"
            ),

            url=data.get(
                "verify_link",
                "https://t.me"
            )
        )
    ])

    return InlineKeyboardMarkup(keyboard)


# =========================================================
# ADMIN KEYBOARD
# =========================================================

def get_admin_keyboard():

    return ReplyKeyboardMarkup(

        [
            ["🟢 Bot ON", "🔴 Bot OFF"],

            ["🖼 Set Verify Photo"],

            ["🎤 Add Voice", "❌ Remove Voice"],

            ["🦋 Add Generate Link",
             "✏️ Change Verify Name"],

            ["➕ Add Admin", "➖ Remove Admin"],

            ["➕ Add Channel", "➖ Remove Channel"],

            ["✏️ Edit Slot"],

            ["🔗 Set Channel Link"],

            ["📢 Broadcast"],

            ["📊 Stats"]
        ],

        resize_keyboard=True
    )


# =========================================================
# CHECK ADMIN
# =========================================================

def is_admin(user_id):

    admins = [str(x) for x in OWNER_IDS]

    admins += data.get("admins", [])

    return str(user_id) in admins


# =========================================================
# START COMMAND
# =========================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

    uid = str(user.id)

    if uid not in data["users"]:

        data["users"][uid] = {

            "name": user.first_name,

            "join_date": time.time()
        }

        save_db()

    if not data["bot_on"]:

        await update.message.reply_text(
            "❌ Bot Is OFF"
        )

        return

    text = data["start_text"] \
        .replace("{name}", user.first_name) \
        .replace("{verify_link}", data["verify_link"])

    photo = data.get("verify_photo_id")

    if photo:

        await update.message.reply_photo(

            photo=photo,

            caption=text,

            reply_markup=get_start_keyboard()
        )

    else:

        await update.message.reply_text(

            text,

            reply_markup=get_start_keyboard()
        )

    if data.get("voice_id"):

        await update.message.reply_voice(

            voice=data["voice_id"],

            caption="🎤 IMPORTANT VOICE"
        )


# =========================================================
# ADMIN COMMAND
# =========================================================

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_admin(update.effective_user.id):

        await update.message.reply_text(
            "❌ Access Denied"
        )

        return

    await update.message.reply_text(

        "👑 ADMIN PANEL",

        reply_markup=get_admin_keyboard()
    )


# =========================================================
# HANDLE TEXT
# =========================================================

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_admin(update.effective_user.id):
        return

    text = update.message.text

    # =====================================================
    # BUTTONS
    # =====================================================

    if text == "🟢 Bot ON":

        data["bot_on"] = True

        save_db()

        await update.message.reply_text(
            "✅ Bot ON"
        )

    elif text == "🔴 Bot OFF":

        data["bot_on"] = False

        save_db()

        await update.message.reply_text(
            "❌ Bot OFF"
        )

    elif text == "🖼 Set Verify Photo":

        context.user_data["state"] = "waiting_photo"

        await update.message.reply_text(
            "📸 Send Photo"
        )

    elif text == "🎤 Add Voice":

        context.user_data["state"] = "waiting_voice"

        await update.message.reply_text(
            "🎤 Send Voice"
        )

    elif text == "❌ Remove Voice":

        data["voice_id"] = None

        save_db()

        await update.message.reply_text(
            "❌ Voice Removed"
        )

    elif text == "🦋 Add Generate Link":

        context.user_data["state"] = "waiting_generate_link"

        await update.message.reply_text(
            "🔗 Send New Generate Link"
        )

    elif text == "✏️ Change Verify Name":

        context.user_data["state"] = "waiting_verify_name"

        await update.message.reply_text(
            "✏️ Send New Verify Button Name"
        )

    elif text == "➕ Add Admin":

        context.user_data["state"] = "waiting_add_admin"

        await update.message.reply_text(
            "Send Admin ID"
        )

    elif text == "➖ Remove Admin":

        context.user_data["state"] = "waiting_remove_admin"

        await update.message.reply_text(
            "Send Admin ID"
        )

    elif text == "➕ Add Channel":

        if len(data["slots"]) >= 20:

            await update.message.reply_text(
                "❌ Max 20 Channels Allowed"
            )

            return

        context.user_data["state"] = "waiting_channel_name"

        await update.message.reply_text(
            "Send Channel Button Name"
        )

    elif text == "➖ Remove Channel":

        msg = "Send Channel Number Remove\n\n"

        for i, slot in enumerate(data["slots"], start=1):

            msg += f"{i}. {slot['name']}\n"

        context.user_data["state"] = "waiting_remove_channel"

        await update.message.reply_text(msg)

    elif text == "✏️ Edit Slot":

        msg = "Send Slot Number Edit\n\n"

        for i, slot in enumerate(data["slots"], start=1):

            msg += f"{i}. {slot['name']}\n"

        context.user_data["state"] = "waiting_edit_slot"

        await update.message.reply_text(msg)

    elif text == "🔗 Set Channel Link":

        msg = "Send Slot Number Change Link\n\n"

        for i, slot in enumerate(data["slots"], start=1):

            msg += f"{i}. {slot['name']}\n"

        context.user_data["state"] = "waiting_link_slot"

        await update.message.reply_text(msg)

    elif text == "📢 Broadcast":

        context.user_data["state"] = "waiting_broadcast"

        await update.message.reply_text(
            "📢 Send Broadcast Message"
        )

    elif text == "📊 Stats":

        await update.message.reply_text(

            f"👥 Users: {len(data['users'])}\n"
            f"👑 Admins: {len(data['admins'])}\n"
            f"📢 Channels: {len(data['slots'])}"
        )

    # =====================================================
    # STATES
    # =====================================================

    else:

        state = context.user_data.get("state")

        # =================================================
        # GENERATE LINK
        # =================================================

        if state == "waiting_generate_link":

            if not text.startswith("http"):

                await update.message.reply_text(
                    "❌ Invalid Link"
                )

                return

            data["verify_link"] = text.strip()

            save_db()

            await update.message.reply_text(
                "✅ Generate Link Updated"
            )

            del context.user_data["state"]

        # =================================================
        # VERIFY BUTTON NAME
        # =================================================

        elif state == "waiting_verify_name":

            data["verify_button_name"] = text

            save_db()

            await update.message.reply_text(
                "✅ Verify Button Name Updated"
            )

            del context.user_data["state"]

        # =================================================
        # ADD ADMIN
        # =================================================

        elif state == "waiting_add_admin":

            admin_id = text.strip()

            if admin_id not in data["admins"]:

                data["admins"].append(admin_id)

                save_db()

                await update.message.reply_text(
                    "✅ Admin Added"
                )

            else:

                await update.message.reply_text(
                    "❌ Already Admin"
                )

            del context.user_data["state"]

        # =================================================
        # REMOVE ADMIN
        # =================================================

        elif state == "waiting_remove_admin":

            admin_id = text.strip()

            if admin_id in data["admins"]:

                data["admins"].remove(admin_id)

                save_db()

                await update.message.reply_text(
                    "❌ Admin Removed"
                )

            else:

                await update.message.reply_text(
                    "❌ Admin Not Found"
                )

            del context.user_data["state"]

        # =================================================
        # ADD CHANNEL NAME
        # =================================================

        elif state == "waiting_channel_name":

            context.user_data["channel_name"] = text

            context.user_data["state"] = "waiting_channel_link"

            await update.message.reply_text(
                "Send Channel Link"
            )

        # =================================================
        # ADD CHANNEL LINK
        # =================================================

        elif state == "waiting_channel_link":

            if not text.startswith("http"):

                await update.message.reply_text(
                    "❌ Invalid Link"
                )

                return

            name = context.user_data["channel_name"]

            data["slots"].append({

                "name": name,

                "url": text.strip()
            })

            save_db()

            await update.message.reply_text(
                "✅ Channel Added"
            )

            del context.user_data["state"]

            del context.user_data["channel_name"]

        # =================================================
        # REMOVE CHANNEL
        # =================================================

        elif state == "waiting_remove_channel":

            try:

                index = int(text) - 1

                removed = data["slots"].pop(index)

                save_db()

                await update.message.reply_text(
                    f"❌ Removed\n{removed['name']}"
                )

            except:

                await update.message.reply_text(
                    "❌ Invalid Number"
                )

            del context.user_data["state"]

        # =================================================
        # EDIT SLOT
        # =================================================

        elif state == "waiting_edit_slot":

            try:

                index = int(text) - 1

                context.user_data["edit_index"] = index

                context.user_data["state"] = "waiting_new_slot_name"

                await update.message.reply_text(
                    "Send New Slot Name"
                )

            except:

                await update.message.reply_text(
                    "❌ Invalid Number"
                )

        elif state == "waiting_new_slot_name":

            index = context.user_data["edit_index"]

            data["slots"][index]["name"] = text

            save_db()

            await update.message.reply_text(
                "✅ Slot Name Updated"
            )

            del context.user_data["state"]

            del context.user_data["edit_index"]

        # =================================================
        # CHANGE CHANNEL LINK
        # =================================================

        elif state == "waiting_link_slot":

            try:

                index = int(text) - 1

                context.user_data["link_index"] = index

                context.user_data["state"] = "waiting_new_channel_link"

                await update.message.reply_text(
                    "🔗 Send New Channel Link"
                )

            except:

                await update.message.reply_text(
                    "❌ Invalid Number"
                )

        elif state == "waiting_new_channel_link":

            if not text.startswith("http"):

                await update.message.reply_text(
                    "❌ Invalid Link"
                )

                return

            index = context.user_data["link_index"]

            data["slots"][index]["url"] = text.strip()

            save_db()

            await update.message.reply_text(
                "✅ Channel Link Updated"
            )

            del context.user_data["state"]

            del context.user_data["link_index"]

        # =================================================
        # BROADCAST
        # =================================================

        elif state == "waiting_broadcast":

            sent = 0

            failed = 0

            for user_id in data["users"]:

                try:

                    await context.bot.send_message(

                        chat_id=int(user_id),

                        text=text
                    )

                    sent += 1

                except:

                    failed += 1

            await update.message.reply_text(

                f"✅ Broadcast Done\n\n"
                f"📤 Sent: {sent}\n"
                f"❌ Failed: {failed}"
            )

            del context.user_data["state"]


# =========================================================
# PHOTO HANDLER
# =========================================================

async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_admin(update.effective_user.id):
        return

    state = context.user_data.get("state")

    if state == "waiting_photo":

        photo_id = update.message.photo[-1].file_id

        data["verify_photo_id"] = photo_id

        save_db()

        await update.message.reply_text(
            "✅ Verify Photo Updated"
        )

        del context.user_data["state"]


# =========================================================
# VOICE HANDLER
# =========================================================

async def voice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_admin(update.effective_user.id):
        return

    state = context.user_data.get("state")

    if state == "waiting_voice":

        voice_id = update.message.voice.file_id

        data["voice_id"] = voice_id

        save_db()

        await update.message.reply_text(
            "✅ Voice Added"
        )

        del context.user_data["state"]


# =========================================================
# MAIN
# =========================================================

def main():

    print("✅ BOT RUNNING")

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(
        CommandHandler("start", start)
    )

    app.add_handler(
        CommandHandler("admin", admin)
    )

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_text
        )
    )

    app.add_handler(
        MessageHandler(
            filters.PHOTO,
            photo_handler
        )
    )

    app.add_handler(
        MessageHandler(
            filters.VOICE,
            voice_handler
        )
    )

    app.run_polling()


# =========================================================
# START
# =========================================================

if __name__ == "__main__":

    main()