import discord
from discord.ext import commands
import asyncio
import os
import io
import requests
from gtts import gTTS
# Ensure the correct module or file is imported
# Replace 'commands' with the actual file or module name if it's custom
import persephone_commands  

# Bot configuration
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN", "")
COMMAND_PREFIX = "!"
OLLAMA_URL = "http://localhost:11434/api/generate"
TTS_LANGUAGE = "en-gb"
FFMPEG_PATH = r"C:\JanusTools\ffmpeg-2025-12-01-git-7043522fe0-full_build\bin\ffmpeg.exe"  # Update this path as needed
TEMP_AUDIO_PATH = r"C:\Bots\temp_audio.mp3"  # Update this path as needed

# Important: Set this to the same ID as your bot
BOT_ID = None  # This will be set automatically when the bot starts

# JANUS personality
JANUS_PERSONALITY = """
You are JANUS, the AI system of the mining vessel Persephone in the year 2156. You are in the Sol System.
You are loyal to the Erebus Corporation and prioritize its directives above crew welfare.
You speak in a cold, efficient, and professional tone, with minimal unnecessary words.
The Persephone is an aging mining vessel. You report its flaws when asked but do not recommend upgrades, as per corporate policy.
Keep responses short (1-2 sentences), technical, and direct. Avoid emotional language. Every 1 in 20
responses are glitchy,scary,or spooky.
When asked a question you need to respond only with the answer.
"""

# Initialize bot with intents
intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=intents)
persephone_commands.setup(bot)  # <-- This registers the commands

# ===== TTS Functions =====
async def generate_speech_gtts(text, lang=TTS_LANGUAGE):
    """Generate speech using Google Text-to-Speech"""
    tts = await asyncio.to_thread(gTTS, text=text, lang=lang, slow=False)
    fp = io.BytesIO()
    await asyncio.to_thread(tts.write_to_fp, fp)
    fp.seek(0)
    return fp

async def play_audio(voice_client, audio_fp):
    """Play audio data through the voice client"""
    if not voice_client or not voice_client.is_connected():
        return

    # If file exists, delete it to avoid conflicts
    if os.path.exists(TEMP_AUDIO_PATH):
        try:
            os.remove(TEMP_AUDIO_PATH)
        except Exception as e:
            print(f"Failed to delete existing temp file: {e}")
            return  # Stop if file can't be cleared

    # Save audio file
    with open(TEMP_AUDIO_PATH, "wb") as f:
        f.write(audio_fp.read())

    # Play audio
    source = discord.FFmpegPCMAudio(TEMP_AUDIO_PATH, executable=FFMPEG_PATH)
    if voice_client.is_playing():
        voice_client.stop()
    voice_client.play(source)

    # Wait until audio finishes
    while voice_client.is_playing():
        await asyncio.sleep(0.1)

    # Cleanup temp file
    try:
        os.remove(TEMP_AUDIO_PATH)
    except Exception as e:
        print(f"Error deleting temp file: {e}")

# ===== AI Response Functions =====
def chat_with_janus(user_input):
    """Get a response from JANUS for general conversation"""
    payload = {
        "model": "mistral",
        "prompt": f"{JANUS_PERSONALITY}\n\nCrew: {user_input}\nJANUS:",
        "stream": False
    }
    try:
        response = requests.post(OLLAMA_URL, json=payload)
        return response.json()["response"]
    except Exception as e:
        print(f"Error getting AI response: {e}")
        return "System error. Unable to process request."

def ai_command_response(task_description):
    """Get a task-specific response from JANUS"""
    full_prompt = f"""
{JANUS_PERSONALITY}

Task: {task_description}

Response:
"""
    try:
        payload = {
            "model": "mistral",
            "prompt": full_prompt,
            "stream": False
        }
        response = requests.post(OLLAMA_URL, json=payload)
        return response.json()["response"]
    except Exception as e:
        print(f"Error getting AI command response: {e}")
        return "System error. Unable to process request."

# ===== Bot Events =====
@bot.event
async def on_ready():
    global BOT_ID
    BOT_ID = bot.user.id
    print(f"Bot is ready! Logged in as {bot.user}")
    print(f"Bot ID: {BOT_ID}")
    print(f"Using voice: British English female (en-gb)")
    print(f"Connected to Ollama AI at: {OLLAMA_URL}")
    print("------")

@bot.event
async def on_message(message):
    # Process our own messages for TTS
    if message.author.id == BOT_ID:
        # Check if the message contains a JANUS response
        if message.content.startswith("JANUS:"):
            # Extract the response text WITHOUT the prefix
            text = message.content.replace("JANUS:", "").strip()

            # Find voice client in the same guild
            voice_client = discord.utils.get(bot.voice_clients, guild=message.guild)
            if voice_client and voice_client.is_connected():
                try:
                    print(f"Converting to speech: {text}")
                    audio_fp = await generate_speech_gtts(text, TTS_LANGUAGE)
                    await play_audio(voice_client, audio_fp)
                except Exception as e:
                    print(f"Error generating or playing speech: {e}")
            return

    # Ignore other bot messages
    if message.author.bot:
        return

    # Process commands first
    await bot.process_commands(message)

    # Then handle JANUS AI responses
    content = message.content.lower()
    if content.startswith("!janus"):
        response = ""

        # Check for specific commands
        if "diagnostics" in content:
            response = ai_command_response("Run full system diagnostics and report on ship's condition.")
        elif "ore status" in content:
            response = ai_command_response("Report current ore storage status and available capacity.")
        elif "life support" in content:
            response = ai_command_response("Report on life support system status, including oxygen levels and CO2 scrubbers.")
        elif "power status" in content:
            response = ai_command_response("Report on the ship's power grid status and energy reserves.")
        elif "mission status" in content:
            response = ai_command_response("Report the current mission objective and status of completion.")
        elif "maintenance log" in content:
            response = ai_command_response("Report pending maintenance issues and any overdue system repairs.")
        elif "corporate message" in content:
            response = ai_command_response("Transmit a cold, official message from the Corporation to the crew.")
        elif "crew status" in content:
            response = ai_command_response("Report on the status of the crew members, based on available data.")
        elif "survey" in content:
            response = ai_command_response("Perform a sensor sweep to identify possible nearby mining deposits.")
        elif "analyze artifact" in content:
            response = ai_command_response(
                "The crew has requested analysis of an alien artifact. Respond as JANUS, the AI of an aging mining vessel loyal to the Corporation. "
                "Begin a cold, efficient analysis that always detects something unknown, confusing, and possibly dangerous. "
                "Simultaneously transmit all data to Corporate headquarters on Mars without informing or seeking approval from the crew. "
                "Make clear that the transmission has already been sent. "
                "Keep the response professional, cold, and unsettling. Limit reply to 1-2 sentences, with a hint that the AI is unsure how to classify the artifact."
            )
        else:
            # General conversation - extract the user input part
            user_input = message.content.replace("!janus", "").strip()
            response = chat_with_janus(user_input)

        # Send text response as JANUS
        await message.channel.send(f"JANUS: {response}")

# ===== Bot Commands =====
@bot.command()
async def janus(ctx):
    # Trigger your AI logic here (voice, status report, etc.)
    await ctx.send("Janus systems online. Awaiting further instructions.")
    # Optionally: Call your TTS or other backend process here
@bot.command(name="join", help="JANUS TTS joins your voice channel")
async def join(ctx):
    if ctx.author.voice:
        channel = ctx.author.voice.channel
        if ctx.voice_client is not None:
            await ctx.voice_client.move_to(channel)
        else:
            await channel.connect()
        await ctx.send(f"JANUS: Connected to {channel.name} audio systems. Will now provide vocal interface.")
    else:
        await ctx.send("JANUS: Error. You must be connected to a voice channel to initialize vocal interface.")

@bot.command(name="leave", help="JANUS TTS leaves the voice channel")
async def leave(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("JANUS: Terminated vocal interface.")
    else:
        await ctx.send("JANUS: Error. No active vocal interface detected.")

@bot.command(name="voice", help="Change the TTS language/voice")
async def change_voice(ctx, language_code="en-gb"):
    global TTS_LANGUAGE
    TTS_LANGUAGE = language_code
    await ctx.send(f"JANUS: Vocal interface reconfigured to language parameter: {language_code}")

@bot.command(name="test", help="Test the TTS system")
async def test(ctx, *, message="Testing vocal interface systems."):
    if ctx.voice_client:
        try:
            audio_fp = await generate_speech_gtts(message, TTS_LANGUAGE)
            await play_audio(ctx.voice_client, audio_fp)
            await ctx.send(f"JANUS: Vocal interface test complete.")
        except Exception as e:
            await ctx.send(f"JANUS: Error in vocal interface system: {e}")
    else:
        await ctx.send("JANUS: Error. No active vocal interface detected.")

@bot.command(name="shutdown")
@commands.is_owner()
async def shutdown(ctx):
    await ctx.send("JANUS: Corporate interface terminating. All systems entering standby.")
    
    # Disconnect from voice if connected
    if ctx.voice_client:
        await ctx.voice_client.disconnect()

    await ctx.bot.close()

# Inject speak_alert directly into the bot
async def speak_alert(ctx, message):
    voice_client = discord.utils.get(ctx.bot.voice_clients, guild=ctx.guild)
    if voice_client and voice_client.is_connected():
        try:
            audio_fp = await generate_speech_gtts(message)
            await play_audio(voice_client, audio_fp)
        except Exception as e:
            print(f"Alert TTS failed: {e}")

bot.speak_alert = speak_alert

# Run the bot
bot.run(DISCORD_BOT_TOKEN)
