import os, json, logging, html, re, random
from datetime import datetime
from dotenv import load_dotenv
from telebot import TeleBot, types
from telebot.types import MessageEntity

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "8868540804:AAEmU9LCSYXxQHRFE5-XRBVHaiZm_ie2SvQ")
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

bot = TeleBot(BOT_TOKEN, threaded=True)

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
                for item in loaded.get("welcome_contents", []):
                    if "caption_entities" in item and item["caption_entities"]:
                        entities = []
                        for e_dict in item["caption_entities"]:
                            entities.append(MessageEntity(type=e_dict.get("type","custom_emoji"), offset=e_dict.get("offset",0), length=e_dict.get("length",1), custom_emoji_id=e_dict.get("custom_emoji_id","")))
                        item["caption_entities"] = entities
                for key in DEFAULT_DATA:
                    if key not in loaded: loaded[key] = DEFAULT_DATA[key]
                return loaded
    except Exception as e: logger.error(f"Load: {e}")
    return DEFAULT_DATA.copy()

def save_data(d):
    def conv(obj):
        if isinstance(obj, MessageEntity): return {"type": obj.type, "offset": obj.offset, "length": obj.length, "custom_emoji_id": obj.custom_emoji_id}
        if isinstance(obj, dict): return {k: conv(v) for k, v in obj.items()}
        if isinstance(obj, list): return [conv(i) for i in obj]
        return obj
    with open(DATA_FILE, 'w') as f: json.dump(conv(d), f, indent=4)

data = load_data()
for key in DEFAULT_DATA:
    if key not in data: data[key] = DEFAULT_DATA[key]
save_data(data)

user_states = {}

def is_admin(uid): return uid in ADMIN_IDS

def format_quotes(text):
    if not text: return ""
    return re.sub(r'"([^"]*)"', r'<blockquote>\1</blockquote>', text)

def convert_premium_emojis(text):
    if not text: return text, []
    entities = []
    for plan_emoji, emoji_ids in PREMIUM_EMOJI_MAP.items():
        start = 0
        while True:
            pos = text.find(plan_emoji, start)
            if pos == -1: break
            utf16_offset = len(text[:pos].encode('utf-16-le')) // 2
            utf16_length = len(plan_emoji.encode('utf-16-le')) // 2
            selected_id = random.choice(emoji_ids)
            entities.append(MessageEntity(type="custom_emoji", offset=utf16_offset, length=utf16_length, custom_emoji_id=selected_id))
            start = pos + len(plan_emoji)
    entities.sort(key=lambda x: x.offset)
    return text, entities

def extract_button_icon(text):
    for plan_emoji, emoji_ids in PREMIUM_EMOJI_MAP.items():
        if plan_emoji in text:
            icon_id = random.choice(emoji_ids)
            clean_text = text.replace(plan_emoji, "").strip()
            return clean_text, icon_id
    return text, None

# ⭐ FIXED: colored_btn - icon hai to style nahi, style hai to icon nahi
def colored_btn(text, url=None, callback=None, color="primary", icon_emoji_id=None):
    if icon_emoji_id:
        # Icon ke saath button (colored nahi, icon dikhega)
        if url:
            return types.InlineKeyboardButton(text, url=url, icon_custom_emoji_id=icon_emoji_id)
        return types.InlineKeyboardButton(text, callback_data=callback, icon_custom_emoji_id=icon_emoji_id)
    else:
        # Bina icon ke colored button
        if url:
            return types.InlineKeyboardButton(text, url=url, style=color)
        return types.InlineKeyboardButton(text, callback_data=callback, style=color)

def build_keyboard_with_rows(buttons_list):
    mrk = types.InlineKeyboardMarkup(row_width=2)
    buttons_by_row = {}
    for b in buttons_list:
        row = b.get("row", 0)
        if row not in buttons_by_row:
            buttons_by_row[row] = []
        icon_id = b.get("icon_emoji_id", None)
        buttons_by_row[row].append(colored_btn(b['text'], url=b["url"], color=b.get("color","primary"), icon_emoji_id=icon_id))
    for row_num in sorted(buttons_by_row.keys()):
        row_buttons = buttons_by_row[row_num]
        if len(row_buttons) == 1:
            mrk.add(row_buttons[0])
        else:
            mrk.add(*row_buttons)
    return mrk

def send(chat_id, text, reply_markup=None, **kwargs):
    if isinstance(text, str):
        clean_txt, emoji_entities = convert_premium_emojis(text)
        if emoji_entities:
            return bot.send_message(chat_id, clean_txt, entities=emoji_entities, reply_markup=reply_markup, **kwargs)
        return bot.send_message(chat_id, clean_txt, reply_markup=reply_markup, parse_mode="HTML", **kwargs)
    return bot.send_message(chat_id, text, reply_markup=reply_markup, **kwargs)

def send_html(chat_id, text, reply_markup=None):
    clean_txt, emoji_entities = convert_premium_emojis(text)
    if emoji_entities:
        return bot.send_message(chat_id, clean_txt, entities=emoji_entities, reply_markup=reply_markup, disable_web_page_preview=True)
    return bot.send_message(chat_id, clean_txt, reply_markup=reply_markup, parse_mode="HTML", disable_web_page_preview=True)

def send_media_with_caption(func, chat_id, file_id, caption="", reply_markup=None, **kwargs):
    if 'filename' in kwargs:
        kwargs['visible_file_name'] = kwargs.pop('filename')
    if caption:
        clean_cap, cap_entities = convert_premium_emojis(caption)
        if cap_entities:
            return func(chat_id, file_id, caption=clean_cap, caption_entities=cap_entities, reply_markup=reply_markup, **kwargs)
        return func(chat_id, file_id, caption=clean_cap, reply_markup=reply_markup, **kwargs)
    return func(chat_id, file_id, reply_markup=reply_markup, **kwargs)

def send_pinned_content(chat_id, user_name="User", channel_name="Channel"):
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
                    send(chat_id, f"📌 PINNED\n━━━━━━━━━━━━━\n{txt}", reply_markup=markup)
                    return True
                elif item["type"] in ["video","photo","document","voice","audio"]:
                    file_path = item.get("content", "")
                    if not os.path.exists(file_path): return False
                    cap = item.get("caption","").replace("{name}", safe_name).replace("{channel}", safe_channel)
                    cap = format_quotes(cap)
                    with open(file_path, 'rb') as f:
                        if item["type"] == "video":
                            send_media_with_caption(bot.send_video, chat_id, f, cap, reply_markup=markup)
                        elif item["type"] == "photo":
                            send_media_with_caption(bot.send_photo, chat_id, f, cap, reply_markup=markup)
                        elif item["type"] == "document":
                            send_media_with_caption(bot.send_document, chat_id, f, cap, reply_markup=markup, visible_file_name=item.get("filename","file"))
                        elif item["type"] == "voice":
                            send_media_with_caption(bot.send_voice, chat_id, f, cap)
                        elif item["type"] == "audio":
                            send_media_with_caption(bot.send_audio, chat_id, f, cap)
                    return True
            except Exception as e: logger.error(f"Pin: {e}")
    return False

def send_welcome_contents(chat_id, user_name="User", channel_name="Channel"):
    pin_sent = send_pinned_content(chat_id, user_name, channel_name)
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
                    if not pin_sent: send(chat_id, txt, reply_markup=markup)
                    sent = True
                elif item["type"] in ["video","photo","document","voice","audio"]:
                    file_path = item.get("content", "")
                    if not os.path.exists(file_path): continue
                    cap = item.get("caption","").replace("{name}", safe_name).replace("{channel}", safe_channel)
                    cap = format_quotes(cap)
                    with open(file_path, 'rb') as f:
                        if item["type"] == "video":
                            send_media_with_caption(bot.send_video, chat_id, f, cap, reply_markup=markup)
                        elif item["type"] == "photo":
                            send_media_with_caption(bot.send_photo, chat_id, f, cap, reply_markup=markup)
                        elif item["type"] == "document":
                            send_media_with_caption(bot.send_document, chat_id, f, cap, reply_markup=markup, visible_file_name=item.get("filename","file"))
                        elif item["type"] == "voice":
                            send_media_with_caption(bot.send_voice, chat_id, f, cap)
                        elif item["type"] == "audio":
                            send_media_with_caption(bot.send_audio, chat_id, f, cap)
                    sent = True
            except Exception as e: logger.error(f"Welcome: {e}")
    return sent or pin_sent

# ═══════ JOIN HANDLER ═══════
@bot.chat_join_request_handler()
def handle_join(update: types.ChatJoinRequest):
    user = update.from_user; chat = update.chat
    uid, name, chat_id, channel = user.id, user.first_name, chat.id, chat.title
    ckey = str(chat_id)
    
    if not data.get("join_enabled", True):
        logger.info(f"⏸️ JOIN OFF - Request pending: {name}")
        return
    
    if "channels" not in data["stats"]: data["stats"]["channels"] = {}
    if ckey not in data["stats"]["channels"]: data["stats"]["channels"][ckey] = {"name": channel, "approved": 0}
    
    try:
        bot.approve_chat_join_request(chat_id, uid)
        data["stats"]["approved"] += 1; data["stats"]["channels"][ckey]["approved"] += 1
        if uid not in data["users"]: data["users"].append(uid)
        save_data(data)
        sent = send_welcome_contents(uid, name, channel)
        if not sent: send(uid, f"✅ Welcome {html.escape(name)}! ✅")
    except Exception as e:
        logger.error(f"Join: {e}")

# ═══════ COMMANDS ═══════
@bot.message_handler(commands=['start'])
def start(message: types.Message):
    user = message.from_user
    if user.id not in data["users"]: data["users"].append(user.id); save_data(data)
    
    if is_admin(user.id):
        join_status = "🟢 ON" if data.get("join_enabled", True) else "🔴 OFF"
        text = f"""╔══════════════════════╗\n║  🏆 <b>ALL-IN-ONE BOT</b>  ║\n╚══════════════════════╝\n👑 <b>Admin:</b> {user.first_name}\n📋 /welcome | /stats | /pin | /help\n\n📥 <b>Join Accept:</b> {join_status}\n\n<i>💡 Admin = Normal | Forward = Forward Tag</i>\n<i>💎 44 Premium Emojis!</i>"""
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            colored_btn("START ✅", callback="join_on", color="success", icon_emoji_id="6113743365826677162"),
            colored_btn("OFF 🔴", callback="join_off", color="danger", icon_emoji_id="4992743110430687913")
        )
        markup.add(colored_btn("Welcome", callback="welcome_menu", color="primary"), colored_btn("Stats", callback="stats", color="success"))
        send_html(message.chat.id, text, reply_markup=markup)
    else:
        sent = send_welcome_contents(message.chat.id, user.first_name, "Channel")
        if not sent: send(message.chat.id, "✅ Bot Active! ✅")

@bot.message_handler(commands=['pin'])
def pin_cmd(message: types.Message):
    if not is_admin(message.from_user.id): send(message.chat.id, "❌ Admin only!"); return
    contents = data.get("welcome_contents", [])
    if not contents: send(message.chat.id, "⚠️ Pehle /welcome se content add karo!"); return
    t = "📌 <b>PIN CONTENT</b>\n\n"
    for i, item in enumerate(contents, 1):
        prev = item.get("content", item.get("filename", ""))[:30] if item["type"] == "text" else item.get("filename", item["type"].upper())
        t += f"  {i}. {'📝' if item['type']=='text' else '📁'} {prev}\n"
    t += "\n✏️ Number (0=unpin):"
    user_states[message.from_user.id] = "pin_select"; send_html(message.chat.id, t)

@bot.message_handler(commands=['unpin'])
def unpin_cmd(message: types.Message):
    if not is_admin(message.from_user.id): send(message.chat.id, "❌ Admin only!"); return
    data["pinned_content"] = None; save_data(data); send(message.chat.id, "✅ Pin removed!")

@bot.message_handler(commands=['welcome'])
def welcome_cmd(message: types.Message):
    if not is_admin(message.from_user.id): send(message.chat.id, "❌ Admin only!"); return
    contents = data.get("welcome_contents", []); pinned = data.get("pinned_content")
    text = f"🎨 <b>WELCOME BUILDER</b>\n\n📝 Contents: {len(contents)}\n"
    if pinned is not None: text += f"📌 <b>PINNED:</b> #{pinned+1}\n"
    text += "\n"
    if contents:
        text += "<b>Current:</b>\n"
        for i, item in enumerate(contents, 1):
            t = item["type"]; prev = item["content"][:30] if t == "text" else item.get("filename", t.upper())
            text += f"  {i}. {'📝' if t=='text' else '📁'} {prev} [{len(item.get('buttons',[]))}🔘] {'📌' if pinned==i-1 else ''}\n"
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(colored_btn("Add Text", callback="add_text", color="primary"), colored_btn("Add File", callback="add_file", color="success"))
    markup.add(colored_btn("Add Button", callback="btn_add", color="danger"), colored_btn("Pin Content", callback="pin_menu", color="primary"))
    markup.add(colored_btn("Edit", callback="edit_menu", color="danger"), colored_btn("Delete", callback="delete_menu", color="danger"))
    markup.add(colored_btn("Preview", callback="preview", color="success"), colored_btn("Clear All", callback="clear", color="danger"))
    send_html(message.chat.id, text, reply_markup=markup)

@bot.message_handler(commands=['stats'])
def stats_cmd(message: types.Message):
    ch = data.get("stats", {}).get("channels", {}); pinned = data.get("pinned_content")
    join_status = "🟢 ON" if data.get("join_enabled", True) else "🔴 OFF"
    text = f"📊 <b>STATS</b>\n\n✅ Approved: {data['stats']['approved']}\n📢 Channels: {len(ch)}\n📝 Contents: {len(data.get('welcome_contents',[]))}\n👥 Users: {len(data.get('users',[]))}\n💎 Emojis: {len(PREMIUM_EMOJI_MAP)}\n📥 Join: {join_status}"
    if pinned is not None: text += f"\n📌 Pinned: #{pinned+1}"
    send_html(message.chat.id, text)

@bot.message_handler(commands=['help'])
def help_cmd(message: types.Message):
    text = "📋 <b>COMMANDS ✅</b>\n\n/welcome | /stats | /pin | /unpin | /help\n\n📥 <b>START/OFF Buttons</b> se join on/off karo!\n\n💡 <b>Button Format:</b>\n<code>Text ✅ | URL/color/row:1</code>"
    send_html(message.chat.id, text)

# ═══════ CALLBACKS ═══════
@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call: types.CallbackQuery):
    uid = call.from_user.id
    if not is_admin(uid): bot.answer_callback_query(call.id, "❌ Admin only!", show_alert=True); return
    cmd = call.data; contents = data.get("welcome_contents", []); bot.answer_callback_query(call.id)
    
    if cmd == "join_on":
        data["join_enabled"] = True; save_data(data)
        send(call.message.chat.id, "🟢 <b>Join Accept ON!</b>")
        return
    elif cmd == "join_off":
        data["join_enabled"] = False; save_data(data)
        send(call.message.chat.id, "🔴 <b>Join Accept OFF!</b>")
        return
    
    if cmd == "welcome_menu": welcome_cmd(call.message)
    elif cmd == "stats": stats_cmd(call.message)
    elif cmd == "pin_menu":
        if not contents: send(call.message.chat.id, "⚠️ Pehle content add!"); return
        t = "📌 <b>PIN CONTENT</b>\n\n"
        for i, item in enumerate(contents, 1):
            prev = item.get("content", item.get("filename", ""))[:30] if item["type"] == "text" else item.get("filename", item["type"].upper())
            t += f"{i}. {'📝' if item['type']=='text' else '📁'} {prev}\n"
        t += "\nNumber (0=unpin):"; user_states[uid] = "pin_select"; send_html(call.message.chat.id, t)
    elif cmd == "add_text": user_states[uid] = "adding_text"; send_html(call.message.chat.id, "📝 Welcome text ✅\n\nUse {name} | {channel} | \"text\" for quotes\n\n/cancel")
    elif cmd == "add_file": user_states[uid] = "adding_file"; send_html(call.message.chat.id, "📁 File bhejo 📁\n\nCaption likho - ✅😂🔥⭐ sab auto premium!\n\n/cancel")
    elif cmd == "btn_add":
        if not contents: send(call.message.chat.id, "⚠️ Pehle text add!"); return
        user_states[uid] = "adding_button"
        t = "🔘 <b>ADD BUTTONS</b>\n\nKis content ke niche?\n\n"
        for i, item in enumerate(contents, 1):
            prev = item.get("content", item.get("filename", ""))[:30] if item["type"] == "text" else item.get("filename", item["type"].upper())
            t += f"<b>Content {i}:</b> {'📝' if item['type']=='text' else '📁'} {prev}\n"
        t += "\n<b>Format:</b>\n<code>Content Number\nButton1 ✅ | URL/blue/row:1\nButton2 🚀 | URL/green/row:1</code>\n\n/cancel"
        send_html(call.message.chat.id, t)
    elif cmd == "edit_menu":
        if not contents: send(call.message.chat.id, "⚠️ No content!"); return
        t = "✏️ <b>SELECT ✅</b>\n\n"
        for i, item in enumerate(contents, 1): t += f"{i}. {'📝' if item['type']=='text' else '📁'} {item.get('content',item.get('filename',''))[:30]}\n"
        t += "\nNumber:"; user_states[uid] = "edit_select"; send_html(call.message.chat.id, t)
    elif cmd == "delete_menu":
        if not contents: send(call.message.chat.id, "⚠️ No content!"); return
        t = "🗑️ <b>SELECT</b>\n\n"
        for i, item in enumerate(contents, 1): t += f"{i}. {'📝' if item['type']=='text' else '📁'} {item.get('content',item.get('filename',''))[:30]}\n"
        t += "\nNumber (0=cancel):"; user_states[uid] = "delete_select"; send_html(call.message.chat.id, t)
    elif cmd == "preview":
        if not contents: send(call.message.chat.id, "⚠️ No content!"); return
        t = "👁️ <b>PREVIEW</b>\n\n"
        for i, item in enumerate(contents, 1): t += f"{i}. {'📝' if item['type']=='text' else '📁'} {item.get('content',item.get('filename',''))[:50]}\n"
        send_html(call.message.chat.id, t)
    elif cmd == "clear": data["welcome_contents"] = []; data["pinned_content"] = None; save_data(data); send(call.message.chat.id, "✅ Cleared!")

# ═══════ FILE UPLOAD ═══════
@bot.message_handler(content_types=['video', 'photo', 'document', 'voice', 'audio'], func=lambda m: is_admin(m.from_user.id) and user_states.get(m.from_user.id) == "adding_file")
def handle_file_upload(message: types.Message):
    uid = message.from_user.id; fname = f"w_{datetime.now():%H%M%S}"; saved = False
    new_item = {"type": "", "content": "", "buttons": []}; admin_caption = message.caption
    try:
        if message.video:
            fi = bot.get_file(message.video.file_id); d = bot.download_file(fi.file_path)
            fp = os.path.join(WELCOME_DIR, f"{fname}.mp4")
            with open(fp, 'wb') as f: f.write(d)
            cap = admin_caption if admin_caption else DEFAULT_CAPTIONS["video"]
            clean_cap, cap_entities = convert_premium_emojis(cap)
            new_item = {"type": "video", "content": fp, "caption": clean_cap, "caption_entities": cap_entities, "buttons": []}; saved = True
        elif message.photo:
            fi = bot.get_file(message.photo[-1].file_id); d = bot.download_file(fi.file_path)
            fp = os.path.join(WELCOME_DIR, f"{fname}.jpg")
            with open(fp, 'wb') as f: f.write(d)
            cap = admin_caption if admin_caption else DEFAULT_CAPTIONS["photo"]
            clean_cap, cap_entities = convert_premium_emojis(cap)
            new_item = {"type": "photo", "content": fp, "caption": clean_cap, "caption_entities": cap_entities, "buttons": []}; saved = True
        elif message.document:
            fi = bot.get_file(message.document.file_id); d = bot.download_file(fi.file_path)
            ext = os.path.splitext(message.document.file_name or ".file")[1]
            fp = os.path.join(WELCOME_DIR, f"{fname}{ext}")
            with open(fp, 'wb') as f: f.write(d)
            cap = admin_caption if admin_caption else DEFAULT_CAPTIONS["document"]
            clean_cap, cap_entities = convert_premium_emojis(cap)
            new_item = {"type": "document", "content": fp, "filename": message.document.file_name or "file", "caption": clean_cap, "caption_entities": cap_entities, "buttons": []}; saved = True
        elif message.voice:
            fi = bot.get_file(message.voice.file_id); d = bot.download_file(fi.file_path)
            fp = os.path.join(WELCOME_DIR, f"{fname}.ogg")
            with open(fp, 'wb') as f: f.write(d)
            cap = admin_caption if admin_caption else DEFAULT_CAPTIONS["voice"]
            clean_cap, cap_entities = convert_premium_emojis(cap)
            new_item = {"type": "voice", "content": fp, "caption": clean_cap, "caption_entities": cap_entities, "buttons": []}; saved = True
        elif message.audio:
            fi = bot.get_file(message.audio.file_id); d = bot.download_file(fi.file_path)
            fp = os.path.join(WELCOME_DIR, f"{fname}.mp3")
            with open(fp, 'wb') as f: f.write(d)
            cap = admin_caption if admin_caption else DEFAULT_CAPTIONS["audio"]
            clean_cap, cap_entities = convert_premium_emojis(cap)
            new_item = {"type": "audio", "content": fp, "caption": clean_cap, "caption_entities": cap_entities, "buttons": []}; saved = True
    except Exception as e: logger.error(f"File: {e}")
    if saved: data["welcome_contents"].append(new_item); save_data(data); user_states.pop(uid, None); send(message.chat.id, "✅ File added! /welcome")
    else: user_states.pop(uid, None); send(message.chat.id, "❌ Failed!")

# ═══════ STATES HANDLER ═══════
@bot.message_handler(func=lambda m: is_admin(m.from_user.id) and user_states.get(m.from_user.id) in ["adding_text", "adding_button", "edit_select", "delete_select", "pin_select"])
def handle_states(message: types.Message):
    uid = message.from_user.id; state = user_states.get(uid, "")
    if message.text == '/cancel': user_states.pop(uid, None); send(message.chat.id, "❌ Cancelled\n/welcome"); return
    
    if state == "pin_select":
        try:
            idx = int(message.text.strip()) - 1; contents = data.get("welcome_contents", [])
            if idx == -1: data["pinned_content"] = None; save_data(data); send(message.chat.id, "✅ Pin removed!")
            elif 0 <= idx < len(contents):
                data["pinned_content"] = idx; save_data(data)
                prev = contents[idx].get("content", contents[idx].get("filename", ""))[:30]
                send(message.chat.id, f"📌 <b>PINNED!</b>\n\n#{idx+1}: {prev}...")
            else: send(message.chat.id, "❌ Invalid!")
        except: send(message.chat.id, "❌ Number!")
        user_states.pop(uid, None)
    elif state == "adding_text":
        data["welcome_contents"].append({"type": "text", "content": message.text, "buttons": []})
        save_data(data); user_states.pop(uid, None); send(message.chat.id, "✅ Text added! /welcome")
    elif state == "adding_button":
        lines = message.text.strip().split('\n')
        try: content_idx = int(lines[0].strip()) - 1
        except: send(message.chat.id, "❌ Pehli line: Content Number!\n\n/cancel"); return
        contents = data.get("welcome_contents", [])
        if content_idx < 0 or content_idx >= len(contents): send(message.chat.id, "❌ Invalid Content Number!\n\n/cancel"); return
        added = 0
        for line in lines[1:]:
            if '|' in line:
                parts = line.split('|', 1); rest = parts[1].strip()
                btn_text = parts[0].strip()
                btn_row = 0
                if '/row:' in rest:
                    up = rest.split('/row:'); rest = up[0].strip()
                    try: btn_row = int(up[1].strip())
                    except: pass
                if '/style:' in rest:
                    up = rest.split('/style:'); btn_url = up[0].strip()
                    c = up[1].strip().lower() if len(up) > 1 else "blue"
                else: btn_url = rest; c = "blue"
                btn_color = COLOR_MAP.get(c, "primary")
                if "buttons" not in contents[content_idx]: contents[content_idx]["buttons"] = []
                clean_btn_text, icon_emoji_id = extract_button_icon(btn_text)
                contents[content_idx]["buttons"].append({
                    "text": clean_btn_text,
                    "url": btn_url,
                    "color": btn_color,
                    "icon_emoji_id": icon_emoji_id,
                    "row": btn_row
                })
                added += 1
        if added > 0: save_data(data); send(message.chat.id, f"✅ {added} buttons added to Content {content_idx+1}!\n/welcome")
        else: send(message.chat.id, "❌ Koi button add nahi hua!\n\n/cancel")
        user_states.pop(uid, None)
    elif state == "edit_select":
        contents = data.get("welcome_contents", [])
        try:
            idx = int(message.text.strip()) - 1
            if 0 <= idx < len(contents): user_states[uid] = f"edit_save_{idx}"; send(message.chat.id, f"✏️ Edit #{idx+1}:\n/cancel")
            else: user_states.pop(uid, None); send(message.chat.id, "❌ Invalid!")
        except: user_states.pop(uid, None)
    elif state.startswith("edit_save_"):
        idx = int(state.split("_")[-1]); contents = data.get("welcome_contents", [])
        if 0 <= idx < len(contents) and message.text:
            old = contents[idx]
            if old["type"] != "text" and os.path.exists(old.get("content", "")): os.remove(old["content"])
            contents[idx] = {"type": "text", "content": message.text, "buttons": old.get("buttons", [])}; save_data(data)
        user_states.pop(uid, None); send(message.chat.id, "✅ Updated! /welcome")
    elif state == "delete_select":
        contents = data.get("welcome_contents", [])
        try:
            idx = int(message.text.strip()) - 1
            if idx == -1: send(message.chat.id, "❌ Cancelled")
            elif 0 <= idx < len(contents):
                if data.get("pinned_content") == idx: data["pinned_content"] = None
                elif data.get("pinned_content") is not None and data["pinned_content"] > idx: data["pinned_content"] -= 1
                deleted = contents.pop(idx)
                if deleted["type"] != "text" and os.path.exists(deleted.get("content", "")): os.remove(deleted["content"])
                save_data(data); send(message.chat.id, "✅ Deleted! /welcome")
        except: pass
        user_states.pop(uid, None)

# ═══════ USER → ADMIN ═══════
@bot.message_handler(content_types=['text', 'photo', 'video', 'document', 'voice', 'audio', 'sticker', 'animation'], func=lambda m: not is_admin(m.from_user.id))
def user_to_admin(message: types.Message):
    user = message.from_user
    if user.id not in data["users"]: data["users"].append(user.id); save_data(data)
    for aid in ADMIN_IDS:
        try: bot.forward_message(aid, message.chat.id, message.message_id)
        except: pass
    try: send(message.chat.id, "✅ Message sent to admin!")
    except: pass

# ═══════ ADMIN BROADCAST ═══════
@bot.message_handler(content_types=['text', 'photo', 'video', 'document', 'voice', 'audio', 'sticker', 'animation'], func=lambda m: is_admin(m.from_user.id) and not (m.text and m.text.startswith('/')))
def admin_broadcast(message: types.Message):
    users = data.get("users", [])
    if not users: send(message.chat.id, "⚠️ No users!"); return
    sent = 0; failed = 0; blocked_users = []
    is_forwarded = message.forward_from or message.forward_from_chat
    
    for uid in users:
        try:
            if is_forwarded:
                bot.forward_message(uid, message.chat.id, message.message_id)
            else:
                if message.text:
                    send(uid, message.text)
                elif message.photo:
                    cap = message.caption or ""
                    send_media_with_caption(bot.send_photo, uid, message.photo[-1].file_id, cap)
                elif message.video:
                    cap = message.caption or ""
                    send_media_with_caption(bot.send_video, uid, message.video.file_id, cap)
                elif message.document:
                    cap = message.caption or ""
                    send_media_with_caption(bot.send_document, uid, message.document.file_id, cap)
                elif message.voice:
                    cap = message.caption or ""
                    send_media_with_caption(bot.send_voice, uid, message.voice.file_id, cap)
                elif message.audio:
                    cap = message.caption or ""
                    send_media_with_caption(bot.send_audio, uid, message.audio.file_id, cap)
                elif message.sticker:
                    bot.send_sticker(uid, message.sticker.file_id)
                elif message.animation:
                    cap = message.caption or ""
                    send_media_with_caption(bot.send_animation, uid, message.animation.file_id, cap)
            sent += 1
        except Exception as e:
            error_msg = str(e)
            if "Forbidden" in error_msg or "blocked" in error_msg.lower(): blocked_users.append(uid)
            else: logger.error(f"BC {uid}: {e}")
            failed += 1
    
    if blocked_users:
        for buid in blocked_users:
            if buid in data["users"]: data["users"].remove(buid)
        save_data(data)
    
    report = f"✅ Sent: {sent}"
    if failed > 0: report += f"\n❌ Failed: {failed}"
    if blocked_users: report += f"\n🚫 Blocked (removed): {len(blocked_users)}"
    send_html(message.chat.id, report)

# ═══════ MAIN ═══════
def main():
    logger.info("🤖 ALL-IN-ONE BOT STARTING...")
    logger.info(f"💾 Data Path: {DATA_FILE}")
    logger.info(f"📁 Welcome Dir: {WELCOME_DIR}")
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f: json.load(f)
        except:
            logger.warning("⚠️ Corrupt data.json deleted")
            os.remove(DATA_FILE)
            global data; data = DEFAULT_DATA.copy(); save_data(data)
    bot_info = bot.get_me()
    logger.info(f"✅ @{bot_info.username}")
    logger.info(f"💎 Premium Emojis: {len(PREMIUM_EMOJI_MAP)} LOADED!")
    logger.info(f"📥 Join Accept: {'ON' if data.get('join_enabled', True) else 'OFF'}")
    logger.info(f"🎯 START/OFF BUTTONS ACTIVE!")
    bot.infinity_polling(timeout=10, long_polling_timeout=5)

if __name__ == "__main__":
    main()
