from pyrogram import Client, filters
from pymongo import MongoClient
import os
from info import DATABASE_URI

# Initialize the MongoDB client and database
client = MongoClient(DATABASE_URI)
db = client["settings"]
collection = db["autofilter_settings"]

# Helper function to update the autofilter setting in the database
def set_autofilter_status(chat_id, status):
    collection.update_one(
        {"chat_id": chat_id},
        {"$set": {"autofilter": status}},
        upsert=True
    )

# Helper function to get the current autofilter status
def get_autofilter_status(chat_id):
    doc = collection.find_one({"chat_id": chat_id})
    return doc["autofilter"] if doc else False

# Command to turn autofilter on
@Client.on_message(filters.command("autofilter") & filters.group)
async def toggle_autofilter(client, message):
    chat_id = message.chat.id
    args = message.text.split()

    if len(args) < 2:
        await message.reply_text("Please specify 'on' or 'off' after the command.")
        return

    if args[1].lower() == "on":
        set_autofilter_status(chat_id, True)
        await message.reply_text("Autofilter is now ON.")
    elif args[1].lower() == "off":
        set_autofilter_status(chat_id, False)
        await message.reply_text("Autofilter is now OFF.")
    else:
        await message.reply_text("Invalid option. Use 'on' or 'off'.")

# Command to check the current autofilter status
@Client.on_message(filters.command("autofilterstatus") & filters.group)
async def autofilter_status(client, message):
    chat_id = message.chat.id
    status = get_autofilter_status(chat_id)
    status_text = "ON" if status else "OFF"
    await message.reply_text(f"Autofilter is currently {status_text}.")

