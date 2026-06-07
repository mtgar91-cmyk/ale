import os
import time
import logging
from typing import Optional

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)
from pyrogram import Client
from pyrogram.errors import PeerIdInvalid, ChannelInvalid, UsernameInvalid

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ══════════════════════════════════════════════════════════
#  إعدادات البوت
# ══════════════════════════════════════════════════════════
BOT_TOKEN = os.getenv(
    "BOT_TOKEN", "8495856594:AAEASdXfZV4bouc39CcNqdcw80gP6FfFDUw"
)
OWNER_ID = int(os.getenv("OWNER_ID", "6668195885"))
API_ID = int(os.getenv("API_ID", "32801472"))
API_HASH = os.getenv("API_HASH", "80947f2a32a377b50e2e55a83ae0cd9e")
SESSION_STR = (
    "AQE1hZwAjp43mUrFkh0fqr7eHAF3iUnVBVa4FSsW3F59dUkjucUPpoq5xB3e81CXc"
    "P9vpK2xdz6ttuiHEdW23mcron5A0vxDFHrJyJjuAuZmtgo_iuwTWFA4VQWxUp1LonE"
    "ygo5V6qfTM34OsJVScA9JxeZM2EQdaYoRFYjWTEqC-1FDftD-ubmOnJCEzWTYtwpfo"
    "OU7le1PDu_184M07sXsLwRquz85K55NS_Nxbf2BfSX8MWzhCYIJSzuxz5yr4xaehKO"
    "3IYMxlLAuMRpiuntJLjfbod97NS2f_9LNEnpzSclQxFwrf5L6qVIc8316Rg52P0T63"
    "6fkAKseLRgyFb6emx23ngAAAAHlNi4wAA"
)

RESULTS_PER_PAGE = 10
BOOK_COOLDOWN = 7  # ثواني

# ══════════════════════════════════════════════════════════
#  البيانات المدمجة
# ══════════════════════════════════════════════════════════
_DEFAULT_START = (
    "🌟 مرحبًا بك في بوت مكتبة الكتب\n\n"
    "📚 مكتبة رقمية مجانية تضم أكثر من مليون كتاب\n"
    "🔎 يمكنك البحث بسهولة بكتابة اسم الكتاب أو جزء منه\n\n"
    "🧭 تعليمات البحث الصحيحة:\n"
    "✔️ اكتب اسم الكتاب فقط\n"
    "✔️ أو جزء واضح من العنوان\n\n"
    "❌ أمثلة بحث غير صحيحة:\n"
    "✖️ كلمات عشوائية\n"
    "✖️ ج ..."
)

_DEFAULT_CHANNELS = [
    "@booksrrrkg", "@lovekotob", "@shiabooks_pdf", "@ktbnct",
    "@mansourr911", "@books2024", "@l_alnader2", "@justabookk",
    "@sharkelmoreeg", "@freebooksf", "@thefuturist2021", "@yasmeenbook",
    "@bookspsych", "@ahn2323", "@rayihat_alkutub", "@maktabty_Ar",
    "@katabatakatabata", "@falsafaANDma3refa", "@RamiTikrite", "@dewan55",
    "@ESSA98_Historical_Library", "@iqra2bk", "@pdf_novels",
    "@library_shia1", "@mybook22", "@books_dm",
    "@Golden_Islamic_Library_10_1987", "@lmatnawi", "@Psychologybookss",
    "@ahn1972", "@kutubunmufidatun", "@maktabat_almualafat_alkamila",
    "@taswkut", "@philosophybookss", "@alfekerpdf", "@library_313_sh",
    "@botonalktob", "@MarashiNajafiLibrary", "@hadithshia", "@asd213m",
    "@khalaf_books", "@salfibook", "@jvvfdch", "@gvxxghbbb", "@SBWWW",
    "@alnjafy", "@Den54321", "@muhammed_maher5", "@kashkool_mb", "@kotmn",
    "@T_Talabook", "@nusaxalktubub", "@kutubtabkhdz", "@mv12jr",
    "@fbd22_fbd22", "@books2023", "@PDF_Books2U", "@syriaaa22",
    "@fgh4321", "@christianlib", "@N_R_F4", "@brananamis", "@phychybook",
    "@altarikhwelsira", "@history_lib", "@a_pdf", "@Passion_1",
    "@ktb7sria", "@Ma7a6aat", "@diwan_shaer", "@SoffiaSufism",
    "@naktal62", "@almaktabat_alashearia", "@MandeanLibrary",
    "@politicalTA", "@pdf_novelsA",
    "@cybercecurity_bookscybercecurity", "@arabic17",
    "@phlisopherlibrary", "@soramnqraa", "@Almootnbe100", "@abo_abdu",
    "@BOOKlargelearn", "@svjajdjson", "@all5aa", "@bookdhr",
    "@ALmaeeahe", "@booksshiiet", "@omerokasha",
]

# حالة مشتركة في الذاكرة (تُعاد للقيم الافتراضية عند كل إعادة تشغيل)
_state = {
    "start_message": _DEFAULT_START,
    "channels": list(_DEFAULT_CHANNELS),
    "relay_chat_id": -1004292166163,
}

# كولداون الكتب: {(user_id, chat, msg_id): timestamp}
_book_cooldowns: dict = {}

# ══════════════════════════════════════════════════════════
#  دوال مساعدة
# ══════════════════════════════════════════════════════════


def get_relay_id() -> Optional[int]:
    return _state.get("relay_chat_id")


def check_cooldown(user_id: int, chat: str, msg_id: int) -> int:
    """يُعيد الثواني المتبقية (0 = لا كولداون)."""
    key = (user_id, chat, msg_id)
    last = _book_cooldowns.get(key, 0)
    remaining = int(BOOK_COOLDOWN - (time.time() - last))
    return max(remaining, 0)


def set_cooldown(user_id: int, chat: str, msg_id: int) -> None:
    key = (user_id, chat, msg_id)
    _book_cooldowns[key] = time.time()


# ══════════════════════════════════════════════════════════
#  Pyrogram
# ══════════════════════════════════════════════════════════
pyro: Optional[Client] = None


async def start_pyro(app: Application) -> None:
    global pyro
    pyro = Client(
        "book_session",
        api_id=API_ID,
        api_hash=API_HASH,
        session_string=SESSION_STR,
    )
    await pyro.start()
    logger.info("Pyrogram متصل — جاري تحميل المحادثات...")
    try:
        count = 0
        async for _ in pyro.get_dialogs():
            count += 1
        logger.info(f"تم تحميل {count} محادثة")
    except Exception as e:
        logger.warning(f"تعذّر تحميل الـ dialogs: {e}")

    relay_id = get_relay_id()
    if relay_id:
        try:
            chat = await pyro.get_chat(relay_id)
            logger.info(f"مجموعة الريلاي: {chat.title} ({relay_id})")
        except Exception as e:
            logger.warning(f"تعذّر تحميل الريلاي: {e}")


async def stop_pyro(app: Application) -> None:
    if pyro and pyro.is_connected:
        await pyro.stop()


def _extract_name(msg) -> str:
    """استخراج اسم الملف من رسالة Pyrogram."""
    if msg.document and msg.document.file_name:
        return msg.document.file_name
    if msg.caption:
        return msg.caption.split("\n")[0].strip()
    return "ملف"


async def _search_channel(ch: str, query: str, results: list) -> None:
    """البحث في قناة واحدة وإضافة النتائج للقائمة."""
    try:
        async for msg in pyro.search_messages(ch, query=query, limit=300):
            if msg.document or msg.video or msg.audio:
                results.append({
                    "name": _extract_name(msg)[:80],
                    "chat": ch,
                    "msg_id": msg.id,
                })
    except (PeerIdInvalid, ChannelInvalid, UsernameInvalid):
        logger.warning(f"لا يمكن الوصول: {ch}")
    except Exception as e:
        logger.error(f"خطأ في البحث ({ch}): {e}")


async def search_books(query: str, channels: list) -> list:
    if not pyro or not pyro.is_connected:
        return []
    results = []
    for ch in channels:
        await _search_channel(ch, query, results)
    return results


async def deliver_via_relay(
    user_id: int, chat: str, msg_id: int, bot
) -> tuple:
    relay_id = get_relay_id()
    if not relay_id:
        return False, "مجموعة الريلاي غير مضبوطة."

    if not pyro or not pyro.is_connected:
        return False, "عميل Pyrogram غير متصل."

    relay_msg_id = None
    try:
        relay_chat = await pyro.get_chat(relay_id)
        pyro_relay_id = relay_chat.id

        relay_msg = await pyro.copy_message(
            chat_id=pyro_relay_id,
            from_chat_id=chat,
            message_id=msg_id,
            caption="",
        )
        relay_msg_id = relay_msg.id

        await bot.copy_message(
            chat_id=user_id,
            from_chat_id=relay_id,
            message_id=relay_msg_id,
            caption="",
        )
        return True, ""

    except Exception as e:
        err = str(e)
        logger.error(f"خطأ في الريلاي [{chat}/{msg_id}]: {err}")
        return False, err

    finally:
        if relay_msg_id:
            try:
                await pyro.delete_messages(relay_id, relay_msg_id)
            except Exception:
                pass


# ══════════════════════════════════════════════════════════
#  لوحات المفاتيح
# ══════════════════════════════════════════════════════════
def main_keyboard(is_owner: bool = False) -> Optional[InlineKeyboardMarkup]:
    if not is_owner:
        return None
    relay_id = get_relay_id()
    relay_btn = (
        f"الريلاي: {relay_id}" if relay_id else "ضبط مجموعة الريلاي"
    )
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("تعديل رسالة الستارت", callback_data="edit_start")],
        [InlineKeyboardButton("ادارة القنوات", callback_data="manage_channels")],
        [InlineKeyboardButton(relay_btn, callback_data="set_relay")],
    ])


def channels_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("اضافة قناة", callback_data="add_channel")],
        [InlineKeyboardButton("حذف قناة", callback_data="delete_channel")],
        [InlineKeyboardButton("سجل القنوات", callback_data="list_channels")],
        [InlineKeyboardButton("رجوع", callback_data="back_main")],
    ])


def delete_channels_keyboard(channels: list) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(ch, callback_data=f"del:{ch}")]
        for ch in channels
    ]
    buttons.append([InlineKeyboardButton("رجوع", callback_data="manage_channels")])
    return InlineKeyboardMarkup(buttons)


def results_keyboard(results: list, page: int) -> InlineKeyboardMarkup:
    start = page * RESULTS_PER_PAGE
    end = start + RESULTS_PER_PAGE
    page_results = results[start:end]

    buttons = []
    for abs_idx, r in enumerate(page_results, start=start):
        label = f"{abs_idx + 1}. {r['name']}"[:64]
        buttons.append([
            InlineKeyboardButton(label, callback_data=f"send_book:{abs_idx}")
        ])

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("السابق", callback_data=f"page:{page - 1}"))
    if end < len(results):
        nav.append(InlineKeyboardButton("التالي", callback_data=f"page:{page + 1}"))
    if nav:
        buttons.append(nav)
    return InlineKeyboardMarkup(buttons)


# ══════════════════════════════════════════════════════════
#  حالات المحادثة
# ══════════════════════════════════════════════════════════
AWAIT_START_MSG, AWAIT_CHANNEL_LINK, AWAIT_RELAY_ID = range(3)


# ── /start ────────────────────────────────────────────────
async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    is_owner = update.effective_user.id == OWNER_ID
    await update.message.reply_text(
        _state["start_message"], reply_markup=main_keyboard(is_owner)
    )


# ── تعديل رسالة الستارت ───────────────────────────────────
async def cb_edit_start(
    update: Update, ctx: ContextTypes.DEFAULT_TYPE
) -> int:
    q = update.callback_query
    await q.answer()
    await q.message.reply_text(
        f"الرسالة الحالية:\n\n{_state['start_message']}\n\n"
        "ارسل النص الجديد او /cancel للالغاء:"
    )
    return AWAIT_START_MSG


async def received_start_msg(
    update: Update, ctx: ContextTypes.DEFAULT_TYPE
) -> int:
    _state["start_message"] = update.message.text
    await update.message.reply_text("تم تحديث رسالة الستارت!")
    return ConversationHandler.END


# ── ضبط الريلاي ───────────────────────────────────────────
async def cb_set_relay(
    update: Update, ctx: ContextTypes.DEFAULT_TYPE
) -> int:
    q = update.callback_query
    await q.answer()
    relay_id = get_relay_id()
    current = f"الريلاي الحالي: {relay_id}\n\n" if relay_id else ""
    await q.message.reply_text(
        f"{current}"
        "ارسل ID المجموعة (رقم يبدأ بـ -):\n"
        "مثال: -1001234567890\n\n"
        "او /cancel للالغاء"
    )
    return AWAIT_RELAY_ID


async def received_relay_id(
    update: Update, ctx: ContextTypes.DEFAULT_TYPE
) -> int:
    text = update.message.text.strip()
    try:
        relay_id = int(text)
    except ValueError:
        await update.message.reply_text(
            "المعرف غير صحيح. يجب ان يكون رقما مثل: -1001234567890\n\n"
            "حاول مجددا او /cancel للالغاء"
        )
        return AWAIT_RELAY_ID

    try:
        chat = await ctx.bot.get_chat(relay_id)
    except Exception as e:
        await update.message.reply_text(
            f"البوت لا يستطيع الوصول للمجموعة.\n"
            f"تاكد ان البوت مضاف اليها.\n\nالخطا: {e}\n\n"
            "حاول مجددا او /cancel"
        )
        return AWAIT_RELAY_ID

    _state["relay_chat_id"] = relay_id

    if pyro and pyro.is_connected:
        try:
            await pyro.get_chat(relay_id)
        except Exception as e:
            logger.warning(f"تعذر تحميل الريلاي في Pyrogram: {e}")

    await update.message.reply_text(
        f"تم ضبط مجموعة الريلاي!\n"
        f"المجموعة: {chat.title}\n"
        f"ID: {relay_id}"
    )
    return ConversationHandler.END


# ── إدارة القنوات ─────────────────────────────────────────
async def cb_manage_channels(
    update: Update, ctx: ContextTypes.DEFAULT_TYPE
) -> None:
    q = update.callback_query
    await q.answer()
    await q.message.edit_text(
        "ادارة القنوات المكتبية:", reply_markup=channels_menu_keyboard()
    )


async def cb_add_channel(
    update: Update, ctx: ContextTypes.DEFAULT_TYPE
) -> int:
    q = update.callback_query
    await q.answer()
    await q.message.reply_text(
        "ارسل يوزرنيم او رابط القناة:\n"
        "مثال: @mybookchannel\n\n"
        "او /cancel للالغاء"
    )
    return AWAIT_CHANNEL_LINK


async def received_channel_link(
    update: Update, ctx: ContextTypes.DEFAULT_TYPE
) -> int:
    text = update.message.text.strip()
    if text.startswith("https://t.me/"):
        username = "@" + text.replace("https://t.me/", "").split("/")[0]
    elif text.startswith("t.me/"):
        username = "@" + text.replace("t.me/", "").split("/")[0]
    elif not text.startswith("@"):
        username = "@" + text
    else:
        username = text

    if username in _state["channels"]:
        await update.message.reply_text("هذه القناة مضافة مسبقا!")
    else:
        _state["channels"].append(username)
        await update.message.reply_text(f"تمت اضافة القناة {username}")
    return ConversationHandler.END


async def cb_delete_channel(
    update: Update, ctx: ContextTypes.DEFAULT_TYPE
) -> None:
    q = update.callback_query
    await q.answer()
    if not _state["channels"]:
        await q.message.edit_text(
            "لا توجد قنوات مضافة.", reply_markup=channels_menu_keyboard()
        )
        return
    await q.message.edit_text(
        "اختر القناة للحذف:",
        reply_markup=delete_channels_keyboard(_state["channels"])
    )


async def cb_del_channel_confirm(
    update: Update, ctx: ContextTypes.DEFAULT_TYPE
) -> None:
    q = update.callback_query
    await q.answer()
    ch = q.data.split(":", 1)[1]
    if ch in _state["channels"]:
        _state["channels"].remove(ch)
        await q.message.edit_text(
            f"تم حذف {ch}!", reply_markup=channels_menu_keyboard()
        )
    else:
        await q.message.edit_text(
            "القناة غير موجودة.", reply_markup=channels_menu_keyboard()
        )


async def cb_list_channels(
    update: Update, ctx: ContextTypes.DEFAULT_TYPE
) -> None:
    q = update.callback_query
    await q.answer()
    if not _state["channels"]:
        text = "لا توجد قنوات مضافة."
    else:
        lines = "\n".join(
            f"{i + 1}. {ch}" for i, ch in enumerate(_state["channels"])
        )
        text = f"القنوات ({len(_state['channels'])}):\n\n{lines}"
    await q.message.edit_text(text, reply_markup=channels_menu_keyboard())


async def cb_back_main(
    update: Update, ctx: ContextTypes.DEFAULT_TYPE
) -> None:
    q = update.callback_query
    await q.answer()
    is_owner = q.from_user.id == OWNER_ID
    await q.message.edit_text(
        _state["start_message"], reply_markup=main_keyboard(is_owner)
    )


# ══════════════════════════════════════════════════════════
#  البحث
# ══════════════════════════════════════════════════════════
async def handle_search(
    update: Update, ctx: ContextTypes.DEFAULT_TYPE
) -> None:
    query = update.message.text.strip()
    if not query:
        return
    if not _state["channels"]:
        await update.message.reply_text("لا توجد قنوات مكتبية مضافة بعد.")
        return

    msg = await update.message.reply_text(f"جاري البحث عن: {query}...")
    results = await search_books(query, _state["channels"])

    ctx.user_data["search_results"] = results
    ctx.user_data["search_query"] = query

    if not results:
        await msg.edit_text(f"لم يتم العثور على نتائج لـ: {query}")
        return

    text = (
        f"نتائج البحث عن: {query}\n"
        f"عدد النتائج: {len(results)}\n\n"
        "اضغط على الكتاب لاستلامه:"
    )
    await msg.edit_text(text, reply_markup=results_keyboard(results, 0))


async def cb_page(
    update: Update, ctx: ContextTypes.DEFAULT_TYPE
) -> None:
    q = update.callback_query
    await q.answer()
    page = int(q.data.split(":")[1])

    results = ctx.user_data.get("search_results")
    query = ctx.user_data.get("search_query", "")
    if not results:
        await q.message.edit_text("انتهت الجلسة. ابحث مجددا.")
        return

    text = (
        f"نتائج البحث عن: {query}\n"
        f"عدد النتائج: {len(results)}\n\n"
        "اضغط على الكتاب لاستلامه:"
    )
    await q.message.edit_text(
        text, reply_markup=results_keyboard(results, page)
    )


# ══════════════════════════════════════════════════════════
#  إرسال الكتاب (مع كولداون 7 ثواني)
# ══════════════════════════════════════════════════════════
async def cb_send_book(
    update: Update, ctx: ContextTypes.DEFAULT_TYPE
) -> None:
    q = update.callback_query

    idx = int(q.data.split(":")[1])
    results = ctx.user_data.get("search_results", [])

    if not results or idx >= len(results):
        await q.answer("انتهت الجلسة. ابحث مجددا.", show_alert=True)
        return

    r = results[idx]
    user_id = q.from_user.id

    # ── فحص الكولداون ──────────────────────────────────
    remaining = check_cooldown(user_id, r["chat"], r["msg_id"])
    if remaining > 0:
        await q.answer(
            f"الكتاب مرسل قبل قليل، انتظر {remaining} ثانية.",
            show_alert=True,
        )
        return

    await q.answer("جاري الارسال...")
    set_cooldown(user_id, r["chat"], r["msg_id"])

    success, err = await deliver_via_relay(
        user_id, r["chat"], r["msg_id"], ctx.bot
    )
    if not success:
        if not get_relay_id():
            await q.message.reply_text(
                "مجموعة الريلاي غير مضبوطة.\n"
                "المالك يحتاج لضبطها من لوحة التحكم."
            )
        else:
            await q.message.reply_text(f"تعذر ارسال الملف.\nالسبب: {err}")


# ══════════════════════════════════════════════════════════
#  إلغاء
# ══════════════════════════════════════════════════════════
async def cancel(
    update: Update, ctx: ContextTypes.DEFAULT_TYPE
) -> int:
    await update.message.reply_text("تم الالغاء.")
    return ConversationHandler.END


# ══════════════════════════════════════════════════════════
#  التشغيل
# ══════════════════════════════════════════════════════════
def main() -> None:
    owner_filter = filters.User(OWNER_ID)

    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(start_pyro)
        .post_shutdown(stop_pyro)
        .build()
    )

    edit_start_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(cb_edit_start, pattern="^edit_start$")
        ],
        states={
            AWAIT_START_MSG: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND & owner_filter,
                    received_start_msg,
                )
            ]
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            CallbackQueryHandler(cb_manage_channels, pattern="^manage_channels$"),
            CallbackQueryHandler(cb_back_main, pattern="^back_main$"),
        ],
        per_message=False,
        allow_reentry=True,
    )

    add_channel_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(cb_add_channel, pattern="^add_channel$")
        ],
        states={
            AWAIT_CHANNEL_LINK: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND & owner_filter,
                    received_channel_link,
                )
            ]
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            CallbackQueryHandler(cb_manage_channels, pattern="^manage_channels$"),
            CallbackQueryHandler(cb_back_main, pattern="^back_main$"),
            CallbackQueryHandler(cb_delete_channel, pattern="^delete_channel$"),
            CallbackQueryHandler(cb_list_channels, pattern="^list_channels$"),
        ],
        per_message=False,
        allow_reentry=True,
    )

    set_relay_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(cb_set_relay, pattern="^set_relay$")
        ],
        states={
            AWAIT_RELAY_ID: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND & owner_filter,
                    received_relay_id,
                )
            ]
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            CallbackQueryHandler(cb_back_main, pattern="^back_main$"),
            CallbackQueryHandler(cb_manage_channels, pattern="^manage_channels$"),
        ],
        per_message=False,
        allow_reentry=True,
    )

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(edit_start_conv)
    app.add_handler(add_channel_conv)
    app.add_handler(set_relay_conv)
    app.add_handler(
        CallbackQueryHandler(cb_manage_channels, pattern="^manage_channels$")
    )
    app.add_handler(
        CallbackQueryHandler(cb_delete_channel, pattern="^delete_channel$")
    )
    app.add_handler(
        CallbackQueryHandler(cb_del_channel_confirm, pattern="^del:")
    )
    app.add_handler(
        CallbackQueryHandler(cb_list_channels, pattern="^list_channels$")
    )
    app.add_handler(
        CallbackQueryHandler(cb_back_main, pattern="^back_main$")
    )
    app.add_handler(CallbackQueryHandler(cb_page, pattern="^page:"))
    app.add_handler(CallbackQueryHandler(cb_send_book, pattern="^send_book:"))
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_search)
    )

    logger.info("البوت يعمل...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
