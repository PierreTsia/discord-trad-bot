import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from src import db
from discord.ext.commands import has_permissions, CheckFailure
from googletrans import Translator
import re
import aiosqlite

# Load environment variables
load_dotenv()

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Supported language codes (Google Translate ISO 639-1)
SUPPORTED_LANGUAGES = {
    'af', 'sq', 'am', 'ar', 'hy', 'az', 'eu', 'be', 'bn', 'bs', 'bg', 'ca', 'ceb', 'zh-cn', 'zh-tw', 'co', 'hr', 'cs', 'da', 'nl', 'en', 'eo', 'et', 'fi', 'fr', 'fy', 'gl', 'ka', 'de', 'el', 'gu', 'ht', 'ha', 'haw', 'he', 'hi', 'hmn', 'hu', 'is', 'ig', 'id', 'ga', 'it', 'ja', 'jw', 'kn', 'kk', 'km', 'rw', 'ko', 'ku', 'ky', 'lo', 'la', 'lv', 'lt', 'lb', 'mk', 'mg', 'ms', 'ml', 'mt', 'mi', 'mr', 'mn', 'my', 'ne', 'no', 'ny', 'or', 'ps', 'fa', 'pl', 'pt', 'pa', 'ro', 'ru', 'sm', 'gd', 'sr', 'st', 'sn', 'sd', 'si', 'sk', 'sl', 'so', 'es', 'su', 'sw', 'sv', 'tl', 'tg', 'ta', 'tt', 'te', 'th', 'tr', 'tk', 'uk', 'ur', 'ug', 'uz', 'vi', 'cy', 'xh', 'yi', 'yo', 'zu'
}

translator = Translator()

# --- Helper Functions ---
def preserve_user_mentions(text):
    """Replace user mentions with robust placeholders and return (text_with_placeholders, mention_map)."""
    mention_map = {}
    def mention_replacer(match):
        user_id = match.group(1)
        placeholder = f"[[[MENTION{len(mention_map)+1}]]]"
        mention_map[placeholder] = f"<@{user_id}>"
        return placeholder
    text_with_placeholders = re.sub(r'<@!?([0-9]+)>', mention_replacer, text)
    return text_with_placeholders, mention_map

def restore_mentions(text, mention_map):
    """Restore mentions in text using the mention_map (case-insensitive)."""
    for placeholder, mention in mention_map.items():
        text = re.sub(re.escape(placeholder), mention, text, flags=re.IGNORECASE)
    return text

def translate_message(content, dest_lang):
    """Translate content to dest_lang using googletrans."""
    return translator.translate(content, dest=dest_lang).text

def detect_language(content):
    """Detect the language of the content using googletrans."""
    try:
        detected = translator.detect(content)
        return detected.lang
    except Exception:
        return None

# --- Bot Events and Commands ---
@bot.event
async def on_ready():
    await db.init_db()
    print(f'{bot.user} has connected to Discord!')

@bot.command(name='ping')
async def ping(ctx):
    """Simple command to test if the bot is working"""
    await ctx.send('Pong!')

@bot.command(name='debugdb')
@has_permissions(administrator=True)
async def debugdb(ctx):
    """Debug command to check database schema and content"""
    try:
        # Get all translation channels
        channels = await db.get_trans_channels()
        channels_info = "\n".join([f"Channel ID: {ch[0]}, Default Lang: {ch[1]}" for ch in channels])
        
        # Get some user preferences (limit to 5 for readability)
        async with aiosqlite.connect(db.DB_PATH) as conn:
            async with conn.execute('SELECT user_id, lang FROM user_lang LIMIT 5') as cursor:
                users = await cursor.fetchall()
        users_info = "\n".join([f"User ID: {u[0]}, Lang: {u[1]}" for u in users])
        
        # Get table info
        async with aiosqlite.connect(db.DB_PATH) as conn:
            async with conn.execute("SELECT name FROM sqlite_master WHERE type='table'") as cursor:
                tables = await cursor.fetchall()
        tables_info = "\n".join([f"Table: {t[0]}" for t in tables])
        
        # Format the response
        response = f"""**Database Debug Info:**
        
**Tables:**
{tables_info}

**Translation Channels:**
{channels_info}

**Sample User Preferences (up to 5):**
{users_info}"""
        
        await ctx.send(response)
    except Exception as e:
        await ctx.send(f"Error checking database: {str(e)}")

@debugdb.error
async def debugdb_error(ctx, error):
    if isinstance(error, CheckFailure):
        await ctx.send('You need to be an administrator to use this command.')

@bot.command(name='setlang')
async def setlang(ctx, lang: str):
    """Set your preferred language. Usage: !setlang <language_code>"""
    lang = lang.lower()
    if lang not in SUPPORTED_LANGUAGES:
        await ctx.send(f'`{lang}` is not a supported language code. Use `!languages` to see the list of supported codes.')
        return
    await db.set_user_lang(ctx.author.id, lang)
    await ctx.send(f'Your preferred language has been set to `{lang}`.')

@bot.command(name='languages')
async def languages(ctx):
    """List all supported language codes."""
    codes = sorted(SUPPORTED_LANGUAGES)
    chunk_size = 50
    for i in range(0, len(codes), chunk_size):
        await ctx.send(' '.join(codes[i:i+chunk_size]))

@bot.command(name='mylang')
async def mylang(ctx):
    """Show your current preferred language."""
    user_lang = await db.get_user_lang(ctx.author.id)
    if user_lang:
        await ctx.send(f'Your preferred language is `{user_lang}`.')
    else:
        await ctx.send('You have not set a preferred language yet. Use `!setlang <language_code>`.')

@bot.command(name='settranschannel')
@has_permissions(administrator=True)
async def settranschannel(ctx, channel: discord.TextChannel = None):
    """Set the translation channel. Usage: !settranschannel #channel (or run in the channel to set it)"""
    if channel is None:
        channel = ctx.channel
    await db.add_trans_channel(channel.id)
    await ctx.send(f'Translation channel added: {channel.mention}')

@bot.command(name='addtranschannel')
@has_permissions(administrator=True)
async def addtranschannel(ctx, channel: discord.TextChannel):
    """Add a new translation channel. Usage: !addtranschannel #channel"""
    if not await db.is_trans_channel(channel.id):
        await db.add_trans_channel(channel.id)
        await ctx.send(f'Translation channel added: {channel.mention}')
    else:
        await ctx.send(f'{channel.mention} is already a translation channel.')

@bot.command(name='removetranschannel')
@has_permissions(administrator=True)
async def removetranschannel(ctx, channel: discord.TextChannel):
    """Remove a translation channel. Usage: !removetranschannel #channel"""
    if not await db.is_trans_channel(channel.id):
        await ctx.send(f'{channel.mention} is not a translation channel.')
        return
    await db.remove_trans_channel(channel.id)
    await ctx.send(f'Translation channel removed: {channel.mention}')

@bot.command(name='listtranschannels')
@has_permissions(administrator=True)
async def listtranschannels(ctx):
    """List all translation channels and their default languages."""
    channels = await db.get_trans_channels()
    if not channels:
        await ctx.send('No translation channels configured.')
        return
    
    channel_list = []
    for channel_id, default_lang in channels:
        channel = ctx.guild.get_channel(channel_id)
        if channel:
            channel_list.append(f"{channel.mention} (default: {default_lang})")
    
    await ctx.send("**Translation Channels:**\n" + "\n".join(channel_list))

@bot.command(name='setchannellang')
@has_permissions(administrator=True)
async def setchannellang(ctx, channel: discord.TextChannel, lang: str):
    """Set the default language for a translation channel. Usage: !setchannellang #channel <language_code>"""
    if not await db.is_trans_channel(channel.id):
        await ctx.send(f'{channel.mention} is not a translation channel.')
        return
    if lang not in SUPPORTED_LANGUAGES:
        await ctx.send(f'`{lang}` is not a supported language code. Use `!languages` to see the list of supported codes.')
        return
    await db.set_channel_default_lang(channel.id, lang)
    await ctx.send(f'Default language for {channel.mention} set to `{lang}`')

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    
    # Skip translation for commands
    if message.content.startswith('!'):
        await bot.process_commands(message)
        return
    
    # Check if the message is in a translation channel
    if await db.is_trans_channel(message.channel.id):
        user_lang = await db.get_user_lang(message.author.id)
        if not user_lang:
            # Use channel's default language if user hasn't set one
            user_lang = await db.get_channel_default_lang(message.channel.id)
        
        # Preserve user mentions
        content_preserved, mention_map = preserve_user_mentions(message.content)
        detected_lang = detect_language(content_preserved)
        
        # Only translate if the message isn't already in the user's preferred language
        if detected_lang and detected_lang != user_lang:
            try:
                translated_text = translate_message(content_preserved, user_lang)
                translated_text = restore_mentions(translated_text, mention_map)
                await message.reply(f"{translated_text}")
            except Exception as e:
                await message.reply(f"[Translation error: {e}]")
        else:
            content_preserved = restore_mentions(content_preserved, mention_map)
            await message.reply(f"{content_preserved}")
    
    await bot.process_commands(message)

# Run the bot
if __name__ == '__main__':
    bot.run(os.getenv('DISCORD_TOKEN')) 