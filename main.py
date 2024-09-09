import pyrogram
from pyrogram import Client, filters
from pyrogram.errors import UserAlreadyParticipant, InviteHashExpired, UsernameNotOccupied
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import asyncio
import time
import os
import threading
import json
from os import environ

bot_token = environ.get("TOKEN", "")
api_hash = environ.get("HASH", "")
api_id = int(environ.get("ID", ""))
bot = Client("mybot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

ss = environ.get("STRING", "")
if ss is not None:
    acc = Client("myacc", api_id=api_id, api_hash=api_hash, session_string=ss)
    acc.start()
else:
    acc = None

# Download status
def downstatus(statusfile, message):
    while True:
        if os.path.exists(statusfile):
            break

    time.sleep(3)
    while os.path.exists(statusfile):
        with open(statusfile, "r") as downread:
            txt = downread.read()
        try:
            bot.edit_message_text(message.chat.id, message.id, f"__Downloaded__ : **{txt}**")
            time.sleep(10)
        except:
            time.sleep(5)


# Upload status
def upstatus(statusfile, message):
    while True:
        if os.path.exists(statusfile):
            break

    time.sleep(3)
    while os.path.exists(statusfile):
        with open(statusfile, "r") as upread:
            txt = upread.read()
        try:
            bot.edit_message_text(message.chat.id, message.id, f"__Uploaded__ : **{txt}**")
            time.sleep(10)
        except:
            time.sleep(5)


# Progress writer
def progress(current, total, message, type):
    with open(f'{message.id}{type}status.txt', "w") as fileup:
        fileup.write(f"{current * 100 / total:.1f}%")


# Start command
@bot.on_message(filters.command(["start"]))
async def send_start(client: pyrogram.Client, message: pyrogram.types.Message):
    await bot.send_message(
        message.chat.id,
        f"**__👋 Hi** **{message.from_user.mention}**, **I am Save Restricted Bot, I can send you restricted content by its post link__**\n\n{USAGE}",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("🌐 Update Channel", url="https://t.me/restrictedcontentlife_bot")]]
        ),
        reply_to_message_id=message.id
    )


@bot.on_message(filters.text)
async def save(client: pyrogram.Client, message: pyrogram.types.Message):
    print(message.text)

    # Joining chats
    if "https://t.me/+" in message.text or "https://t.me/joinchat/" in message.text:

        if acc is None:
            await bot.send_message(message.chat.id, f"**String Session is not Set**", reply_to_message_id=message.id)
            return

        try:
            try:
                await acc.join_chat(message.text)
            except Exception as e:
                await bot.send_message(message.chat.id, f"**Error** : __{e}__", reply_to_message_id=message.id)
                return
            await bot.send_message(message.chat.id, "**Chat Joined**", reply_to_message_id=message.id)
        except UserAlreadyParticipant:
            await bot.send_message(message.chat.id, "**Chat already Joined**", reply_to_message_id=message.id)
        except InviteHashExpired:
            await bot.send_message(message.chat.id, "**Invalid Link**", reply_to_message_id=message.id)

    # Getting message
    elif "https://t.me/" in message.text:

        datas = message.text.split("/")
        temp = datas[-1].replace("?single", "").split("-")
        fromID = int(temp[0].strip())
        try:
            toID = int(temp[1].strip())
        except:
            toID = fromID

        for msgid in range(fromID, toID + 1):

            # Private
            if "https://t.me/c/" in message.text:
                chatid = int("-100" + datas[4])

                if acc is None:
                    await bot.send_message(message.chat.id, f"**String Session is not Set**", reply_to_message_id=message.id)
                    return

                await handle_private(message, chatid, msgid)

            # Bot
            elif "https://t.me/b/" in message.text:
                username = datas[4]

                if acc is None:
                    await bot.send_message(message.chat.id, f"**String Session is not Set**", reply_to_message_id=message.id)
                    return
                try:
                    await handle_private(message, username, msgid)
                except Exception as e:
                    await bot.send_message(message.chat.id, f"**Error** : __{e}__", reply_to_message_id=message.id)

            # Public
            else:
                username = datas[3]

                try:
                    msg = await bot.get_messages(username, msgid)
                except UsernameNotOccupied:
                    await bot.send_message(message.chat.id, f"**The username is not occupied by anyone**", reply_to_message_id=message.id)
                    return

                try:
                    await bot.copy_message(message.chat.id, msg.chat.id, msg.id, reply_to_message_id=message.id)
                except:
                    if acc is None:
                        await bot.send_message(message.chat.id, f"**String Session is not Set**", reply_to_message_id=message.id)
                        return
                    try:
                        await handle_private(message, username, msgid)
                    except Exception as e:
                        await bot.send_message(message.chat.id, f"**Error** : __{e}__", reply_to_message_id=message.id)

            # Wait time
            time.sleep(3)


# Handle private
async def handle_private(message: pyrogram.types.Message, chatid: int, msgid: int):
    msg = await acc.get_messages(chatid, msgid)
    msg_type = get_message_type(msg)

    if "Text" == msg_type:
        await bot.send_message(message.chat.id, msg.text, entities=msg.entities, reply_to_message_id=message.id)
        return

    smsg = await bot.send_message(message.chat.id, '__Downloading__', reply_to_message_id=message.id)
    dosta = threading.Thread(target=lambda: downstatus(f'{message.id}downstatus.txt', smsg), daemon=True)
    dosta.start()
    file = await acc.download_media(msg, progress=progress, progress_args=[message, "down"])
    os.remove(f'{message.id}downstatus.txt')

    upsta = threading.Thread(target=lambda: upstatus(f'{message.id}upstatus.txt', smsg), daemon=True)
    upsta.start()

    if "Document" == msg_type:
        try:
            thumb = await acc.download_media(msg.document.thumbs[0].file_id)
        except:
            thumb = None

        await bot.send_document(message.chat.id, file, thumb=thumb, caption=msg.caption, caption_entities=msg.caption_entities, reply_to_message_id=message.id, progress=progress, progress_args=[message, "up"])
        if thumb is not None:
            os.remove(thumb)

    elif "Video" == msg_type:
        try:
            thumb = await acc.download_media(msg.video.thumbs[0].file_id)
        except:
            thumb = None

        await bot.send_video(message.chat.id, file, duration=msg.video.duration, width=msg.video.width, height=msg.video.height, thumb=thumb, caption=msg.caption, caption_entities=msg.caption_entities, reply_to_message_id=message.id, progress=progress, progress_args=[message, "up"])
        if thumb is not None:
            os.remove(thumb)

    elif "Animation" == msg_type:
        await bot.send_animation(message.chat.id, file, reply_to_message_id=message.id)

    elif "Sticker" == msg_type:
        await bot.send_sticker(message.chat.id, file, reply_to_message_id=message.id)

    elif "Voice" == msg_type:
        await bot.send_voice(message.chat.id, file, caption=msg.caption, thumb=thumb, caption_entities=msg.caption_entities, reply_to_message_id=message.id, progress=progress, progress_args=[message, "up"])

    elif "Audio" == msg_type:
        try:
            thumb = await acc.download_media(msg.audio.thumbs[0].file_id)
        except:
            thumb = None

        await bot.send_audio(message.chat.id, file, caption=msg.caption, caption_entities=msg.caption_entities, reply_to_message_id=message.id, progress=progress, progress_args=[message, "up"])
        if thumb is not None:
            os.remove(thumb)

    elif "Photo" == msg_type:
        await bot.send_photo(message.chat.id, file, caption=msg.caption, caption_entities=msg.caption_entities, reply_to_message_id=message.id)

    os.remove(file)
    if os.path.exists(f'{message.id}upstatus.txt'):
        os.remove(f'{message.id}upstatus.txt')
    await bot.delete_messages(message.chat.id, [smsg.id])


# Get the type of message
def get_message_type(msg: pyrogram.types.Message):
    try:
        msg.document.file_id
        return "Document"
    except:
        pass

    try:
        msg.video.file_id
        return "Video"
    except:
        pass

    try:
        msg.animation.file_id
        return "Animation"
    except:
        pass

    try:
        msg.sticker.file_id
        return "Sticker"
    except:
        pass

    try:
        msg.voice.file_id
        return "Voice"
    except:
        pass

    try:
        msg.audio.file_id
        return "Audio"
    except:
        pass

    try:
        msg.photo.file_id
        return "Photo"
    except:
        pass

    try:
        msg.text
        return "Text"
    except:
        pass


USAGE = """**FOR PUBLIC CHATS**

**__Just send the post(s) link__**

**FOR PRIVATE CHATS**

**__First send the invite link of the chat (unnecessary if the account of string session is already a member of the chat)
then send the post(s) link__**

**FOR BOT CHATS**

**__Send the link with** '/b/', **the bot's username, and message id. You might want to install some unofficial client to get the id like below__**

https://t.me/b/botusername/4321

**MULTI POSTS**

**__Send public/private post links as explained above with the format "from - to" to send multiple messages like below__**

https://t.me/xxxx/1001-1010

https://t.me/c/xxxx/101 - 120

**__Note that space in between doesn't matter__**
"""


# Infinity polling
bot.run()
