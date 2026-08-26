import os, json, logging, html, re, random
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatJoinRequest
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ChatJoinRequestHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode

BOT_TOKEN = "8868540804:AAEmU9LCSYXxQHRFE5-XRBVHaiZm_ie2SvQ"
ADMIN_IDS = [8498419947]
DATA_FILE = os.path.join(os.getcwd(), "data.json")
WELCOME_DIR = os.path.join(os.getcwd(), "welcome_files")
os.makedirs(WELCOME_DIR, exist_ok=True)

# ═══════ PREMIUM EMOJI MAPPING (44 EMOJIS) ═══════
PREMIUM_EMOJI_MAP = {
    "✅": ["6113743365826677162"],
    "📢": ["5931641120458018914"],
    "🧠": ["6271505894089952985"],
    "🔄": ["6242148104699648157"],
    "🥳": ["6242018680155152197"],
    "🦸‍♂": ["6242014252043868089"],
    "😄": ["6240160909231135849"],
    "🥏": ["6242113113601089103"],
    "❤️‍🔥": ["6242105356890151132"],
    "🔗": ["6116012762121377264"],
    "📎": ["6118262478875922552"],
    "🔺": ["5823288729191584314"],
    "📌": ["6068848489293422081"],
    "☄️": ["6068866888933317376"],
    "💁‍♀": ["6068998173198655021"],
    "💸": ["6332581398485931268"],
    "🔴": ["4992743110430687913"],
    "😉": ["6242158090498610126"],
    "😌": ["6242183396445918139"],
    "😍": ["6242440158180808121"],
    "🥰": ["6242062076504709224"],
    "📥": ["6330021121236145815"],
    "🔥": ["6332589971240655050"],
    "🚨": ["6334665239308537561"],
    "🚀": ["6332241232781121574"],
    "🔮": ["5042302287087666158"],
    "👑": ["5816539591812845173"],
    "🔛": ["5990026957419453239"],
    "👀": ["6053362469311617342"],
    "🤡": ["5323588426971227340"],
    "😀": ["6105039966788655018"],
    "🔼": ["6105002832501414007"],
    "🆘": ["5294057271226017876"],
    "🆑": ["5294125024335112026"],
    "🅾️": ["5292250898175633031"],
    "🅱️": ["5294194388056941995"],
    "🆎": ["5294467530797098107"],
    "🌹": ["6278173680493137560"],
    "💎": ["6204123844400124499"],
    "😂": ["6246887506621507085"],
    "📈": ["6093561301617875302"],
    "🎁": ["6093372095423585554"],
    "👆": ["6084832734071493634"],
    "💘": ["6266818250818983044"],
    "🎥": ["6264778055454036969"],
    "⭐": ["6138574830917655563"],
}

COLOR_MAP = {"blue": "primary", "green": "success", "red": "danger"}

DEFAULT_CAPTIONS = {
    "video": "✅NEW HACK How To Activate Hack✅\n  Pls Video Ko Pura Dekhna\n        ✅ Setup Video ✅\n\n✅ FULL NUMBER WORKING  ✅",
    "document": "📥 📌 🎥\n\n👆 DOWNLOAD & USE FAST 💸\n\n💎 MINIMUM DEPOSIT 300+ 💎\n\n🔥 FULL NUMBER WORKING 🔥",
    "photo": "✅✅✅✅✅✅✅✅\n\n✅ DOWNLOAD & USE FAST ✅\n\n✅ MINIMUM DEPOSIT 300+ ✅\n\n✅ FULL NUMBER WORKING  ✅",
    "voice": "✅ Voice Message ✅",
    "audio": "✅ Audio File ✅"
}

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

DEFAULT_DATA = {
    "welcome_contents": [],
    "users": [],
    "stats": {"approved": 0, "channels": {}},
    "pinned_content": None,
    "join_enabled": True
}

def load_data():
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r') as f:
                loaded = json.load(f)
                for key in DEFAULT_DATA:
                    if key not in loaded:
                        loaded[key] = DEFAULT_DATA[key]
                return loaded
    except Exception as e:
        logger.error(f"Load: {e}")
    return DEFAULT_DATA.copy()

def save_data(d):
    with open(DATA_FILE, 'w') as f:
        json.dump(d, f, indent=4)

data = load_data()
for key in DEFAULT_DATA:
    if key not in data:
        data[key] = DEFAULT_DATA[key]
save_data(data)

user_states = {}

def is_admin(uid):
    return uid in ADMIN_IDS

def format_quotes(text):
    if not text:
        return ""
    return re.sub(r'"([^"]*)"', r'<blockquote>\1</blockquote>', text)

# ═══════ PTB COLORED BUTTON ═══════
def colored_btn(text, url=None, callback=None, color="primary"):
    """PTB style colored button"""
    if url:
        return InlineKeyboardButton(text, url=url, style=color)
    return InlineKeyboardButton(text, callback_data=callback, style=color)

def build_keyboard_with_rows(buttons_list):
    keyboard = []
    buttons_by_row = {}
    for b in buttons_list:
        row = b.get("row", 0)
        if row not in buttons_by_row:
            buttons_by_row[row] = []
        buttons_by_row[row].append(InlineKeyboardButton(
            b['text'],
            url=b.get("url"),
            style=b.get("color", "primary")
        ))
    for row_num in sorted(buttons_by_row.keys()):
        keyboard.append(buttons_by_row[row_num])
    return InlineKeyboardMarkup(keyboard)

# ═══════ JOIN HANDLER ═══════
async def handle_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    join_request = update.chat_join_request
    user = join_request.from_user
    chat = join_request.chat
    uid, name, chat_id, channel = user.id, user.first_name, chat.id, chat.title
    
    if not data.get("join_enabled", True):
        logger.info(f"⏸️ JOIN OFF - Request pending: {name}")
        return
    
    ckey = str(chat_id)
    if "channels" not in data["stats"]:
        data["stats"]["channels"] = {}
    if ckey not in data["stats"]["channels"]:
        data["stats"]["channels"][ckey] = {"name": channel, "approved": 0}
    
    try:
        await join_request.approve()
        data["stats"]["approved"] += 1
        data["stats"]["channels"][ckey]["approved"] += 1
        if uid not in data["users"]:
            data["users"].append(uid)
        save_data(data)
        
        sent = await send_welcome_contents(context, uid, name, channel)
        if not sent:
            await context.bot.send_message(uid, f"✅ Welcome {html.escape(name)}! ✅")
    except Exception as e:
        logger.error(f"Join: {e}")

async def send_welcome_contents(context, chat_id, user_name="User", channel_name="Channel"):
    pin_sent = await send_pinned_content(context, chat_id, user_name, channel_name)
    contents = data.get("welcome_contents", [])
    sent = False
    
    if contents:
        for item in contents:
            try:
                markup = None
                if item.get("buttons"):
                    markup = build_keyboard_with_rows(item["buttons"])
                
                safe_name = html.escape(user_name) if user_name else "User"
                safe_channel = html.escape(channel_name) if channel_name else "Channel"
                
                if item["type"] == "text":
                    txt = item["content"].replace("{name}", safe_name).replace("{channel}", safe_channel)
                    txt = format_quotes(txt)
                    if not pin_sent:
                        await context.bot.send_message(chat_id, txt, reply_markup=markup, parse_mode=ParseMode.HTML)
                    sent = True
                    
                elif item["type"] in ["video","photo","document","voice","audio"]:
                    file_path = item.get("content", "")
                    if not os.path.exists(file_path):
                        continue
                    
                    cap = item.get("caption","").replace("{name}", safe_name).replace("{channel}", safe_channel)
                    cap = format_quotes(cap)
                    
                    with open(file_path, 'rb') as f:
                        if item["type"] == "video":
                            await context.bot.send_video(chat_id, f, caption=cap, reply_markup=markup)
                        elif item["type"] == "photo":
                            await context.bot.send_photo(chat_id, f, caption=cap, reply_markup=markup)
                        elif item["type"] == "document":
                            await context.bot.send_document(chat_id, f, caption=cap, reply_markup=markup)
                        elif item["type"] == "voice":
                            await context.bot.send_voice(chat_id, f, caption=cap)
                        elif item["type"] == "audio":
                            await context.bot.send_audio(chat_id, f, caption=cap)
                    sent = True
            except Exception as e:
                logger.error(f"Welcome send error: {e}")
    
    return sent or pin_sent

async def send_pinned_content(context, chat_id, user_name="User", channel_name="Channel"):
    pinned_idx = data.get("pinned_content")
    if pinned_idx is not None:
        contents = data.get("welcome_contents", [])
        if 0 <= pinned_idx < len(contents):
            item = contents[pinned_idx]
            try:
                safe_name = html.escape(user_name) if user_name else "User"
                safe_channel = html.escape(channel_name) if channel_name else "Channel"
                markup = None
                if item.get("buttons"):
                    markup = build_keyboard_with_rows(item["buttons"])
                
                if item["type"] == "text":
                    txt = item["content"].replace("{name}", safe_name).replace("{channel}", safe_channel)
                    txt = format_quotes(txt)
                    await context.bot.send_message(chat_id, f"📌 PINNED\n━━━━━━━━━━━━━\n{txt}", reply_markup=markup, parse_mode=ParseMode.HTML)
                    return True
                    
                elif item["type"] in ["video","photo","document","voice","audio"]:
                    file_path = item.get("content", "")
                    if not os.path.exists(file_path):
                        return False
                    
                    cap = item.get("caption","").replace("{name}", safe_name).replace("{channel}", safe_channel)
                    cap = format_quotes(cap)
                    
                    with open(file_path, 'rb') as f:
                        if item["type"] == "video":
                            await context.bot.send_video(chat_id, f, caption=cap, reply_markup=markup)
                        elif item["type"] == "photo":
                            await context.bot.send_photo(chat_id, f, caption=cap, reply_markup=markup)
                        elif item["type"] == "document":
                            await context.bot.send_document(chat_id, f, caption=cap, reply_markup=markup)
                        elif item["type"] == "voice":
                            await context.bot.send_voice(chat_id, f, caption=cap)
                        elif item["type"] == "audio":
                            await context.bot.send_audio(chat_id, f, caption=cap)
                    return True
            except Exception as e:
                logger.error(f"Pin: {e}")
    return False

# ═══════ COMMANDS ═══════
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id not in data["users"]:
        data["users"].append(user.id)
        save_data(data)
    
    if is_admin(user.id):
        join_status = "🟢 ON" if data.get("join_enabled", True) else "🔴 OFF"
        text = f"""╔══════════════════════╗\n║  🏆 <b>ALL-IN-ONE BOT</b>  ║\n╚══════════════════════╝\n👑 <b>Admin:</b> {user.first_name}\n📋 /welcome | /stats | /pin | /help\n\n📥 <b>Join Accept:</b> {join_status}\n\n<i>💎 44 Premium Emojis!</i>"""
        keyboard = [
            [colored_btn("START ✅", callback="join_on", color="success")],
            [colored_btn("OFF 🔴", callback="join_off", color="danger")],
            [colored_btn("Welcome", callback="welcome_menu", color="primary"), colored_btn("Stats", callback="stats", color="success")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    else:
        sent = await send_welcome_contents(context, user.id, user.first_name, "Channel")
        if not sent:
            await update.message.reply_text("✅ Bot Active! ✅")

async def pin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Admin only!")
        return
    contents = data.get("welcome_contents", [])
    if not contents:
        await update.message.reply_text("⚠️ Pehle /welcome se content add karo!")
        return
    t = "📌 <b>PIN CONTENT</b>\n\n"
    for i, item in enumerate(contents, 1):
        prev = item.get("content", item.get("filename", ""))[:30] if item["type"] == "text" else item.get("filename", item["type"].upper())
        t += f"  {i}. {'📝' if item['type']=='text' else '📁'} {prev}\n"
    t += "\n✏️ Number (0=unpin):"
    user_states[update.effective_user.id] = "pin_select"
    await update.message.reply_text(t, parse_mode=ParseMode.HTML)

async def unpin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Admin only!")
        return
    data["pinned_content"] = None
    save_data(data)
    await update.message.reply_text("✅ Pin removed!")

async def welcome_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Admin only!")
        return
    contents = data.get("welcome_contents", [])
    pinned = data.get("pinned_content")
    text = f"🎨 <b>WELCOME BUILDER</b>\n\n📝 Contents: {len(contents)}\n"
    if pinned is not None:
        text += f"📌 <b>PINNED:</b> #{pinned+1}\n"
    text += "\n"
    if contents:
        text += "<b>Current:</b>\n"
        for i, item in enumerate(contents, 1):
            t = item["type"]
            prev = item["content"][:30] if t == "text" else item.get("filename", t.upper())
            text += f"  {i}. {'📝' if t=='text' else '📁'} {prev} [{len(item.get('buttons',[]))}🔘] {'📌' if pinned==i-1 else ''}\n"
    
    keyboard = [
        [colored_btn("Add Text", callback="add_text", color="primary"), colored_btn("Add File", callback="add_file", color="success")],
        [colored_btn("Add Button", callback="btn_add", color="danger"), colored_btn("Pin Content", callback="pin_menu", color="primary")],
        [colored_btn("Edit", callback="edit_menu", color="danger"), colored_btn("Delete", callback="delete_menu", color="danger")],
        [colored_btn("Preview", callback="preview", color="success"), colored_btn("Clear All", callback="clear", color="danger")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)

async def stats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ch = data.get("stats", {}).get("channels", {})
    pinned = data.get("pinned_content")
    join_status = "🟢 ON" if data.get("join_enabled", True) else "🔴 OFF"
    text = f"📊 <b>STATS</b>\n\n✅ Approved: {data['stats']['approved']}\n📢 Channels: {len(ch)}\n📝 Contents: {len(data.get('welcome_contents',[]))}\n👥 Users: {len(data.get('users',[]))}\n💎 Emojis: {len(PREMIUM_EMOJI_MAP)}\n📥 Join: {join_status}"
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "📋 <b>COMMANDS ✅</b>\n\n/welcome | /stats | /pin | /unpin | /help\n\n📥 <b>START/OFF</b> se join on/off karo!\n\n💡 <b>Button Format:</b>\n<code>Text ✅ | URL/color/row:1</code>"
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)

# ═══════ CALLBACKS ═══════
async def handle_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    
    if not is_admin(uid):
        await query.message.reply_text("❌ Admin only!")
        return
    
    cmd = query.data
    contents = data.get("welcome_contents", [])
    
    if cmd == "join_on":
        data["join_enabled"] = True
        save_data(data)
        await query.message.reply_text("🟢 <b>Join Accept ON!</b>", parse_mode=ParseMode.HTML)
        return
    elif cmd == "join_off":
        data["join_enabled"] = False
        save_data(data)
        await query.message.reply_text("🔴 <b>Join Accept OFF!</b>", parse_mode=ParseMode.HTML)
        return
    elif cmd == "welcome_menu":
        await welcome_cmd(update, context)
    elif cmd == "stats":
        await stats_cmd(update, context)
    elif cmd == "pin_menu":
        if not contents:
            await query.message.reply_text("⚠️ Pehle content add!")
            return
        t = "📌 <b>PIN CONTENT</b>\n\n"
        for i, item in enumerate(contents, 1):
            prev = item.get("content", item.get("filename", ""))[:30] if item["type"] == "text" else item.get("filename", item["type"].upper())
            t += f"{i}. {'📝' if item['type']=='text' else '📁'} {prev}\n"
        t += "\nNumber (0=unpin):"
        user_states[uid] = "pin_select"
        await query.message.reply_text(t, parse_mode=ParseMode.HTML)
    elif cmd == "add_text":
        user_states[uid] = "adding_text"
        await query.message.reply_text("📝 Welcome text ✅\n\nUse {name} | {channel} | \"text\" for quotes\n\n/cancel")
    elif cmd == "add_file":
        user_states[uid] = "adding_file"
        await query.message.reply_text("📁 File bhejo 📁\n\nCaption likho - ✅😂🔥⭐ sab auto premium!\n\n/cancel")
    elif cmd == "btn_add":
        if not contents:
            await query.message.reply_text("⚠️ Pehle text add!")
            return
        user_states[uid] = "adding_button"
        t = "🔘 <b>ADD BUTTONS</b>\n\nKis content ke niche?\n\n"
        for i, item in enumerate(contents, 1):
            prev = item.get("content", item.get("filename", ""))[:30] if item["type"] == "text" else item.get("filename", item["type"].upper())
            t += f"<b>Content {i}:</b> {'📝' if item['type']=='text' else '📁'} {prev}\n"
        t += "\n<b>Format:</b>\n<code>Content Number\nButton1 ✅ | URL/blue/row:1\nButton2 🚀 | URL/green/row:1</code>\n\n/cancel"
        await query.message.reply_text(t, parse_mode=ParseMode.HTML)
    elif cmd == "edit_menu":
        if not contents:
            await query.message.reply_text("⚠️ No content!")
            return
        t = "✏️ <b>SELECT ✅</b>\n\n"
        for i, item in enumerate(contents, 1):
            t += f"{i}. {'📝' if item['type']=='text' else '📁'} {item.get('content',item.get('filename',''))[:30]}\n"
        t += "\nNumber:"
        user_states[uid] = "edit_select"
        await query.message.reply_text(t, parse_mode=ParseMode.HTML)
    elif cmd == "delete_menu":
        if not contents:
            await query.message.reply_text("⚠️ No content!")
            return
        t = "🗑️ <b>SELECT</b>\n\n"
        for i, item in enumerate(contents, 1):
            t += f"{i}. {'📝' if item['type']=='text' else '📁'} {item.get('content',item.get('filename',''))[:30]}\n"
        t += "\nNumber (0=cancel):"
        user_states[uid] = "delete_select"
        await query.message.reply_text(t, parse_mode=ParseMode.HTML)
    elif cmd == "preview":
        if not contents:
            await query.message.reply_text("⚠️ No content!")
            return
        t = "👁️ <b>PREVIEW</b>\n\n"
        for i, item in enumerate(contents, 1):
            t += f"{i}. {'📝' if item['type']=='text' else '📁'} {item.get('content',item.get('filename',''))[:50]}\n"
        await query.message.reply_text(t, parse_mode=ParseMode.HTML)
    elif cmd == "clear":
        data["welcome_contents"] = []
        data["pinned_content"] = None
        save_data(data)
        await query.message.reply_text("✅ Cleared!")

# ═══════ MESSAGE HANDLER ═══════
async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    uid = user.id
    
    if not is_admin(uid):
        # User → Admin forward
        if uid not in data["users"]:
            data["users"].append(uid)
            save_data(data)
        for aid in ADMIN_IDS:
            try:
                await update.message.forward(aid)
            except:
                pass
        await update.message.reply_text("✅ Message sent to admin!")
        return
    
    # Admin states
    state = user_states.get(uid, "")
    msg_text = update.message.text or ""
    
    if msg_text == '/cancel':
        user_states.pop(uid, None)
        await update.message.reply_text("❌ Cancelled\n/welcome")
        return
    
    if state == "pin_select":
        try:
            idx = int(msg_text.strip()) - 1
            contents = data.get("welcome_contents", [])
            if idx == -1:
                data["pinned_content"] = None
                save_data(data)
                await update.message.reply_text("✅ Pin removed!")
            elif 0 <= idx < len(contents):
                data["pinned_content"] = idx
                save_data(data)
                prev = contents[idx].get("content", contents[idx].get("filename", ""))[:30]
                await update.message.reply_text(f"📌 <b>PINNED!</b>\n\n#{idx+1}: {prev}...", parse_mode=ParseMode.HTML)
            else:
                await update.message.reply_text("❌ Invalid!")
        except:
            await update.message.reply_text("❌ Number!")
        user_states.pop(uid, None)
    
    elif state == "adding_text":
        data["welcome_contents"].append({"type": "text", "content": msg_text, "buttons": []})
        save_data(data)
        user_states.pop(uid, None)
        await update.message.reply_text("✅ Text added! /welcome")
    
    elif state == "adding_button":
        lines = msg_text.strip().split('\n')
        try:
            content_idx = int(lines[0].strip()) - 1
        except:
            await update.message.reply_text("❌ Pehli line: Content Number!\n\n/cancel")
            return
        contents = data.get("welcome_contents", [])
        if content_idx < 0 or content_idx >= len(contents):
            await update.message.reply_text("❌ Invalid Content Number!\n\n/cancel")
            return
        added = 0
        for line in lines[1:]:
            if '|' in line:
                parts = line.split('|', 1)
                rest = parts[1].strip()
                btn_text = parts[0].strip()
                btn_row = 0
                if '/row:' in rest:
                    up = rest.split('/row:')
                    rest = up[0].strip()
                    try:
                        btn_row = int(up[1].strip())
                    except:
                        pass
                if '/style:' in rest:
                    up = rest.split('/style:')
                    btn_url = up[0].strip()
                    c = up[1].strip().lower() if len(up) > 1 else "blue"
                else:
                    btn_url = rest
                    c = "blue"
                btn_color = COLOR_MAP.get(c, "primary")
                if "buttons" not in contents[content_idx]:
                    contents[content_idx]["buttons"] = []
                contents[content_idx]["buttons"].append({
                    "text": btn_text,
                    "url": btn_url,
                    "color": btn_color,
                    "row": btn_row
                })
                added += 1
        if added > 0:
            save_data(data)
            await update.message.reply_text(f"✅ {added} buttons added to Content {content_idx+1}!\n/welcome")
        else:
            await update.message.reply_text("❌ Koi button add nahi hua!\n\n/cancel")
        user_states.pop(uid, None)
    
    elif state == "edit_select":
        contents = data.get("welcome_contents", [])
        try:
            idx = int(msg_text.strip()) - 1
            if 0 <= idx < len(contents):
                user_states[uid] = f"edit_save_{idx}"
                await update.message.reply_text(f"✏️ Edit #{idx+1}:\n/cancel")
            else:
                user_states.pop(uid, None)
                await update.message.reply_text("❌ Invalid!")
        except:
            user_states.pop(uid, None)
    
    elif state.startswith("edit_save_"):
        idx = int(state.split("_")[-1])
        contents = data.get("welcome_contents", [])
        if 0 <= idx < len(contents) and msg_text:
            old = contents[idx]
            if old["type"] != "text" and os.path.exists(old.get("content", "")):
                os.remove(old["content"])
            contents[idx] = {"type": "text", "content": msg_text, "buttons": old.get("buttons", [])}
            save_data(data)
        user_states.pop(uid, None)
        await update.message.reply_text("✅ Updated! /welcome")
    
    elif state == "delete_select":
        contents = data.get("welcome_contents", [])
        try:
            idx = int(msg_text.strip()) - 1
            if idx == -1:
                await update.message.reply_text("❌ Cancelled")
            elif 0 <= idx < len(contents):
                if data.get("pinned_content") == idx:
                    data["pinned_content"] = None
                elif data.get("pinned_content") is not None and data["pinned_content"] > idx:
                    data["pinned_content"] -= 1
                deleted = contents.pop(idx)
                if deleted["type"] != "text" and os.path.exists(deleted.get("content", "")):
                    os.remove(deleted["content"])
                save_data(data)
                await update.message.reply_text("✅ Deleted! /welcome")
        except:
            pass
        user_states.pop(uid, None)
    
    else:
        # Admin broadcast
        users = data.get("users", [])
        if not users:
            await update.message.reply_text("⚠️ No users!")
            return
        sent = 0
        for target_uid in users:
            try:
                await update.message.copy(target_uid)
                sent += 1
            except:
                pass
        await update.message.reply_text(f"✅ Sent: {sent}/{len(users)}")

# ═══════ MAIN ═══════
def main():
    logger.info("🤖 ALL-IN-ONE BOT STARTING...")
    logger.info(f"💾 Data Path: {DATA_FILE}")
    logger.info(f"📁 Welcome Dir: {WELCOME_DIR}")
    
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                json.load(f)
        except:
            logger.warning("⚠️ Corrupt data.json deleted")
            os.remove(DATA_FILE)
            global data
            data = DEFAULT_DATA.copy()
            save_data(data)
    
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Join Request Handler
    application.add_handler(ChatJoinRequestHandler(handle_join))
    
    # Command Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("pin", pin_cmd))
    application.add_handler(CommandHandler("unpin", unpin_cmd))
    application.add_handler(CommandHandler("welcome", welcome_cmd))
    application.add_handler(CommandHandler("stats", stats_cmd))
    application.add_handler(CommandHandler("help", help_cmd))
    
    # Callback Handler
    application.add_handler(CallbackQueryHandler(handle_callbacks))
    
    # Message Handler
    application.add_handler(MessageHandler(filters.ALL, handle_messages))
    
    logger.info(f"✅ Bot starting...")
    logger.info(f"💎 Premium Emojis: {len(PREMIUM_EMOJI_MAP)} LOADED!")
    logger.info(f"📥 Join Accept: {'ON' if data.get('join_enabled', True) else 'OFF'}")
    logger.info(f"🎯 START/OFF BUTTONS ACTIVE!")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
