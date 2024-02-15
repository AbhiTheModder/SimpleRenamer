import math
import time
import os
import asyncio

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Retrieve the environment variable
sudo_users = os.getenv('SUDO_USER_IDS') # use ```export SUDO_USER_IDS=ID1,ID2,ID3``` to set
# Split the string into a list of strings
sudo_users_list = sudo_users.split(',')

# Convert the list of strings to a list of integers
SUDO_USERS = [int(user_id) for user_id in sudo_users_list]

from pyrogram.errors import FloodWait, MessageNotModified
from pyrogram import Client, errors, types, enums, filters
from pyrogram.types import Message

def time_formatter(milliseconds: int) -> str:
    """Time Formatter"""
    seconds, milliseconds = divmod(int(milliseconds), 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    tmp = (
        ((str(days) + " day(s), ") if days else "")
        + ((str(hours) + " hour(s), ") if hours else "")
        + ((str(minutes) + " minute(s), ") if minutes else "")
        + ((str(seconds) + " second(s), ") if seconds else "")
        + ((str(milliseconds) + " millisecond(s), ") if milliseconds else "")
    )
    return tmp[:-2]

def humanbytes(size):
    """Convert Bytes To Bytes So That Human Can Read It"""
    if not size:
        return ""
    power = 2 ** 10
    raised_to_pow = 0
    dict_power_n = {0: "", 1: "Ki", 2: "Mi", 3: "Gi", 4: "Ti"}
    while size > power:
        size /= power
        raised_to_pow += 1
    return str(round(size, 2)) + " " + dict_power_n[raised_to_pow] + "B"

async def progress(current, total, message, start, type_of_ps, file_name=None):
    """Progress Bar For Showing Progress While Uploading / Downloading File - Normal"""
    now = time.time()
    diff = now - start
    if round(diff % 10.00) == 0 or current == total:
        percentage = current * 100 / total
        speed = current / diff
        elapsed_time = round(diff) * 1000
        if elapsed_time == 0:
            return
        time_to_completion = round((total - current) / speed) * 1000
        estimated_total_time = elapsed_time + time_to_completion
        progress_str = "{0}{1} {2}%\n".format(
            "".join(["▰" for i in range(math.floor(percentage / 10))]),
            "".join(["▱" for i in range(10 - math.floor(percentage / 10))]),
            round(percentage, 2),
        )
        tmp = progress_str + "{0} of {1}\nETA: {2}".format(
            humanbytes(current), humanbytes(total), time_formatter(estimated_total_time)
        )
        if file_name:
            try:
                await message.edit(
                    "{}\n**File Name:** `{}`\n{}".format(type_of_ps, file_name, tmp, parse_mode=enums.ParseMode.MARKDOWN)
                )
            except FloodWait as e:
                await asyncio.sleep(e.x)
            except MessageNotModified:
                pass
        else:
            try:
                await message.edit("{}\n{}".format(type_of_ps, tmp), parse_mode=enums.ParseMode.MARKDOWN)
            except FloodWait as e:
                await asyncio.sleep(e.x)
            except MessageNotModified:
                pass

app = Client("rename_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

@app.on_message(filters.command("start"))
async def start(client: Client, message: Message):
    if message.from_user.id not in SUDO_USERS:
        await message.reply("You are not authorized to use this command.")
        return
    else:
        await message.reply("Use /rename `file_name.extension`\nand /setthumb with reply to image to set new thumb. \nI'm also capable of multi renaming at once just use rename command to files you want to rename, sit back and relax :D")

@app.on_message(filters.command("rename"))
async def rename(client: Client, message: Message):
    if message.from_user.id not in SUDO_USERS:
        await message.reply("You are not authorized to use this command.")
        return
    else:
        try:
            c_time = time.time()
            i = await message.reply("`Renaming...`")
            user_dir = f"thumbnails/{message.from_user.id}"
            thumb_path = os.path.join(user_dir, "thumb.jpg")
            if len(message.command) > 1:
                r_fname = message.text.split(maxsplit=1)[1]
                o_f = await message.reply_to_message.download(
                progress=progress,
                progress_args=(i, c_time, '`Renaming...`'),)
                r_f = os.rename(o_f, r_fname)
                await i.edit_text("`Done, Uploading...`")
                # Check if the user has a custom thumbnail
                if os.path.exists(thumb_path):
                    # Use the user's custom thumbnail
                    await client.send_document(message.chat.id, r_fname, reply_to_message_id=message.id, caption=r_fname,
                    progress=progress,
                    progress_args=(i, c_time, '`Done, Uploading...`'),
                    thumb=thumb_path)
                else:
                    # No custom thumbnail, so don't include the thumb parameter
                    await client.send_document(message.chat.id, r_fname, reply_to_message_id=message.id, caption=r_fname,
                    progress=progress,
                    progress_args=(i, c_time, '`Done, Uploading...`'))
                await i.delete()
            else:
                await i.edit_text("lOl, Atleast reply to file and give new name (with extension ofc) to rename to -_-")
        except Exception as e:
            await i.edit(str(e))
        finally:
            os.remove(r_fname)

@app.on_message(filters.command("setthumb"))
async def setthumb(client: Client, message: Message):
    if message.from_user.id not in SUDO_USERS:
        await message.reply("You are not authorized to use this command.")
        return
    else:
        try:
            # Create a directory for the user if it doesn't exist
            user_dir = f"thumbnails/{message.from_user.id}"
            if not os.path.exists(user_dir):
                os.makedirs(user_dir)
            
            # Download the thumbnail and save it in the user's directory
            new_thumb = await message.reply_to_message.download()
            thumb_path = os.path.join(user_dir, "thumb.jpg")
            os.rename(new_thumb, thumb_path)
            
            # Send a confirmation message
            await message.reply("Thumbnail set successfully!")
        except Exception as e:
            await message.reply(str(e))


app.run()
