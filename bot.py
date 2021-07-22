import re
import os
import asyncio
from subprocess import getstatusoutput
from config import Config
from pyrogram.types.messages_and_media import message
from telegram_upload import files
from pyrogram import Client
from pyrogram import filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from bs4 import BeautifulSoup

API_ID = int(os.environ.get("API_ID", Config.API_ID))
API_HASH = os.environ.get("API_HASH", Config.API_HASH)
BOT_TOKEN = os.environ.get("BOT_TOKEN", Config.BOT_TOKEN)

bot = Client("bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)


@bot.on_message(filters.command("start"))
async def start(bot, message):
    await message.reply("Send video link or html")


async def send_video(message, path, caption):
    atr = files.get_file_attributes(path)
    duration = atr[0].duration
    width = atr[0].w
    height = atr[0].h
    thumb = "thumb.png"
    await message.reply_video(
        video=path,
        caption=caption,
        duration=duration,
        width=width,
        height=height,
        thumb=thumb,
        supports_streaming=True,
        quote=False
    )


# @bot.on_message(filters.document)
# async def choose_format(bot, message):
    # if message.document["mime_type"] == "text/html":
        # file = (
            # "./downloads/"
            # + str(message.from_user.id)
            # + "/"
            # + message.document.file_id
            # + ".html"
        # )
        # await message.download(file)

        # with open(file, "r") as f:
            # source = f.read()

        # soup = BeautifulSoup(source, "html.parser")

        # formats = ["144", "240", "360", "480", "720"]
        # buttons = []
        # for format in formats:
            # buttons.append(
                # InlineKeyboardButton(text=format + "p", callback_data=format)
            # )
        # buttons_markup = InlineKeyboardMarkup([buttons])

        # paras = soup.find_all("p")
        # title = paras[0].string
        # await message.reply(title, quote=True, reply_markup=buttons_markup)
        # os.remove(file)


# @bot.on_callback_query()
# async def upload(bot, query):
    # message = query.message.reply_to_message
    # format = query.data
    # file = (
        # "./downloads/"
        # + str(message.from_user.id)
        # + "/"
        # + message.document.file_id
        # + ".html"
    # )
    # await message.download(file)

    # with open(file, "r") as f:
        # source = f.read()

    # soup = BeautifulSoup(source, "html.parser")

    # vids = "".join(
        # [
            # str(tag)
            # for tag in soup.find_all("p", style="text-align:center;font-size:25px;")
        # ]
    # )
    # vids_soup = BeautifulSoup(vids, "html.parser")
    # links = [link.extract().text for link in vids_soup.findAll("a")]
    # name = re.compile("\d+\..*?(?=<br/>)")
    # names = name.findall(vids)
    # vids_dict = dict(zip(names, links))

    # for vid in vids_dict:
        # vid_name = vid + ".mp4"
        # vid_path = "./downloads/" + str(message.from_user.id) + "/" + vid_name
        # vid_link = vids_dict[vid]
        # command = (
            # "youtube-dl -o '"
            # + vid_path
            # + "' -f 'bestvideo[height="+format+"]+bestaudio' "
            # + vid_link
        # )
        # os.system(command)
        # await message.reply_chat_action("upload_video")
        # await send_video(message, vid_path, vid)
        # os.remove(vid_path)

async def download_video(message, video):
    chat = message.chat.id
    index = video[0]
    link = video[1]
    vid_format = video[2]
    title = video[3]
    topic = video[4]
    st1, yt_title  = getstatusoutput(f"yt-dlp -e  --no-warning '{link}' -R 50")
    if st1 == 1:
        await message.reply(f"Can't download. Probably DRM\n\nLink: {link}", quote=False)
        return
    if title == '':
        title = yt_title
    caption = f"Link: {link}\n\nTitle: {title}\n\nTopic: {topic}"

    if 'youtu' in link:
        if vid_format == '144':
            ytf = 160
        elif vid_format == '240':
            ytf = 133
        elif vid_format == '360':
            ytf = 18
        elif vid_format == '480':
            ytf = 135
        elif vid_format == '720':
            ytf = 22
        else:
            ytf = 18
    elif ('deshdeepak' in link and len(link.split('/')[-1]) == 13) or ('magnetoscript' in link and ('brightcove' in link or len(link.split('/')[-1]) == 13)):
        if vid_format not in ['144', '240', '360', '480', '720']:
            vid_format = '360'
        ytf = f"'bestvideo[height<={vid_format}]+bestaudio'"
    elif ('deshdeepak' in link and len(link.split('/')[-1]) == 8) or ('magnetoscript' in link and 'jwp' in link) :
        if vid_format == '144':
            vid_format == '180'
        elif vid_format == '240':
            vid_format == '270'
        elif vid_format == '360':
            vid_format == '360'
        elif vid_format == '480':
            vid_format == '540'
        elif vid_format == '720':
            vid_format == '720'
        else:
            vid_format = '360'
        ytf = f"'best[height<={vid_format}]'"
    else:
        return

    cmd = f"yt-dlp -o './download/{chat}/%(id)s.%(ext)s' -f {ytf} --no-warning '{link}'"
    filename_cmd = f"{cmd} --get-filename -R 25"
    st2, filename = getstatusoutput(filename_cmd)
    if st2 != 0:
        await message.reply(f"Can't Download.\n\nTitle: {title}\n\nLink: {link}", quote=False)
        return
    download_cmd = f"{cmd} -R 25 --fragment-retries 25"
    st3, out = getstatusoutput(download_cmd)
    if st3 != 0:
        await message.reply(f"Can't download.\n\nTitle: {title}\n\nLink: {link}", quote=False)
        return
    else:
        path = filename
        await send_video(message, path, caption)



async def download_videos(message, videos):
    videos = [(videos.index(video), video[0], video[1], video[2], video[3]) for video in videos]
    asyncio.gather(*(download_video(message, video) for video in videos))



@bot.on_callback_query()
async def choose_format(bot, query):
    message = query.message.reply_to_message
    def_format = query.data
    command = message.text.split()
    req_videos = command[1:-1]
    videos = []
    for video in req_videos:
        video_parts = video.split('|')
        video_link = video_parts[0]
        video_format = video_parts[1] if len(video_parts) == 2 and video_parts[1] != '' else def_format
        videos.append((video_link, video_format, '', ''))

    await message.reply('Downloading!!!')
    await download_videos(message, videos)


@bot.on_message(filters.command("download_link"))
async def download_link(bot, message):
    if len(message.command) == 1:
        await message.reply(
                "Send video link(s) separated by space, and format separated by | or f at end to choose format (optional) \n\n"
                + "e.g. /downloadLink https://link1|360 http://link2 http://link3|480 \n\n"
                + "e.g. /downloadLink http://link1 http://link2 f"
                )
        return
    if message.command[-1] == 'f':
        formats = ["144", "240", "360", "480", "720"]
        buttons = []
        for def_format in formats:
            buttons.append(
                InlineKeyboardButton(text=def_format + "p", callback_data=def_format)
            )
        buttons_markup = InlineKeyboardMarkup([buttons])
        await message.reply("Choose Format", quote=True, reply_markup=buttons_markup)
    else:
        req_videos = message.command[1:]
        def_format = "360"
        videos = []
        for video in req_videos:
            video_parts = video.split('|')
            video_link = video_parts[0]
            video_format = video_parts[1] if len(video_parts) == 2 and video_parts[1] != '' else def_format
            videos.append((video_link, video_format, '', ''))

        await message.reply('Downloading!!!')
        await download_videos(message, videos)


bot.run()
