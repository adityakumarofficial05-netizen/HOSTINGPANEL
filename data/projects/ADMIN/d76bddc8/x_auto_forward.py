"""
╔══════════════════════════════════════════════════════════════╗
║           X AUTO FORWARD BOT — Main Bot Script               ║
║  Built with python-telegram-bot (v20+, async/await style)    ║
╚══════════════════════════════════════════════════════════════╝

Features:
  • Secure Admin Panel (owner can promote/demote admins by User ID)
  • Channel management (add/remove channel IDs)
  • Broadcast / Auto-Forward to all channels or a selected subset
  • Professional Inline Keyboard UI with submenu support
  • Persistent JSON-based storage (no database required)
  • Graceful error handling for missing bot permissions

Setup:
  1. pip install python-telegram-bot>=20.0
  2. Set BOT_TOKEN and OWNER_ID below (or use environment variables)
  3. python x_auto_forward_bot.py
"""

import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Optional

from telegram import (
    Bot,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    Update,
)
from telegram.constants import ParseMode
from telegram.error import BadRequest, Forbidden, TelegramError
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

# ──────────────────────────────────────────────────────────────
#  CONFIGURATION  (override via environment variables in prod)
# ──────────────────────────────────────────────────────────────

BOT_TOKEN: str = os.getenv("BOT_TOKEN", "8966684570:AAFq0IqeI19Z_UoZwFJY-Z2KzcR-1lXOxGM")
OWNER_ID: int = int(os.getenv("7216698208", "7216698208"))          # Your Telegram numeric user ID
DATA_FILE: Path = Path("bot_data.json")                   # Persistent storage file

# ──────────────────────────────────────────────────────────────
#  LOGGING
# ──────────────────────────────────────────────────────────────

logging.basicConfig(
    format="%(asctime)s | %(levelname)-8s | %(name)s — %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("XAutoForwardBot")

# ──────────────────────────────────────────────────────────────
#  CONVERSATION STATES
# ──────────────────────────────────────────────────────────────

(
    STATE_MAIN,
    STATE_ADD_CHANNEL,
    STATE_REMOVE_CHANNEL,
    STATE_ADD_ADMIN,
    STATE_REMOVE_ADMIN,
    STATE_BROADCAST_MSG,
    STATE_BROADCAST_SELECT,
    STATE_GET_CHANNEL_ID,
) = range(8)

# ──────────────────────────────────────────────────────────────
#  DATA STORE  (lightweight JSON persistence)
# ──────────────────────────────────────────────────────────────

def _default_data() -> dict:
    return {"admins": [], "channels": {}}


def load_data() -> dict:
    """Load bot data from JSON file; return defaults if missing/corrupt."""
    if DATA_FILE.exists():
        try:
            with DATA_FILE.open("r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Could not read data file (%s). Using defaults.", exc)
    return _default_data()


def save_data(data: dict) -> None:
    """Persist bot data to JSON file atomically."""
    tmp = DATA_FILE.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    tmp.replace(DATA_FILE)


# ──────────────────────────────────────────────────────────────
#  PERMISSION HELPERS
# ──────────────────────────────────────────────────────────────

def is_owner(user_id: int) -> bool:
    return user_id == OWNER_ID


def is_admin(user_id: int, data: dict) -> bool:
    return is_owner(user_id) or user_id in data.get("admins", [])


def require_admin(func):
    """Decorator: reject non-admins with a clean notice."""
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        uid = update.effective_user.id
        data = load_data()
        if not is_admin(uid, data):
            await update.effective_message.reply_text(
                "🚫 *Access Denied* — You don't have admin privileges.",
                parse_mode=ParseMode.MARKDOWN,
            )
            return ConversationHandler.END
        return await func(update, context, data)
    wrapper.__name__ = func.__name__
    return wrapper


# ──────────────────────────────────────────────────────────────
#  UI BUILDERS  (Inline Keyboards)
# ──────────────────────────────────────────────────────────────

EMOJI = {
    "broadcast": "📣",
    "add_ch":    "➕",
    "rm_ch":     "➖",
    "channels":  "📋",
    "admin":     "⚙️",
    "add_adm":   "👤",
    "rm_adm":    "🗑",
    "list_adm":  "👥",
    "back":      "◀️",
    "menu":      "⊞",   # 4-box menu icon
    "check":     "✅",
    "cross":     "❌",
    "info":      "ℹ️",
    "refresh":   "🔄",
    "get_id":    "🆔",
}

# Telegram inline buttons cannot have real background colours.
# These colour badges make every button look different and premium in Telegram.
BTN = {
    "red": "🔴",
    "blue": "🔵",
    "green": "🟢",
    "yellow": "🟡",
    "purple": "🟣",
    "orange": "🟠",
    "black": "⚫",
    "white": "⚪",
}


def cbtn(color: str, text: str) -> str:
    return f"{BTN.get(color, '🔘')} {text}"


def kb_main_menu() -> InlineKeyboardMarkup:
    """Home panel — shown after /start or when pressing Back."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(cbtn("red", f"{EMOJI['broadcast']} Broadcast"),  callback_data="broadcast"),
            InlineKeyboardButton(cbtn("blue", f"{EMOJI['channels']} Channels"),    callback_data="channels"),
        ],
        [
            InlineKeyboardButton(cbtn("green", f"{EMOJI['add_ch']} Add Channel"),   callback_data="add_channel"),
            InlineKeyboardButton(cbtn("orange", f"{EMOJI['rm_ch']} Remove Channel"), callback_data="remove_channel"),
        ],
        [
            InlineKeyboardButton(cbtn("purple", f"{EMOJI['get_id']} Get Channel ID"), callback_data="get_channel_id"),
        ],
        [
            InlineKeyboardButton(
                cbtn("black", f"{EMOJI['menu']} Admin Settings"),
                callback_data="admin_menu",
            ),
        ],
    ])


def kb_admin_menu(is_owner_flag: bool = False) -> InlineKeyboardMarkup:
    """Admin submenu — only meaningful buttons visible."""
    rows = [
        [
            InlineKeyboardButton(cbtn("blue", f"{EMOJI['list_adm']} List Admins"), callback_data="list_admins"),
        ],
    ]
    if is_owner_flag:
        rows.append([
            InlineKeyboardButton(cbtn("green", f"{EMOJI['add_adm']} Add Admin"),    callback_data="add_admin"),
            InlineKeyboardButton(cbtn("red", f"{EMOJI['rm_adm']} Remove Admin"),  callback_data="remove_admin"),
        ])
    rows.append([
        InlineKeyboardButton(cbtn("black", f"{EMOJI['back']} Back to Menu"), callback_data="main_menu"),
    ])
    return InlineKeyboardMarkup(rows)


def kb_back_only() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton(cbtn("black", f"{EMOJI['back']} Back to Menu"), callback_data="main_menu"),
    ]])


def kb_broadcast_scope(channels: dict) -> InlineKeyboardMarkup:
    """Let admin choose: all channels or pick individually."""
    rows = [
        [InlineKeyboardButton(cbtn("red", f"{EMOJI['broadcast']} Send to ALL Channels"), callback_data="bcast_all")],
    ]
    for cid, name in list(channels.items())[:10]:   # cap at 10 to avoid overflow
        rows.append([InlineKeyboardButton(
            cbtn("green", f"{EMOJI['check']} {name} ({cid})"),
            callback_data=f"bcast_one:{cid}",
        )])
    rows.append([InlineKeyboardButton(cbtn("orange", f"{EMOJI['back']} Cancel"), callback_data="main_menu")])
    return InlineKeyboardMarkup(rows)


# ──────────────────────────────────────────────────────────────
#  TEXT TEMPLATES
# ──────────────────────────────────────────────────────────────

WELCOME_TEXT = (
    "╔════════════════════════╗\n"
    "║.      *X AUTO FORWARD BOT*     ║\n"
    "╚════════════════════════╝\n\n"
    "Welcome, *{name}*! 👋\n\n"
    "Use the panel below to manage broadcasts, channels, channel IDs, and admin settings.\n\n"
    f"_{EMOJI['get_id']} Tap *Get Channel ID* to fetch a channel ID before adding._"
)


# ──────────────────────────────────────────────────────────────
#  /start COMMAND
# ──────────────────────────────────────────────────────────────

@require_admin
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE, data: dict):
    """Show the main menu panel."""
    name = update.effective_user.first_name or "Admin"
    text = WELCOME_TEXT.format(name=name)
    await update.message.reply_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=kb_main_menu(),
    )
    return STATE_MAIN


# ──────────────────────────────────────────────────────────────
#  CALLBACK QUERY ROUTER
# ──────────────────────────────────────────────────────────────

@require_admin
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, data: dict):
    """Central dispatcher for all InlineKeyboard callbacks."""
    query: CallbackQuery = update.callback_query
    await query.answer()
    cbd = query.data

    # ── Main menu ──────────────────────────────────────────────
    if cbd == "main_menu":
        await query.edit_message_text(
            WELCOME_TEXT.format(name=update.effective_user.first_name or "Admin"),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=kb_main_menu(),
        )
        return STATE_MAIN

    # ── Channel list ───────────────────────────────────────────
    if cbd == "channels":
        channels = data.get("channels", {})
        if not channels:
            text = f"{EMOJI['info']} *No channels registered yet.*\nUse *Add Channel* to get started."
        else:
            lines = [f"*Registered Channels* ({len(channels)})\n"]
            for cid, name in channels.items():
                lines.append(f"  • `{cid}` — {name}")
            text = "\n".join(lines)
        await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=kb_back_only())
        return STATE_MAIN

    # ── Get channel ID helper ──────────────────────────────────
    if cbd == "get_channel_id":
        await query.edit_message_text(
            f"{EMOJI['get_id']} *Get Channel ID*\n\n"
            "Forward any post from your channel to this bot.\n\n"
            "I will detect and show the channel ID like `-1001234567890`.\n\n"
            "You can also send `@channelusername` if the channel is public.",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=kb_back_only(),
        )
        return STATE_GET_CHANNEL_ID

    # ── Add channel ────────────────────────────────────────────
    if cbd == "add_channel":
        context.user_data["action"] = "add_channel"
        await query.edit_message_text(
            f"{EMOJI['add_ch']} *Add a Channel*\n\n"
            "Send the channel ID (e.g. `-1001234567890`) or username (e.g. `@mychannel`).\n\n"
            f"Need ID? Tap *{EMOJI['get_id']} Get Channel ID* first.\n\n"
            "_Make sure the bot is already an admin in that channel._",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=kb_back_only(),
        )
        return STATE_ADD_CHANNEL

    # ── Remove channel ─────────────────────────────────────────
    if cbd == "remove_channel":
        channels = data.get("channels", {})
        if not channels:
            await query.edit_message_text(
                f"{EMOJI['info']} No channels to remove.",
                reply_markup=kb_back_only(),
            )
            return STATE_MAIN
        context.user_data["action"] = "remove_channel"
        lines = ["*Remove a Channel*\n", "Reply with the channel ID to remove:\n"]
        for cid, name in channels.items():
            lines.append(f"  • `{cid}` — {name}")
        await query.edit_message_text(
            "\n".join(lines),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=kb_back_only(),
        )
        return STATE_REMOVE_CHANNEL

    # ── Broadcast ──────────────────────────────────────────────
    if cbd == "broadcast":
        channels = data.get("channels", {})
        if not channels:
            await query.edit_message_text(
                f"{EMOJI['info']} *No channels added yet.*\nAdd channels first via *Add Channel*.",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=kb_back_only(),
            )
            return STATE_MAIN
        await query.edit_message_text(
            f"{EMOJI['broadcast']} *Broadcast*\n\nChoose where to send:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=kb_broadcast_scope(channels),
        )
        return STATE_BROADCAST_SELECT

    # ── Broadcast: ALL channels ────────────────────────────────
    if cbd == "bcast_all":
        context.user_data["bcast_targets"] = list(data.get("channels", {}).keys())
        await query.edit_message_text(
            f"{EMOJI['broadcast']} *Broadcast to ALL channels*\n\nNow send me the message to forward.",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=kb_back_only(),
        )
        return STATE_BROADCAST_MSG

    # ── Broadcast: single channel ──────────────────────────────
    if cbd.startswith("bcast_one:"):
        cid = cbd.split(":", 1)[1]
        context.user_data["bcast_targets"] = [cid]
        ch_name = data.get("channels", {}).get(cid, cid)
        await query.edit_message_text(
            f"{EMOJI['broadcast']} *Broadcast to* `{ch_name}`\n\nNow send me the message to forward.",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=kb_back_only(),
        )
        return STATE_BROADCAST_MSG

    # ── Admin submenu ──────────────────────────────────────────
    if cbd == "admin_menu":
        owner_flag = is_owner(update.effective_user.id)
        await query.edit_message_text(
            f"{EMOJI['menu']} *Admin Settings*\n\n"
            f"{'_Owner mode — full access._' if owner_flag else '_Admin mode._'}",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=kb_admin_menu(is_owner_flag=owner_flag),
        )
        return STATE_MAIN

    # ── List admins ────────────────────────────────────────────
    if cbd == "list_admins":
        admins = data.get("admins", [])
        lines = [f"*Admin List*\n\n• `{OWNER_ID}` _(Owner)_"]
        for aid in admins:
            lines.append(f"• `{aid}`")
        if not admins:
            lines.append("_No additional admins yet._")
        await query.edit_message_text(
            "\n".join(lines),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=kb_back_only(),
        )
        return STATE_MAIN

    # ── Add admin (owner only) ─────────────────────────────────
    if cbd == "add_admin":
        if not is_owner(update.effective_user.id):
            await query.answer("Only the owner can add admins.", show_alert=True)
            return STATE_MAIN
        context.user_data["action"] = "add_admin"
        await query.edit_message_text(
            f"{EMOJI['add_adm']} *Add Admin*\n\nSend the Telegram *User ID* of the new admin.",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=kb_back_only(),
        )
        return STATE_ADD_ADMIN

    # ── Remove admin (owner only) ──────────────────────────────
    if cbd == "remove_admin":
        if not is_owner(update.effective_user.id):
            await query.answer("Only the owner can remove admins.", show_alert=True)
            return STATE_MAIN
        admins = data.get("admins", [])
        if not admins:
            await query.edit_message_text(
                f"{EMOJI['info']} No additional admins to remove.",
                reply_markup=kb_back_only(),
            )
            return STATE_MAIN
        context.user_data["action"] = "remove_admin"
        lines = ["*Remove Admin*\n\nReply with the User ID to remove:\n"]
        for aid in admins:
            lines.append(f"  • `{aid}`")
        await query.edit_message_text(
            "\n".join(lines),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=kb_back_only(),
        )
        return STATE_REMOVE_ADMIN

    # Fallback
    logger.warning("Unhandled callback: %s", cbd)
    return STATE_MAIN


# ──────────────────────────────────────────────────────────────
#  MESSAGE HANDLERS  (conversation states)
# ──────────────────────────────────────────────────────────────

@require_admin
async def handle_get_channel_id(update: Update, context: ContextTypes.DEFAULT_TYPE, data: dict):
    """Get a channel ID from a forwarded channel post or public @username."""
    msg: Message = update.message
    bot: Bot = context.bot
    chat = None

    # New Telegram API style: message.forward_origin.chat
    origin = getattr(msg, "forward_origin", None)
    if origin and getattr(origin, "chat", None):
        chat = origin.chat

    # Legacy style fallback
    if chat is None and getattr(msg, "forward_from_chat", None):
        chat = msg.forward_from_chat

    # Public username fallback
    text = (msg.text or "").strip()
    if chat is None and text.startswith("@"):
        try:
            chat = await bot.get_chat(text)
        except (BadRequest, TelegramError) as exc:
            await msg.reply_text(
                f"{EMOJI['cross']} Cannot fetch this channel: `{exc}`\n\n"
                "Forward a channel post here, or check the public username.",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=kb_back_only(),
            )
            return STATE_GET_CHANNEL_ID

    if chat is None:
        await msg.reply_text(
            f"{EMOJI['info']} *Send a forwarded channel post.*\n\n"
            "Open your channel → forward any post to this bot → I will show the channel ID.",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=kb_back_only(),
        )
        return STATE_GET_CHANNEL_ID

    cid = str(chat.id)
    title = chat.title or chat.username or "Unknown Channel"
    username = f"@{chat.username}" if getattr(chat, "username", None) else "Private channel"

    await msg.reply_text(
        f"{EMOJI['check']} *Channel ID Found!*\n\n"
        f"*Name:* {title}\n"
        f"*Username:* `{username}`\n"
        f"*Channel ID:* `{cid}`\n\n"
        f"Now tap *Add Channel* and send this ID: `{cid}`",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=kb_main_menu(),
    )
    return STATE_MAIN


@require_admin
async def handle_add_channel(update: Update, context: ContextTypes.DEFAULT_TYPE, data: dict):
    """Receive and validate a channel ID/username, then store it."""
    text = (update.message.text or "").strip()
    bot: Bot = context.bot

    # Resolve the channel and verify bot has post permissions
    try:
        chat = await bot.get_chat(text)
        cid = str(chat.id)
        ch_name = chat.title or chat.username or cid

        # Test-send a blank to verify permissions (we immediately delete it)
        # Instead, check bot's member status
        member = await bot.get_chat_member(cid, bot.id)
        if member.status not in ("administrator", "creator"):
            raise PermissionError("Bot is not an admin in this channel.")

    except PermissionError as exc:
        await update.message.reply_text(
            f"{EMOJI['cross']} *Permission Error:* {exc}\n\nMake the bot an admin, then try again.",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=kb_back_only(),
        )
        return STATE_MAIN
    except (BadRequest, TelegramError) as exc:
        await update.message.reply_text(
            f"{EMOJI['cross']} *Telegram Error:* `{exc}`\n\nCheck the ID/username and try again.",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=kb_back_only(),
        )
        return STATE_MAIN

    channels = data.setdefault("channels", {})
    channels[cid] = ch_name
    save_data(data)

    await update.message.reply_text(
        f"{EMOJI['check']} *Channel Added!*\n\n`{ch_name}` (`{cid}`)",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=kb_main_menu(),
    )
    return STATE_MAIN


@require_admin
async def handle_remove_channel(update: Update, context: ContextTypes.DEFAULT_TYPE, data: dict):
    """Remove a channel from the stored list by its ID."""
    cid = (update.message.text or "").strip()
    channels = data.get("channels", {})

    if cid not in channels:
        await update.message.reply_text(
            f"{EMOJI['cross']} Channel ID `{cid}` not found in the list.",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=kb_back_only(),
        )
        return STATE_MAIN

    removed_name = channels.pop(cid)
    save_data(data)

    await update.message.reply_text(
        f"{EMOJI['check']} *Removed:* `{removed_name}` (`{cid}`)",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=kb_main_menu(),
    )
    return STATE_MAIN


@require_admin
async def handle_add_admin(update: Update, context: ContextTypes.DEFAULT_TYPE, data: dict):
    """Add a new admin by User ID (owner only)."""
    if not is_owner(update.effective_user.id):
        await update.message.reply_text("🚫 Owner only.", reply_markup=kb_back_only())
        return STATE_MAIN

    raw = (update.message.text or "").strip()
    try:
        new_id = int(raw)
    except ValueError:
        await update.message.reply_text(
            f"{EMOJI['cross']} Invalid User ID. Must be a number.",
            reply_markup=kb_back_only(),
        )
        return STATE_MAIN

    if new_id == OWNER_ID:
        await update.message.reply_text(
            f"{EMOJI['info']} That's the owner ID — already has full access.",
            reply_markup=kb_back_only(),
        )
        return STATE_MAIN

    admins: list = data.setdefault("admins", [])
    if new_id in admins:
        await update.message.reply_text(
            f"{EMOJI['info']} `{new_id}` is already an admin.",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=kb_back_only(),
        )
        return STATE_MAIN

    admins.append(new_id)
    save_data(data)

    await update.message.reply_text(
        f"{EMOJI['check']} Admin `{new_id}` added successfully.",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=kb_main_menu(),
    )
    return STATE_MAIN


@require_admin
async def handle_remove_admin(update: Update, context: ContextTypes.DEFAULT_TYPE, data: dict):
    """Remove an admin by User ID (owner only)."""
    if not is_owner(update.effective_user.id):
        await update.message.reply_text("🚫 Owner only.", reply_markup=kb_back_only())
        return STATE_MAIN

    raw = (update.message.text or "").strip()
    try:
        rem_id = int(raw)
    except ValueError:
        await update.message.reply_text(
            f"{EMOJI['cross']} Invalid User ID.",
            reply_markup=kb_back_only(),
        )
        return STATE_MAIN

    admins: list = data.get("admins", [])
    if rem_id not in admins:
        await update.message.reply_text(
            f"{EMOJI['cross']} `{rem_id}` is not in the admin list.",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=kb_back_only(),
        )
        return STATE_MAIN

    admins.remove(rem_id)
    save_data(data)

    await update.message.reply_text(
        f"{EMOJI['check']} Admin `{rem_id}` removed.",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=kb_main_menu(),
    )
    return STATE_MAIN


@require_admin
async def handle_broadcast_msg(update: Update, context: ContextTypes.DEFAULT_TYPE, data: dict):
    """Forward the admin's message to all target channels and report results."""
    targets: list[str] = context.user_data.get("bcast_targets", [])
    msg: Message = update.message
    bot: Bot = context.bot
    channels = data.get("channels", {})

    if not targets:
        await msg.reply_text(
            f"{EMOJI['cross']} No targets selected. Returning to menu.",
            reply_markup=kb_main_menu(),
        )
        return STATE_MAIN

    # Status message
    status_msg = await msg.reply_text(
        f"⏳ Broadcasting to {len(targets)} channel(s)…",
    )

    success, failed = [], []

    for cid in targets:
        try:
            await bot.forward_message(
                chat_id=cid,
                from_chat_id=msg.chat_id,
                message_id=msg.message_id,
            )
            success.append(channels.get(cid, cid))
            logger.info("Broadcast OK → %s", cid)
        except Forbidden:
            failed.append(f"{channels.get(cid, cid)} (bot blocked/kicked)")
            logger.warning("Broadcast FORBIDDEN → %s", cid)
        except BadRequest as exc:
            failed.append(f"{channels.get(cid, cid)} (bad request: {exc})")
            logger.warning("Broadcast BAD REQUEST → %s | %s", cid, exc)
        except TelegramError as exc:
            failed.append(f"{channels.get(cid, cid)} ({exc})")
            logger.error("Broadcast ERROR → %s | %s", cid, exc)

    # Build report
    lines = [f"{EMOJI['broadcast']} *Broadcast Report*\n"]
    if success:
        lines.append(f"{EMOJI['check']} *Sent to {len(success)}:*")
        lines.extend(f"  • {n}" for n in success)
    if failed:
        lines.append(f"\n{EMOJI['cross']} *Failed ({len(failed)}):*")
        lines.extend(f"  • {n}" for n in failed)

    await status_msg.edit_text(
        "\n".join(lines),
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=kb_main_menu(),
    )
    context.user_data.pop("bcast_targets", None)
    return STATE_MAIN


# ──────────────────────────────────────────────────────────────
#  FALLBACK / CANCEL
# ──────────────────────────────────────────────────────────────

async def cmd_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel current action and return to main menu."""
    context.user_data.clear()
    await update.message.reply_text(
        "↩️ Action cancelled. Returning to main menu.",
        reply_markup=kb_main_menu(),
    )
    return STATE_MAIN


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Log unexpected errors."""
    logger.error("Unhandled exception: %s", context.error, exc_info=True)


# ──────────────────────────────────────────────────────────────
#  APPLICATION BOOTSTRAP
# ──────────────────────────────────────────────────────────────

def build_application() -> Application:
    """Wire up all handlers and return the Application object."""
    app = Application.builder().token(BOT_TOKEN).build()

    # ConversationHandler covers all states
    conv = ConversationHandler(
        entry_points=[CommandHandler("start", cmd_start)],
        states={
            STATE_MAIN: [
                CallbackQueryHandler(handle_callback),
            ],
            STATE_ADD_CHANNEL: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_add_channel),
                CallbackQueryHandler(handle_callback),
            ],
            STATE_REMOVE_CHANNEL: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_remove_channel),
                CallbackQueryHandler(handle_callback),
            ],
            STATE_GET_CHANNEL_ID: [
                MessageHandler(
                    (filters.TEXT | filters.FORWARDED) & ~filters.COMMAND,
                    handle_get_channel_id,
                ),
                CallbackQueryHandler(handle_callback),
            ],
            STATE_ADD_ADMIN: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_add_admin),
                CallbackQueryHandler(handle_callback),
            ],
            STATE_REMOVE_ADMIN: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_remove_admin),
                CallbackQueryHandler(handle_callback),
            ],
            STATE_BROADCAST_SELECT: [
                CallbackQueryHandler(handle_callback),
            ],
            STATE_BROADCAST_MSG: [
                MessageHandler(
                    (filters.TEXT | filters.PHOTO | filters.VIDEO | filters.Document.ALL)
                    & ~filters.COMMAND,
                    handle_broadcast_msg,
                ),
                CallbackQueryHandler(handle_callback),
            ],
        },
        fallbacks=[CommandHandler("cancel", cmd_cancel)],
        allow_reentry=True,
        per_user=True,
        per_chat=True,
    )

    app.add_handler(conv)
    app.add_error_handler(error_handler)
    return app


def main():
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        logger.error("❌ BOT_TOKEN is not set. Edit the script or set the BOT_TOKEN env variable.")
        return
    if OWNER_ID == 0:
        logger.error("❌ OWNER_ID is not set. Edit the script or set the OWNER_ID env variable.")
        return

    logger.info("🚀 Starting X Auto Forward Bot…")
    app = build_application()
    app.run_polling(allowed_updates=["message", "callback_query"])


if __name__ == "__main__":
    main()