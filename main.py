
import logging
import os
import random
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Setup logging
logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

SONGS_FOLDER = "songs"

# Keyboard
def get_keyboard():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        types.InlineKeyboardButton("▶️ Next", callback_data="next"),
        types.InlineKeyboardButton("🔁 Replay", callback_data="replay")
    )
    return keyboard

# Commands
@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    await message.reply("👋 Welcome to Squonk Radio V0.3! Use /setup in private chat or /play in groups.")

@dp.message_handler(commands=["setup"])
async def setup(message: types.Message):
    if message.chat.type != "private":
        return await message.reply("Please use this command in a private chat.")
    await message.reply("📥 Send me an mp3 file, and tell me which group it belongs to.\n\nExample:\n1. Send: `GroupID: 123456789`\n2. Then upload mp3 files.")

@dp.message_handler(lambda msg: msg.text and msg.text.startswith("GroupID:"))
async def receive_group_id(message: types.Message):
    group_id = message.text.replace("GroupID:", "").strip()
    if not group_id.isdigit():
        return await message.reply("❌ Invalid group ID. Please send like `GroupID: 123456789`")
    message.chat_data = {"group_id": group_id}
    await message.reply(f"✅ Group ID set to {group_id}. Now send mp3 files!")

@dp.message_handler(content_types=types.ContentType.AUDIO)
async def handle_audio(message: types.Message):
    group_id = message.chat_data.get("group_id") if hasattr(message, "chat_data") else None
    if not group_id:
        return await message.reply("❗ Please first send `GroupID: <your_group_id>`")

    file = message.audio
    file_path = f"{SONGS_FOLDER}/{group_id}"
    os.makedirs(file_path, exist_ok=True)
    file_name = f"{file.file_unique_id}.mp3"
    full_path = os.path.join(file_path, file_name)
    await file.download(destination_file=full_path)
    await message.reply(f"✅ Saved `{file.file_name}` for group {group_id}")

@dp.message_handler(commands=["play"])
async def play(message: types.Message):
    group_id = str(message.chat.id)
    folder = os.path.join(SONGS_FOLDER, group_id)
    if not os.path.exists(folder) or not os.listdir(folder):
        return await message.reply("❌ No songs found for this group. Use /setup in private chat to add songs.")

    song_file = random.choice(os.listdir(folder))
    song_path = os.path.join(folder, song_file)
    await message.reply_audio(open(song_path, "rb"), caption="🎶 Squonk time!", reply_markup=get_keyboard())

@dp.callback_query_handler(lambda c: c.data in ["next", "replay"])
async def handle_buttons(call: types.CallbackQuery):
    group_id = str(call.message.chat.id)
    folder = os.path.join(SONGS_FOLDER, group_id)
    if not os.path.exists(folder) or not os.listdir(folder):
        return await call.answer("No songs found.", show_alert=True)

    song_file = random.choice(os.listdir(folder)) if call.data == "next" else os.listdir(folder)[0]
    song_path = os.path.join(folder, song_file)
    await bot.send_audio(call.message.chat.id, open(song_path, "rb"), caption="🎵 Squonk on!", reply_markup=get_keyboard())
    await call.answer()
    
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
