import os, re, json, base64, logging, random, asyncio

from Script import script
from database.users_chats_db import db
from pyrogram import Client, filters, enums
from pyrogram.errors import ChatAdminRequired, FloodWait
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from database.ia_filterdb import Media, get_file_details, unpack_new_file_id
from info import CHANNELS, ADMINS, AUTH_CHANNEL, LOG_CHANNEL, PICS, BATCH_FILE_CAPTION, CUSTOM_FILE_CAPTION, PROTECT_CONTENT, START_MESSAGE, FORCE_SUB_TEXT, SUPPORT_CHAT
from utils import get_settings, get_size, is_subscribed, save_group_settings, temp
from database.connections_mdb import active_connection

logger = logging.getLogger(__name__)
BATCH_FILES = {}
 
    
@Client.on_message(filters.command("start") & filters.incoming)
async def start(client, message):
    if message.chat.type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        buttons = [[
            InlineKeyboardButton('📢 Uᴩᴅᴀᴛᴇꜱ 📢', url=f'https://t.me/{SUPPORT_CHAT}')
        ],[
            InlineKeyboardButton('ℹ️ Hᴇʟᴩ ℹ️', url=f"https://t.me/{temp.U_NAME}?start=help")
        ]]
        await message.reply(
            START_MESSAGE.format(
                user=message.from_user.mention if message.from_user else message.chat.title,
                bot=client.mention),
            reply_markup=InlineKeyboardMarkup(buttons),
            disable_web_page_preview=True
        )
        await asyncio.sleep(2)
        if not await db.get_chat(message.chat.id):
            total = await client.get_chat_members_count(message.chat.id)
            await client.send_message(
                LOG_CHANNEL,
                script.LOG_TEXT_G.format(
                    a=message.chat.title,
                    b=message.chat.id,
                    c=message.chat.username,
                    d=total,
                    f=client.mention,
                    e="Unknown"
                )
            )
            await db.add_chat(message.chat.id, message.chat.title, message.chat.username)
        return

    if not await db.is_user_exist(message.from_user.id):
        await db.add_user(message.from_user.id, message.from_user.first_name)
        await client.send_message(
            LOG_CHANNEL,
            script.LOG_TEXT_P.format(message.from_user.id, message.from_user.mention, message.from_user.username, temp.U_NAME)
        )

    if len(message.command) != 2:
        buttons = [[
            InlineKeyboardButton("ʀᴇǫᴜᴇsᴛ ᴍᴏᴠɪᴇs ʜᴇʀᴇ", url="https://t.me/moxi_movies_grp")
        ],[
            InlineKeyboardButton("Sᴇᴀʀᴄʜ 🔎", switch_inline_query_current_chat=''),
            InlineKeyboardButton("Cʜᴀɴɴᴇʟ 🔈", url="https://t.me/mkn_bots_updates")
        ],[
            InlineKeyboardButton("Hᴇʟᴩ 🕸️", callback_data="help"),
            InlineKeyboardButton("Aʙᴏᴜᴛ ✨", callback_data="about")
        ]]
        m = await message.reply_sticker("CAACAgUAAxkBAAEBvlVk7YKnYxIHVnKW2PUwoibIR2ygGAACBAADwSQxMYnlHW4Ls8gQHgQ")
        await asyncio.sleep(2)
        await message.reply_photo(
            photo=random.choice(PICS),
            caption=START_MESSAGE.format(user=message.from_user.mention, bot=client.mention),
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode=enums.ParseMode.HTML
        )
        return await m.delete()

    data = message.command[1]
    try:
        pre, file_id = data.split('_', 1)
    except:
        file_id = data
        pre = ""

    files_ = await get_file_details(file_id)
    if not files_:
        try:
            pre, file_id = ((base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))).decode("ascii")).split("_", 1)
        except:
            return await message.reply('NO SUCH FILE EXIST...')
        try:
            msg = await client.send_cached_media(
                chat_id=message.from_user.id,
                file_id=file_id,
                protect_content=True if pre == 'filep' else False,
            )
            filetype = msg.media
            file = getattr(msg, filetype)
            title = file.file_name
            size = get_size(file.file_size)
            f_caption = f"<code>{title}</code>"
            if CUSTOM_FILE_CAPTION:
                try:
                    f_caption = CUSTOM_FILE_CAPTION.format(
                        mention=message.from_user.mention,
                        file_name=title or '',
                        file_size=size or '',
                        file_caption=''
                    )
                except:
                    return
            return await msg.edit_caption(f_caption)
        except:
            return await message.reply('NO SUCH FILE EXIST...')

    files = files_[0]
    title = files.file_name
    size = get_size(files.file_size)
    f_caption = files.caption

    if CUSTOM_FILE_CAPTION:
        try:
            f_caption = CUSTOM_FILE_CAPTION.format(
                mention=message.from_user.mention,
                file_name=title or '',
                file_size=size or '',
                file_caption=f_caption or ''
            )
        except Exception as e:
            logger.exception(e)

    if f_caption is None:
        f_caption = title

    # Send file and handle auto-delete
    try:
        sent_msg = await client.send_cached_media(
            chat_id=message.from_user.id,
            file_id=file_id,
            caption=f_caption,
            protect_content=True if pre == 'filep' else False,
        )

        async def delete_later(msg):
            await asyncio.sleep(600)
            try:
                await msg.delete()
                await client.send_message(
                    message.from_user.id,
                    "⛔️ This file has been deleted to avoid copyright issues.",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔁 Request Again", url="https://t.me/moxi_movies_grp")
                    ]])
                )
            except Exception as e:
                print(f"[AutoDelete] Error: {e}")

        asyncio.create_task(delete_later(sent_msg))

    except Exception as e:
        logger.error(f"File send failed: {e}")
        await message.reply("❌ Unable to send the file. It might be deleted or inaccessible.")


from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ChatType
import asyncio

@Client.on_message(filters.private & (filters.document | filters.video | filters.audio | filters.photo | filters.animation | filters.voice))
async def auto_delete_media(client: Client, message: Message):
    await asyncio.sleep(600)  # wait 10 minutes
    try:
        await message.delete()  
    except Exception as e:
        print(f"Error deleting message: {e}")
        
@Client.on_message(filters.command('channel') & filters.user(ADMINS))
async def channel_info(bot, message):
    if isinstance(CHANNELS, (int, str)): channels = [CHANNELS]
    elif isinstance(CHANNELS, list): channels = CHANNELS
    else: raise ValueError("Unexpected Type Of CHANNELS")
    text = '📑 **Indexed channels/groups**\n'
    for channel in channels:
        chat = await bot.get_chat(channel)
        if chat.username: text += '\n@' + chat.username
        else: text += '\n' + chat.title or chat.first_name
    text += f'\n\n**Total:** {len(CHANNELS)}'
    if len(text) < 4096: await message.reply(text)
    else:
        file = 'Indexed channels.txt'
        with open(file, 'w') as f:
            f.write(text)
        await message.reply_document(file)
        os.remove(file)


@Client.on_message(filters.command('delete') & filters.user(ADMINS))
async def delete(bot, message):
    reply = message.reply_to_message
    if reply and reply.media: msg = await message.reply("Processing...⏳", quote=True)
    else: return await message.reply('Reply to file with /delete which you want to delete', quote=True)
    for file_type in ("document", "video", "audio"):
        media = getattr(reply, file_type, None)
        if media is not None: break
    else: return await msg.edit('This Is Not Supported File Format')
    file_id, file_ref = unpack_new_file_id(media.file_id)
    result = await Media.collection.delete_one({'_id': file_id})
    if result.deleted_count: await msg.edit('File Is Successfully Deleted From Database')
    else:
        file_name = re.sub(r"(_|\-|\.|\+)", " ", str(media.file_name))
        result = await Media.collection.delete_many({
            'file_name': file_name,
            'file_size': media.file_size,
            'mime_type': media.mime_type
            })
        if result.deleted_count: await msg.edit('File Is Successfully Deleted From Database')
        else:
            result = await Media.collection.delete_many({
                'file_name': media.file_name,
                'file_size': media.file_size,
                'mime_type': media.mime_type
            })
            if result.deleted_count: await msg.edit('File Is Successfully Deleted From Database')
            else: await msg.edit('File Not Found In Database')


@Client.on_message(filters.command('deleteall') & filters.user(ADMINS))
async def delete_all_index(bot, message):
    button = [[
        InlineKeyboardButton("YES", callback_data="autofilter_delete")
        ],[
        InlineKeyboardButton("CANCEL", callback_data="close_data")
    ]]
    await message.reply_text('This Will Delete All Indexed Files.\ndo You Want To Continue??', quote=True, reply_markup=InlineKeyboardMarkup(button))
            

@Client.on_callback_query(filters.regex(r'^autofilter_delete'))
async def delete_all_index_confirm(bot, message):
    await Media.collection.drop()
    await message.message.edit('Succesfully Deleted All The Indexed Files.')


@Client.on_message(filters.command('settings'))
async def settings(client, message):
    userid = message.from_user.id if message.from_user else None
    if not userid: return await message.reply(f"Yᴏᴜ Aʀᴇ Aɴᴏɴʏᴍᴏᴜs Aᴅᴍɪɴ. Usᴇ /connect {message.chat.id} Iɴ PM")
    chat_type = message.chat.type
    if chat_type == enums.ChatType.PRIVATE:
        grpid = await active_connection(str(userid))
        if grpid is not None:
            grp_id = grpid
            try:
                chat = await client.get_chat(grpid)
                title = chat.title
            except:
                return await message.reply_text("Mᴀᴋᴇ Sᴜʀᴇ I'ᴍ Pʀᴇsᴇɴᴛ Iɴ Yᴏᴜʀ Gʀᴏᴜᴘ!!", quote=True)
        else: return await message.reply_text("I'ᴍ Nᴏᴛ Cᴏɴɴᴇᴄᴛᴇᴅ Tᴏ Aɴʏ Gʀᴏᴜᴘs!", quote=True)

    elif chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        grp_id = message.chat.id
        title = message.chat.title
    else: return

    st = await client.get_chat_member(grp_id, userid)
    if (
        st.status != enums.ChatMemberStatus.ADMINISTRATOR
        and st.status != enums.ChatMemberStatus.OWNER
        and str(userid) not in ADMINS
    ): return

    settings = await get_settings(grp_id)
    if settings is not None:
        buttons = [[
            InlineKeyboardButton(f"ꜰɪʟᴛᴇʀ ʙᴜᴛᴛᴏɴ : {'sɪɴɢʟᴇ' if settings['button'] else 'ᴅᴏᴜʙʟᴇ'}", f'setgs#button#{settings["button"]}#{str(grp_id)}')
            ],[
            InlineKeyboardButton(f"ꜰɪʟᴇ ɪɴ ᴩᴍ ꜱᴛᴀʀᴛ: {'ᴏɴ' if settings['botpm'] else 'ᴏꜰꜰ'}", f'setgs#botpm#{settings["botpm"]}#{str(grp_id)}')
            ],[                
            InlineKeyboardButton(f"ʀᴇꜱᴛʀɪᴄᴛ ᴄᴏɴᴛᴇɴᴛ : {'ᴏɴ' if settings['file_secure'] else 'ᴏꜰꜰ'}", f'setgs#file_secure#{settings["file_secure"]}#{str(grp_id)}')
            ],[
            InlineKeyboardButton(f"ɪᴍᴅʙ ɪɴ ꜰɪʟᴛᴇʀ : {'ᴏɴ' if settings['imdb'] else 'ᴏꜰꜰ'}", f'setgs#imdb#{settings["imdb"]}#{str(grp_id)}')
            ],[
            InlineKeyboardButton(f"ꜱᴩᴇʟʟɪɴɢ ᴄʜᴇᴄᴋ : {'ᴏɴ' if settings['spell_check'] else 'ᴏꜰꜰ'}", f'setgs#spell_check#{settings["spell_check"]}#{str(grp_id)}')
            ],[
            InlineKeyboardButton(f"ᴡᴇʟᴄᴏᴍᴇ ᴍᴇꜱꜱᴀɢᴇ : {'ᴏɴ' if settings['welcome'] else 'ᴏꜰꜰ'}", f'setgs#welcome#{settings["welcome"]}#{str(grp_id)}')
        ]]
        await message.reply_text(
            text=f"<b>Cʜᴀɴɢᴇ Yᴏᴜʀ Sᴇᴛᴛɪɴɢꜱ Fᴏʀ {title} Aꜱ Yᴏᴜʀ Wɪꜱʜ ⚙</b>",
            reply_markup=InlineKeyboardMarkup(buttons),
            quote=True, 
            disable_web_page_preview=True,
            parse_mode=enums.ParseMode.HTML,
        )



@Client.on_message(filters.command('set_template'))
async def save_template(client, message):
    sts = await message.reply("Cʜᴇᴄᴋɪɴɢ Tᴇᴍᴘʟᴀᴛᴇ")
    userid = message.from_user.id if message.from_user else None
    if not userid: return await message.reply(f"Yᴏᴜ Aʀᴇ Aɴᴏɴʏᴍᴏᴜs Aᴅᴍɪɴ. Usᴇ /connect {message.chat.id} Iɴ PM")
    chat_type = message.chat.type
    if chat_type == enums.ChatType.PRIVATE:
        grpid = await active_connection(str(userid))
        if grpid is not None:
            grp_id = grpid
            try:
                chat = await client.get_chat(grpid)
                title = chat.title
            except:
                return await message.reply_text("Mᴀᴋᴇ Sᴜʀᴇ I'ᴍ Pʀᴇsᴇɴᴛ Iɴ Yᴏᴜʀ Gʀᴏᴜᴘ !!", quote=True)
        else:
            return await message.reply_text("I'ᴍ Nᴏᴛ Cᴏɴɴᴇᴄᴛᴇᴅ Tᴏ Aɴʏ Gʀᴏᴜᴘs!", quote=True)
    elif chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        grp_id = message.chat.id
        title = message.chat.title
    else: return
    st = await client.get_chat_member(grp_id, userid)
    if (
        st.status != enums.ChatMemberStatus.ADMINISTRATOR
        and st.status != enums.ChatMemberStatus.OWNER
        and str(userid) not in ADMINS
    ): return
    if len(message.command) < 2: return await sts.edit("No Iɴᴩᴜᴛ!!")
    template = message.text.split(" ", 1)[1]
    await save_group_settings(grp_id, 'template', template)
    await sts.edit(f"Sᴜᴄᴄᴇssғᴜʟʟʏ Cʜᴀɴɢᴇᴅ Tᴇᴍᴘʟᴀᴛᴇ Fᴏʀ {title} Tᴏ\n\n{template}")


@Client.on_message(filters.command('get_template'))
async def geg_template(client, message):
    sts = await message.reply("Cʜᴇᴄᴋɪɴɢ Tᴇᴍᴘʟᴀᴛᴇ")
    userid = message.from_user.id if message.from_user else None
    if not userid: return await message.reply(f"Yᴏᴜ Aʀᴇ Aɴᴏɴʏᴍᴏᴜs Aᴅᴍɪɴ. Usᴇ /connect {message.chat.id} Iɴ PM")
    chat_type = message.chat.type
    if chat_type == enums.ChatType.PRIVATE:
        grpid = await active_connection(str(userid))
        if grpid is not None:
            grp_id = grpid
            try:
                chat = await client.get_chat(grpid)
                title = chat.title
            except:
                return await message.reply_text("Mᴀᴋᴇ Sᴜʀᴇ I'ᴍ Pʀᴇsᴇɴᴛ Iɴ Yᴏᴜʀ Gʀᴏᴜᴘ !!", quote=True)
        else:
            return await message.reply_text("I'ᴍ Nᴏᴛ Cᴏɴɴᴇᴄᴛᴇᴅ Tᴏ Aɴʏ Gʀᴏᴜᴘs!", quote=True)
    elif chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        grp_id = message.chat.id
        title = message.chat.title
    else: return
    st = await client.get_chat_member(grp_id, userid)
    if (
        st.status != enums.ChatMemberStatus.ADMINISTRATOR
        and st.status != enums.ChatMemberStatus.OWNER
        and str(userid) not in ADMINS
    ): return
    settings = await get_settings(grp_id)
    template = settings['template']
    await sts.edit(f"Cᴜʀʀᴇɴᴛ Tᴇᴍᴘʟᴀᴛᴇ Fᴏʀ {title} Iꜱ\n\n{template}")



