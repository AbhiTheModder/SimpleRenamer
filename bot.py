"""A Simple Renamer bot with Mass Renaming of files in telegram"""
import time
import re
import shutil
import asyncio
import math
import os
from pyrogram import Client, enums, filters
from pyrogram.types import Message
from pyrogram.errors import FloodWait, MessageNotModified

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Retrieve the environment variable
sudo_users = os.getenv(
    "SUDO_USER_IDS"
)  # use ```export SUDO_USER_IDS=ID1,ID2,ID3``` to set
# Split the string into a list of strings
sudo_users_list = sudo_users.split(",")

# Convert the list of strings to a list of integers
SUDO_USERS = [int(user_id) for user_id in sudo_users_list]

app = Client("rename_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)


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
    power = 2**10
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
        progress_str = f"{''.join(['▰' for i in range(math.floor(percentage / 10))])}"
        progress_str += (
            f"{''.join(['▱' for i in range(10 - math.floor(percentage / 10))])}"
        )
        progress_str += f"{round(percentage, 2)}%\n"
        tmp = f"{progress_str}{humanbytes(current)} of {humanbytes(total)}\n"
        tmp += f"ETA: {time_formatter(estimated_total_time)}"
        if file_name:
            try:
                await message.edit(
                    f"{type_of_ps}\n**File Name:** `{file_name}`\n{tmp}",
                    parse_mode=enums.ParseMode.MARKDOWN,
                )
            except FloodWait as e:
                await asyncio.sleep(e.x)
            except MessageNotModified:
                pass
        else:
            try:
                await message.edit(
                    f"{type_of_ps}\n{tmp}", parse_mode=enums.ParseMode.MARKDOWN
                )
            except FloodWait as e:
                await asyncio.sleep(e.x)
            except MessageNotModified:
                pass


def rename_files(directory, season, series, sep, username):
    """For Multi Rename"""

    if sep == "":
        sep = "⌯"

    episode_pattern = re.compile(r"EP(\d+)")
    chapter_pattern = re.compile(r"Chapter (\d+)")
    ch_pattern = re.compile(r"CH(\d+)")

    files = os.listdir(directory)

    for file in files:
        name, ext = os.path.splitext(file)

        episode_match = episode_pattern.search(name)
        chapter_match = chapter_pattern.search(name)
        ch_match = ch_pattern.search(name)

        if episode_match:
            number = "EP" + (episode_match.group(1))
        elif chapter_match:
            number = "Chapter " + (chapter_match.group(1))
        elif ch_match:
            number = "CH" + (ch_match.group(1))
        else:
            print(f"Could not find episode or chapter number in {file}. Skipping.")
            continue

        if season == "":
            new_file_name = f"{series} {sep} {number} {username}{ext}"
        else:
            new_file_name = f"{series} {sep} {season} {sep} {number} {username}{ext}"

        old_path = os.path.join(directory, file)
        new_path = os.path.join(directory, new_file_name)
        shutil.move(old_path, new_path)
        print(f"Renamed {file} to {new_file_name}")


@app.on_message(filters.command("start"))
async def s(_, message: Message):
    """start command handler"""
    if message.from_user.id not in SUDO_USERS:
        await message.reply("You are not authorized to use this command.")
        return
    else:
        await message.reply(
            "Use /rename `file_name.extension`\n"
            + "and /setthumb with reply to image to set new thumb. \n"
            + "I'm also capable of multi renaming at once,"
            + " use rename command to files you want to rename, sit back and relax :D\n"
            + "For Mass renaming [Mostly used for Movies,Animes,"
            + "Series,Donghua,Manga/Manhwa/Manhua] "
            + "send your files then use /mrename"
        )


@app.on_message(filters.command("setthumb"))
async def setthumb(_, message: Message):
    """set user thumbnail"""
    if message.from_user.id not in SUDO_USERS:
        await message.reply("You are not authorized to use this command.")
        return
    if message.reply_to_message is None:
        await message.reply("Use `setthumb` by relpying to a photo!")
        return
    if message.reply_to_message == enums.MessageMediaType.PHOTO:
        m = await message.reply("Setting your thumbnail...")
        user_dir = f"thumbnails/{message.from_user.id}"
        if not os.path.exists(user_dir):
            os.makedirs(user_dir)
        new_thumb = await message.reply_to_message.download()
        thumb_path = os.path.join(user_dir, "thumb.jpg")
        os.rename(new_thumb, thumb_path)
        await m.edit_text("Thumbnail set successfully!")
    else:
        await message.reply("Use `setthumb` by relpying to a photo!")
        return


@app.on_message(filters.command("rename"))
async def rename(client: Client, message: Message):
    """A Simple Renamer"""
    if message.from_user.id not in SUDO_USERS:
        await message.reply("You are not authorized to use this command.")
        return
    rm_dir = f"downloads/{message.from_user.id}"
    for filename in os.listdir(rm_dir):
        file_path = os.path.join(rm_dir, filename)
        if os.path.isfile(file_path) or os.path.islink(file_path):
            os.unlink(file_path)
    try:
        c_time = time.time()
        i = await message.reply("`Renaming...`")
        user_dir = f"thumbnails/{message.from_user.id}"
        thumb_path = os.path.join(user_dir, "thumb.jpg")
        if len(message.command) > 1:
            r_fname = message.text.split(maxsplit=1)[1]
            o_f = await message.reply_to_message.download(
                progress=progress,
                progress_args=(i, c_time, "`Renaming...`"),
            )
            os.rename(o_f, r_fname)
            await i.edit_text("`Done, Uploading...`")
            if os.path.exists(thumb_path):
                await client.send_document(
                    message.chat.id,
                    r_fname,
                    reply_to_message_id=message.id,
                    caption=r_fname,
                    progress=progress,
                    progress_args=(i, c_time, "`Done, Uploading...`"),
                    thumb=thumb_path,
                )
            else:
                await client.send_document(
                    message.chat.id,
                    r_fname,
                    reply_to_message_id=message.id,
                    caption=r_fname,
                    progress=progress,
                    progress_args=(i, c_time, "`Done, Uploading...`"),
                )
            await i.delete()
            os.remove(r_fname)
        else:
            await i.edit_text(
                "lOl, Atleast reply to file and give new name (with extension ofc) to rename to -_-"
            )
    except Exception as e:
        print(str(e))
        await i.edit_text("An ERROR occured please report to my master @Qbtaumai")


@app.on_message(filters.document)
async def filesdl(_, message: Message):
    """Download files"""
    if message.from_user.id not in SUDO_USERS:
        await message.reply("You are not authorized.")
        return
    i = await message.reply_text("Please wait downloading files...")
    c_time = time.time()
    path = f"downloads/{message.from_user.id}/"
    await message.download(
        file_name=path, progress=progress, progress_args=(i, c_time, "`Downloading...`")
    )
    await i.delete()


@app.on_message(filters.command("mrename"))
async def mrename(client: Client, message: Message):
    """rename handler for multiple files"""
    if message.from_user.id not in SUDO_USERS:
        await message.reply("You are not authorized to use this command.")
        return
    try:
        directory = f"downloads/{message.from_user.id}"
        if not os.path.exists(directory):
            os.mkdir(directory)

        if len(os.listdir(directory)) == 0:
            await message.reply_text(
                "No files provided. Please send me your files first\n"
                + "then use /mrename to proceed"
            )
            return

        await message.reply_text(
            "Please provide the series name(leave blank if not applicable):"
        )
        series = await client.wait_for_message(message.chat.id, filters=filters.text)
        series_name = series.text

        await message.reply_text(
            "Please provide the season number(leave blank if not applicable):"
        )
        season = await client.wait_for_message(message.chat.id, filters=filters.text)
        season_name = season.text

        await message.reply_text(
            "Please provide the separator character (default is '⌯'): "
        )
        sep = await client.wait_for_message(message.chat.id, filters=filters.text)
        seperator = sep.text

        await message.reply_text(
            "Please provide the username to put at the end of file(send `blank` if not applicable):"
        )
        username = await client.wait_for_message(message.chat.id, filters=filters.text)
        username_re = username.text

        if username_re.lower() == "blank":
            username_re = ""

        if season_name == "blank":
            season_name = ""

        rename_files(directory, season_name, series_name, seperator, username_re)

        i = await message.reply_text("Renaming...")
        await asyncio.sleep(5)
        c_time = time.time()

        user_dir = f"thumbnails/{message.from_user.id}"
        thumb_path = os.path.join(user_dir, "thumb.jpg")

        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            if os.path.isfile(file_path):
                if os.path.exists(thumb_path):
                    await client.send_document(
                        message.chat.id,
                        document=file_path,
                        thumb=thumb_path,
                        reply_to_message_id=message.id,
                        progress=progress,
                        progress_args=(i, c_time, "`Done, Uploading...`"),
                    )
                else:
                    await client.send_document(
                        message.chat.id,
                        document=file_path,
                        reply_to_message_id=message.id,
                        progress=progress,
                        progress_args=(i, c_time, "`Done, Uploading...`"),
                    )
                await i.delete()
                os.remove(file_path)
    except Exception as e:
        print("ERROR:", str(e))
        await message.edit_text(
            "An ERROR occured please report to my master @Qbtaumai"
        )


app.run()
