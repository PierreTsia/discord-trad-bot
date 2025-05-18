import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from src import db
from discord.ext.commands import has_permissions, CheckFailure
from googletrans import Translator

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

@bot.event
async def on_ready():
    await db.init_db()
    print(f'{bot.user} has connected to Discord!')

@bot.command(name='ping')
async def ping(ctx):
    """Simple command to test if the bot is working"""
    await ctx.send('Pong!')

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
    # Discord has a 2000 character message limit, so chunk if needed
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
    await db.set_trans_channel(channel.id)
    await ctx.send(f'Translation channel set to {channel.mention}')

@settranschannel.error
async def settranschannel_error(ctx, error):
    if isinstance(error, CheckFailure):
        await ctx.send('You need to be an administrator to use this command.')

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    trans_channel_id = await db.get_trans_channel()
    if trans_channel_id and message.channel.id == trans_channel_id:
        user_lang = await db.get_user_lang(message.author.id)
        if not user_lang:
            user_lang = 'en'  # Default to English
        # Try to detect the language of the message
        try:
            detected = translator.detect(message.content)
            detected_lang = detected.lang
        except Exception:
            detected_lang = None
        # Only translate if the message isn't already in the user's preferred language
        if detected_lang and detected_lang != user_lang:
            try:
                translated = translator.translate(message.content, dest=user_lang)
                await message.reply(f"{translated.text}")
            except Exception as e:
                await message.reply(f"[Translation error: {e}]")
        else:
            await message.reply(f"{message.content}")
    await bot.process_commands(message)

# Run the bot
if __name__ == '__main__':
    bot.run(os.getenv('DISCORD_TOKEN')) 