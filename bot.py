import sqlite3
import yaml
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import asyncio, datetime

# 读取配置文件
with open("config.yaml", 'r', encoding='utf-8') as file:
    config = yaml.safe_load(file)

API_ID = config['api_id']
API_HASH = config['api_hash']
TOKEN = config['bot_token']
YOUR_USER_ID = config['admin_user_id']

# 初始化SQLite数据库
conn = sqlite3.connect('banned_users.db')
cursor = conn.cursor()

# 创建禁言用户表
cursor.execute('''
CREATE TABLE IF NOT EXISTS banned_users (
    user_id INTEGER PRIMARY KEY
)
''')
conn.commit()

VERSION = "v1.0"
# Dictionary to store the mapping between message_id and the original sender's user_id
message_sender_map = {}
# Dictionary to store the mapping between user_id and username
usernames = {}
fullnames = {}
# List to keep track of recent chatters
recent_chatters = []

user_last_interaction = {}
user_timers = {}

if_private = False
privater_id = 0

# 初始化Pyrogram客户端
app = Client("messager", api_id=API_ID, api_hash=API_HASH, bot_token=TOKEN)


@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply("您好，我是传话的，有啥说的尽管说！")

@app.on_message(filters.command("version"))
async def version(client, message):
    message_text = (
        f"Telegram Messager 消息助手 Bot\n"
        f"(ver. {VERSION})\n\n"
        f"该项目由[此](https://github.com/QingshiLane/Telegram-homing_pigeon_bot)获得灵感所作"
    )
    await message.reply_text(message_text, parse_mode=enums.ParseMode.MARKDOWN)

@app.on_message(filters.text & ~filters.command(["start", "ban", "unban", "enter_1v1", "exit_1v1"]))
async def relay_message(client, message):
    global cursor
    user_id = message.from_user.id
    username = message.from_user.username or "Unknown"
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name
    fullname = f"{first_name} {last_name}" if last_name else first_name

    if user_id != YOUR_USER_ID:
        if user_id not in recent_chatters:
            if len(recent_chatters) >= 4:
                recent_chatters.pop(0)
            recent_chatters.append(user_id)

        usernames[user_id] = username
        fullnames[user_id] = fullname

        cursor.execute("SELECT * FROM banned_users WHERE user_id = ?", (user_id,))
        if cursor.fetchone() is None:
            sent_message = await client.forward_messages(YOUR_USER_ID, message.chat.id, message.id)
            message_sender_map[sent_message.id] = user_id
        else:
            await message.reply("你被禁止发送消息")
    else:
        if if_private:
            user_last_interaction[user_id] = datetime.datetime.now()
            if user_id in user_timers:
                user_timers[user_id].cancel()

            user_timers[user_id] = asyncio.create_task(check_inactivity(user_id))

        if message.reply_to_message:
            original_message_id = message.reply_to_message.id
            original_sender_id = message_sender_map.get(original_message_id)

            if original_sender_id:
                await client.send_message(original_sender_id, message.text)
            else:
                await message.reply("无法识别原始发送者，无法发送消息")
        else:
            if if_private:
                await client.send_message(privater_id, message.text)
            else:
                await message.reply("非1v1，您发送的信息仅存在此窗口")


async def check_inactivity(user_id):
    await asyncio.sleep(180)
    last_interaction = user_last_interaction.get(user_id)
    if last_interaction and (datetime.datetime.now() - last_interaction).total_seconds() >= 180:
        global if_private
        if if_private:
            if_private = False
            global privater_id
            privater_id = 0
            await app.send_message(user_id, "你已经3分钟未对话，退出1v1")


@app.on_message(filters.command("ban"))
async def ban(client, message):
    if message.from_user.id == YOUR_USER_ID:
        keyboard = [
            [InlineKeyboardButton(f"禁言🚫{fullnames.get(recent_chatters[i])}@{usernames.get(recent_chatters[i], 'Unknown')}", callback_data=f"ban_{recent_chatters[i]}")]
            for i in range(min(len(recent_chatters), 4))
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await message.reply("选择要禁止的聊天者", reply_markup=reply_markup)
    else:
        await message.reply("您无权进行此操作，您只能向我发消息")


@app.on_message(filters.command("unban"))
async def unban(client, message):
    if message.from_user.id == YOUR_USER_ID:
        keyboard = [
            [InlineKeyboardButton(f"解除禁言🔊{fullnames.get(banned_user)}@{usernames.get(banned_user, 'Unknown')}", callback_data=f"unban_{banned_user}")]
            for banned_user in get_banned_users()
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await message.reply("选择要解除禁止的聊天者", reply_markup=reply_markup)
    else:
        await message.reply("您无权进行此操作，您只能向我发消息")


def get_banned_users():
    global cursor
    cursor.execute("SELECT user_id FROM banned_users")
    return [row[0] for row in cursor.fetchall()]


@app.on_message(filters.command("enter_1v1"))
async def enter_private_chat(client, message):
    if message.from_user.id == YOUR_USER_ID:
        keyboard = [
            [InlineKeyboardButton(f"1v1💬{fullnames.get(recent_chatters[i])}@{usernames.get(recent_chatters[i], 'Unknown')}", callback_data=f"enterprivatechat_{recent_chatters[i]}")]
            for i in range(min(len(recent_chatters), 4))
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await message.reply("选择要1v1的聊天对象", reply_markup=reply_markup)
    else:
        await message.reply("您无权进行此操作，您只能向我发消息")


@app.on_message(filters.command("exit_1v1"))
async def exit_private_chat(client, message):
    if message.from_user.id == YOUR_USER_ID:
        global if_private
        if if_private:
            if_private = False
            global privater_id
            privater_id = 0
            await message.reply("您已退出1v1模式")
        else:
            await message.reply("您已处于非1v1模式，无需重复操作")
    else:
        await message.reply("您无权进行此操作，您只能向我发消息")


@app.on_callback_query()
async def button(client, callback_query):
    global cursor
    data = callback_query.data
    if data.startswith("ban_"):
        user_id = int(data.split("_")[1])
        cursor.execute("INSERT OR IGNORE INTO banned_users (user_id) VALUES (?)", (user_id,))
        conn.commit()
        await callback_query.answer(f"已禁止用户 {fullnames.get(user_id)}@{usernames.get(user_id, 'Unknown')}.")
    elif data.startswith("unban_"):
        user_id = int(data.split("_")[1])
        cursor.execute("DELETE FROM banned_users WHERE user_id = ?", (user_id,))
        conn.commit()
        await callback_query.answer(f"已解除对用户 {fullnames.get(user_id)}@{usernames.get(user_id, 'Unknown')} 的禁止")
    elif data.startswith("enterprivatechat_"):
        global if_private
        if_private = True
        user_id = int(data.split("_")[1])
        global privater_id
        privater_id = user_id
        await callback_query.answer(f"已进入和用户 {fullnames.get(user_id)}@{usernames.get(user_id)} 的1v1模式")


if __name__ == "__main__":
    app.run()
