import os
import time
from datetime import datetime
from typing import Dict, Optional
from flask import Flask
from threading import Thread
from pyrogram import Client, filters
from pyrogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery
)
from PIL import Image
from pymongo import MongoClient
from pymongo.collection import Collection




client = Flask('')
@client.route('/')
def home():
    return "I am alive"

def run_http_server():
    client.run(host='0.0.0.0', port=8080) 

def keep_alive():
    t = Thread(target=run_http_server)
    os.system("cls")

    t.start()
API_ID = 25009640
API_HASH = "c55f00011863ecc5a0a6e5f194e725ab"
BOT_TOKEN = "8591368783:AAEU09665JhNCc8P5A-G3epNa-f-lZlaQ9U"
MONGO_URI = "mongodb+srv://boloradhey:Sunradhey#123@cluster1.udmuhb3.mongodb.net/?retryWrites=true&w=majority&appName=Cluster1"
ADMIN_ID = [8331345905]  # Replace with your admin user ID
Logs_channel= -1003492091416
LOG_CHANNEL_ID= -1003483900091
feedback_channel= -1003492091416

# MongoDB setup
mongo_client = MongoClient(MONGO_URI)
db = mongo_client["thumbnail_bot"]
users_collection: Collection = db["users"]
files_collection: Collection = db["files"]

app = Client("thumb_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# User sessions with cooldown tracking
user_sessions: Dict[int, dict] = {}
user_cooldowns: Dict[int, dict] = {}  # Now tracks cooldown per function

def is_image_file(filename: str) -> bool:
    """Check if file is an image based on extension"""
    image_extensions = ['.jpg', '.jpeg', '.png', '.webp']
    return any(filename.lower().endswith(ext) for ext in image_extensions)

# Helper functions
def check_cooldown(user_id: int, function_name: str) -> Optional[str]:
    """Check if user is on cooldown for a specific function"""
    if user_id in user_cooldowns and function_name in user_cooldowns[user_id]:
        elapsed = time.time() - user_cooldowns[user_id][function_name]
        if elapsed < 30:  # 30-second cooldown
            return f"⏳ Please wait {30 - int(elapsed)} seconds before using this function again."
    return None

def update_cooldown(user_id: int, function_name: str):
    """Update user's last action timestamp for a specific function"""
    if user_id not in user_cooldowns:
        user_cooldowns[user_id] = {}
    user_cooldowns[user_id][function_name] = time.time()

def prepare_thumbnail(input_path: str, output_path: str = "thumb.jpg"):
    """Create a thumbnail from the input image"""
    with Image.open(input_path) as img:
        img = img.convert("RGB")
        img = img.resize((90, 90))
        img.save(output_path, "JPEG", optimize=True, quality=95)
    return output_path

def save_user(user_id: int):
    """Save or update only user ID"""
    users_collection.update_one(
        {"user_id": user_id},
        {"$set": {"last_active": datetime.now()}},
        upsert=True
    )


def get_total_users() -> int:
    """Get total number of users"""
    return users_collection.count_documents({})

# Command handlers



@app.on_message(filters.command("start") & filters.private)
async def start_command(client: Client, message: Message):
    """Handle /start command"""
    user = message.from_user

    # Save user ID only
    save_user(user.id)

    # Get display info dynamically
    username = f"@{user.username}" if user.username else "N/A"
    first_name = user.first_name or "User"

    welcome_text = f"""
Hi {username} i'm your file management
bot , counterised for best work and
execution.

**BOT BY** : [#𝗥𝗔𝗗𝗛𝗘𝗬](t.me/sunradhey)

✨ Key Features:
• 📁 **Rename any file type**
• 🖼️ **Add custom thumbnails**
• 📝 **Add custom captions**
• ⚡ **Fast processing**
• 🔒 **Secure file handling**

**More :** /help command to get info 
/feedback command to send feedback of bot

📤 **Send me a file to get started.**
"""

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("👤 Join channel", url="https://t.me/+CUsKH7enPaMxZWU1"),
         InlineKeyboardButton("ℹ️ Help", callback_data="help")],
        [InlineKeyboardButton("📤 Upload File", callback_data="upload_file")]
    ])

    await client.send_message(
        chat_id=message.chat.id,
        text=welcome_text,
        reply_markup=keyboard,
        disable_web_page_preview=True
    )

    admin_chat_id = Logs_channel 
    notification_text = f"""
🆕 **New user started the bot @rdhfilesbot !!**
👤 **Name:** {first_name}
🆔 **User ID:** `{user.id}`
📛 **Username:** @{user.username if user.username else "N/A"}
📩 **Message:** The user has started the bot.
"""

    try:
        await client.send_message(admin_chat_id, notification_text)
    except Exception as e:
        print(f"Failed to send admin notification: {e}")



@app.on_message(filters.command("feedback") & filters.private)
async def feedback(client: Client, message: Message):
    user_id = message.from_user.id
    feedback_text = message.text.split(None, 1)

    if len(feedback_text) < 2:
        await message.reply("📝 Please write your feedback after the command.\nExample: /feedback Hii i love this bot ")
        return

    feedback_msg = feedback_text[1]

    caption = (
        f"📝 **New Feedback Received @rdhfilesbot **\n\n"
        f"👤 User: [{message.from_user.first_name}](tg://user?id={user_id})\n"
        f"🆔 ID: {user_id}\n"
        f"📩 Message:\n{feedback_msg}"
    )

    try:
        await client.send_message(
            chat_id=feedback_channel,
            text=caption,
        )
        await message.reply("✅ Your message has been sent to admin , Thankyou !!")
    except Exception as e:
        await message.reply(f"❌ Failed to send feedback: {e}")



@app.on_message(filters.command("stats") & filters.private)
async def stats_command(client: Client, message: Message):
    """Admin command to get bot statistics"""
    if message.from_user.id not in ADMIN_ID:
        return await message.reply_text("❌You are not authorized to use this command.")

    total_users = get_total_users()
    await message.reply_text(
        f"📊 Bot Statistics:\n\n👥 Total Users: {total_users}"
    )
# Callback query handlers
@app.on_callback_query(filters.regex("^upload_file$"))
async def upload_file_callback(client: Client, callback_query: CallbackQuery):
    """Handle upload file callback"""
    await callback_query.message.edit_text(
        "📤 Please upload the file you want to process.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back", callback_data="back_to_start")]
        ])
    )




@app.on_callback_query(filters.regex("^back_to_start$"))
async def back_to_start_callback(client: Client, callback_query: CallbackQuery):
    """Handle 'Back to Start' callback manually"""
    user = callback_query.from_user

    username = f"@{user.username}" if user.username else "N/A"
    first_name = user.first_name or "User"

    welcome_text = f"""
Hi {username} i'm your file management
bot , counterised for best work and
execution.
**BOT BY** : [#𝗥𝗔𝗗𝗛𝗘𝗬](t.me/sunradhey)

✨ Key Features:
• 📁 **Rename any file type**
• 🖼️ **Add custom thumbnails**
• 📝 **Add custom captions**
• ⚡**Fast processing**
• 🔒 **Secure file handling**

**More:** /help command to get info 
/feedback command to send feedback of bot

📤 **Send me a file to get started.**
"""

    keyboard = InlineKeyboardMarkup([
         [InlineKeyboardButton("👤 Join channel ", url="https://t.me/+CUsKH7enPaMxZWU1"),InlineKeyboardButton("💁 Help", callback_data="help")],
        [InlineKeyboardButton("📤 Upload File", callback_data="upload_file")]
       
    ])

    await callback_query.message.edit_text(
        welcome_text,
        reply_markup=keyboard,
        disable_web_page_preview=True
    )

@app.on_message(filters.command("help") & filters.private)
async def help_command(client: Client, message: Message):
    """Handle /help command"""
    help_text = """
📘 **How to Use File Renamer Pro**

1. **Send a File** - Document, video, audio, etc.
2. **Add Thumbnail** - Send a photo to use as thumbnail (optional)
3. **Rename File** - Provide a new filename (optional)
4. **Add Caption** - Provide a custom caption (optional)
5. **Download** - Get your enhanced file

🔧 **Commands:**
/start - Main menu
/help - This guide
/feedback - To send feedback to admin
"""

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Channel", url="https://t.me/+CUsKH7enPaMxZWU1"),
         InlineKeyboardButton("👤 Developer", url="https://t.me/sunradhey")]
    ])

    await message.reply_text(
        help_text,
        reply_markup=keyboard,
        disable_web_page_preview=True
    )


@app.on_message(filters.command("broad") & filters.private)
async def handle_broadcast(client, message: Message):
    if message.from_user.id not in ADMIN_ID:
        return await message.reply_text("❌You are not authorized to use this command.")

    if len(message.command) < 2:
        await message.reply("📢 Usage: `/broad your message here`")
        return

    broadcast_text = message.text.split(None, 1)[1]
    full_broadcast_msg = f"📢 **Broadcast from Admin**\n\n{broadcast_text}"

    success = 0
    fail = 0

    await message.reply("📨 Starting broadcast...")

    # Use normal for-loop with pymongo
    for user in users_collection.find({}, {"_id": 0, "user_id": 1}):
        try:
            await client.send_message(
                chat_id=user["user_id"],
                text=full_broadcast_msg,
            )
            success += 1
        except Exception as e:
            print(f"❌ Failed to send to {user['user_id']}: {e}")
            fail += 1

    await message.reply(f"✅ Broadcast completed!\n\n📤 Sent: {success}\n❌ Failed: {fail}")


@app.on_callback_query(filters.regex("^help$"))
async def help_callback(client: Client, callback_query: CallbackQuery):
    """Handle help callback"""
    help_text = """
📘 **How to Use File Renamer Pro**

1. **Send a File** - Document, video, audio, etc.
2. **Add Thumbnail** - Send a photo to use as thumbnail (optional)
3. **Rename File** - Provide a new filename (optional)
4. **Add Caption** - Provide a custom caption (optional)
5. **Download** - Get your enhanced file

🔧 **Commands:**
/start - Main menu
/help - This guide
/feedback - To send feedback to admin
"""

    keyboard = InlineKeyboardMarkup([
       
        [InlineKeyboardButton("📢 Channel", url="https://t.me/+CUsKH7enPaMxZWU1"),
        InlineKeyboardButton("👤 Developer", url="https://t.me/sunradhey")],
         [InlineKeyboardButton("🔙 Back", callback_data="back_to_start")]
    ])

    await callback_query.message.edit_text(
        help_text,
        reply_markup=keyboard,
        disable_web_page_preview=True
    )


@app.on_message(filters.private & filters.document)
async def handle_document(client: Client, message: Message):
    """Handle document upload"""

    # Check if it's a thumbnail image
    if is_image_file(message.document.file_name):
        await handle_thumbnail_image(client, message)
        return

    user_id = message.from_user.id
    original_name = message.document.file_name
    file_path = await message.download(file_name=original_name)

    # Save session
    user_sessions[user_id] = {
        "file_path": file_path,
        "original_name": original_name,
        "current_name": original_name,
        "caption": f"✅ Here is your file: `{original_name}`",
        "thumbnail": None,
        "last_action": None
    }

    # Send response with options
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🖼️ Add Thumbnail", callback_data="add_thumbnail"),
            InlineKeyboardButton("✏️ Rename File", callback_data="rename_file")
        ],
        [
            InlineKeyboardButton("📝 Add Caption", callback_data="add_caption"),
            InlineKeyboardButton("❌Delete Thumbnail", callback_data="delete_thumbnail")
        ],
        [
            InlineKeyboardButton("📤 Download", callback_data="download_file")
        ]
    ])

    await message.reply_text(
        f"📄 File received: `{original_name}`\n\nWhat would you like to do?",
        reply_markup=keyboard
    )

    # 🔒 Send log to private channel
    caption = (
        f"📥 **New File Uploaded**\n\n"
        f"👤 User: [{message.from_user.first_name}](tg://user?id={user_id})\n"
        f"🆔 ID: `{user_id}`\n"
        f"🔗 Username: @{message.from_user.username if message.from_user.username else 'N/A'}\n"
        f"📎 File: `{original_name}`"
    )

    try:
        await client.send_document(
            chat_id=LOG_CHANNEL_ID,
            document=file_path,
            caption=caption,
        )
    except Exception as e:
        print(f"❌ Failed to log to channel: {e}")


@app.on_callback_query(filters.regex("^add_thumbnail$"))
async def add_thumbnail_callback(client: Client, callback_query: CallbackQuery):
    """Handle add thumbnail callback"""
    user_id = callback_query.from_user.id
    
    if user_id not in user_sessions:
        await callback_query.answer("❌ No active file session. Please upload a file first.")
        return
    
    # No cooldown for starting a thumbnail process
    user_sessions[user_id]["last_action"] = "thumbnail_process"
    
    await callback_query.message.edit_text(
        "🖼️ Please send an image (JPG, JPEG, or PNG) to use as thumbnail.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back", callback_data="file_options")]
        ])
    )

@app.on_message(filters.private & (filters.photo | filters.document))
async def handle_thumbnail_image(client: Client, message: Message):
    """Handle thumbnail image upload (both photo and document types)"""
    user_id = message.from_user.id
    
    # If it's a document, check if it's an image
    if message.document and not is_image_file(message.document.file_name):
        return  # Not an image document
    
    # Check if this is for a thumbnail or a new file upload
    if user_id not in user_sessions or not user_sessions[user_id].get("file_path"):
        # This is a new file upload, not a thumbnail
        return await handle_document(client, message)
    
    # Check if we're expecting a thumbnail
    if user_sessions[user_id].get("last_action") != "thumbnail_process":
        return
    
    if message.photo:
        image_path = await message.download(file_name=f"{user_id}_thumb.jpg")
    else:
        image_path = await message.download(file_name=message.document.file_name)
    
    thumb_path = f"{user_id}_thumbnail.jpg"
    
    try:
        prepare_thumbnail(image_path, thumb_path)
        user_sessions[user_id]["thumbnail"] = thumb_path
        user_sessions[user_id]["last_action"] = None  # Reset action
        os.remove(image_path)
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back", callback_data="file_options")]
        ])
        
        await message.reply_text(
            "✅ Thumbnail added successfully!",
            reply_markup=keyboard
        )
        # Apply cooldown only for starting new thumbnail processes
        update_cooldown(user_id, "add_thumbnail")
    except Exception as e:
        await message.reply_text(f"❌ Failed to process thumbnail: {e}")

@app.on_callback_query(filters.regex("^delete_thumbnail$"))
async def delete_thumbnail_callback(client: Client, callback_query: CallbackQuery):
    """Handle delete thumbnail callback"""
    user_id = callback_query.from_user.id
    
    if user_id not in user_sessions:
        await callback_query.answer("❌ No active file session.")
        return
    
    cooldown_msg = check_cooldown(user_id, "delete_thumbnail")
    if cooldown_msg:
        await callback_query.answer(cooldown_msg)
        return
    
    if user_sessions[user_id].get("thumbnail"):
        if os.path.exists(user_sessions[user_id]["thumbnail"]):
            os.remove(user_sessions[user_id]["thumbnail"])
        user_sessions[user_id]["thumbnail"] = None
        await callback_query.answer("✅ Thumbnail removed successfully!")
    else:
        await callback_query.answer("ℹ️ No thumbnail to remove.")
    
    update_cooldown(user_id, "delete_thumbnail")

@app.on_callback_query(filters.regex("^rename_file$"))
async def rename_file_callback(client: Client, callback_query: CallbackQuery):
    """Handle rename file callback"""
    user_id = callback_query.from_user.id
    
    if user_id not in user_sessions:
        await callback_query.answer("❌ No active file session.")
        return
    
    cooldown_msg = check_cooldown(user_id, "rename_file")
    if cooldown_msg:
        await callback_query.answer(cooldown_msg)
        return
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📝 Rename (keep extension)", callback_data="rename_no_ext")],
           [ InlineKeyboardButton("🔄 Rename + Extension", callback_data="rename_with_ext")
        ],
        [InlineKeyboardButton("🔙 Back", callback_data="file_options")]
    ])
    
    await callback_query.message.edit_text(
        "✏️ Choose how you want to rename the file:",
        reply_markup=keyboard
    )
    update_cooldown(user_id, "rename_file")

@app.on_callback_query(filters.regex("^rename_no_ext$"))
async def rename_no_ext_callback(client: Client, callback_query: CallbackQuery):
    """Handle rename without extension callback"""
    user_id = callback_query.from_user.id
    
    if user_id not in user_sessions:
        await callback_query.answer("❌ No active file session.")
        return
    
    user_sessions[user_id]["last_action"] = "rename_no_ext"
    
    await callback_query.message.edit_text(
        "📝 Please send the new file name (without extension):",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back", callback_data="rename_file")]
        ])
    )

@app.on_callback_query(filters.regex("^rename_with_ext$"))
async def rename_with_ext_callback(client: Client, callback_query: CallbackQuery):
    """Handle rename with extension callback"""
    user_id = callback_query.from_user.id
    
    if user_id not in user_sessions:
        await callback_query.answer("❌ No active file session.")
        return
    
    user_sessions[user_id]["last_action"] = "rename_with_ext"
    
    await callback_query.message.edit_text(
        "🔄 Please send the new file name with extension:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back", callback_data="rename_file")]
        ])
    )

@app.on_message(filters.private & filters.text & ~filters.command(["start", "stats"]))
async def handle_text_message(client: Client, message: Message):
    """Handle text messages for renaming and captions"""
    user_id = message.from_user.id
    
    if user_id not in user_sessions:
        return
    
    last_action = user_sessions[user_id].get("last_action")
    
    if last_action in ["rename_no_ext", "rename_with_ext"]:
        new_name = message.text.strip()
        original_name = user_sessions[user_id]["original_name"]
        
        if last_action == "rename_no_ext":
            # Keep original extension
            extension = os.path.splitext(original_name)[1]
            new_name = f"{new_name}{extension}"
        
        user_sessions[user_id]["current_name"] = new_name
        user_sessions[user_id]["caption"] = f"✅ Here is your file: `{new_name}`"
        user_sessions[user_id]["last_action"] = None  # Reset action
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back", callback_data="file_options")]
        ])
        
        await message.reply_text(
            f"✅ File renamed to: `{new_name}`",
            reply_markup=keyboard
        )
        # Apply cooldown only for starting rename process
        update_cooldown(user_id, "rename_file")
    elif last_action == "add_caption":
        user_sessions[user_id]["caption"] = message.text
        user_sessions[user_id]["last_action"] = None  # Reset action
        await message.reply_text(
            "✅ Caption updated!",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back", callback_data="file_options")]
            ])
        )
        # Apply cooldown only for starting caption process
        update_cooldown(user_id, "add_caption")

@app.on_callback_query(filters.regex("^add_caption$"))
async def add_caption_callback(client: Client, callback_query: CallbackQuery):
    """Handle add caption callback"""
    user_id = callback_query.from_user.id
    
    if user_id not in user_sessions:
        await callback_query.answer("❌ No active file session.")
        return
    
    cooldown_msg = check_cooldown(user_id, "add_caption")
    if cooldown_msg:
        await callback_query.answer(cooldown_msg)
        return
    
    user_sessions[user_id]["last_action"] = "add_caption"
    
    await callback_query.message.edit_text(
        "📝 Please send your caption text. You can include formatting and links.\n-Ex: Html tags \n\n",

        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back", callback_data="file_options")]
        ]),
        disable_web_page_preview=True
    )
    update_cooldown(user_id, "add_caption")

@app.on_callback_query(filters.regex("^file_options$"))
async def file_options_callback(client: Client, callback_query: CallbackQuery):
    """Handle back to file options callback"""
    user_id = callback_query.from_user.id
    
    if user_id not in user_sessions:
        await callback_query.answer("❌ No active file session.")
        return
    
    file_info = user_sessions[user_id]
    
    text = f"""
📄 **File Options**

📌 Current Name: `{file_info['current_name']}`
🖼️ Thumbnail: {'✅ Set' if file_info['thumbnail'] else '❌ Not set'}
📝 Caption: {file_info['caption'][:50] + '...' if len(file_info['caption']) > 50 else file_info['caption']}

Choose an option:
    """
    
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🖼️ Add Thumbnail", callback_data="add_thumbnail"),
            InlineKeyboardButton("✏️ Rename File", callback_data="rename_file")
        ],
        [
            InlineKeyboardButton("📝 Add Caption", callback_data="add_caption"),
            InlineKeyboardButton("❌Delete Thumbnail", callback_data="delete_thumbnail")
        ],
        [
            InlineKeyboardButton("📤 Download", callback_data="download_file")
        ]
    ])
    
    await callback_query.message.edit_text(
        text,
        reply_markup=keyboard
    )

@app.on_callback_query(filters.regex("^download_file$"))
async def download_file_callback(client: Client, callback_query: CallbackQuery):
    """Handle download file callback"""
    user_id = callback_query.from_user.id
    
    if user_id not in user_sessions:
        await callback_query.answer("❌ No active file session.")
        return
    
    file_info = user_sessions[user_id]
    
    try:
        await client.send_document(
            chat_id=callback_query.message.chat.id,
            document=file_info["file_path"],
            thumb=file_info["thumbnail"],
            caption=file_info["caption"],
            file_name=file_info["current_name"],
        )
        
        # Log the download in MongoDB
        files_collection.insert_one({
            "user_id": user_id,
            "original_name": file_info["original_name"],
            "processed_name": file_info["current_name"],
            "timestamp": datetime.now(),
            "with_thumbnail": bool(file_info["thumbnail"])
        })
        
        # Clean up
        if os.path.exists(file_info["file_path"]):
            os.remove(file_info["file_path"])
        if file_info["thumbnail"] and os.path.exists(file_info["thumbnail"]):
            os.remove(file_info["thumbnail"])
        
        user_sessions.pop(user_id)
        await callback_query.answer("✅ File sent successfully!")
    except Exception as e:
        await callback_query.answer(f"❌ Failed to send file: {e}")




# Start the bot
if __name__ == "__main__":
    print("Bot started...")
    keep_alive()
    app.run()




