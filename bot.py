import io
import os
import random
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
from datetime import date
from ai import generate_response, generate_image, generate_chat_response, PET_AVATARS
from db import log_mood, get_user_checkins_today, get_streak, get_unrewarded_streak, record_streak_reward

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

mood_map = {
    "😄": "good",
    "🙂": "okay",
    "😐": "meh",
    "😕": "bad",
    "😡": "awful",
}

IMAGE_CHANCE = 0.30

AVATAR_DIR = os.path.join(os.path.dirname(__file__), "avatars")


def _load_avatar(pet_name):
    """Load avatar bytes for a pet, or None."""
    avatar_file = PET_AVATARS.get(pet_name)
    if not avatar_file:
        return None
    path = os.path.join(AVATAR_DIR, os.path.basename(avatar_file))
    if os.path.exists(path):
        with open(path, "rb") as f:
            return f.read()
    return None


async def get_pet_webhook(channel, pet_name):
    """Get or create a webhook with the pet's name and avatar."""
    webhooks = await channel.webhooks()
    for wh in webhooks:
        if wh.name == pet_name:
            return wh
    avatar_bytes = _load_avatar(pet_name)
    return await channel.create_webhook(name=pet_name, avatar=avatar_bytes)


async def send_as_pet(messageable, pet_name, content=None, file=None):
    """Send a message as a pet via webhook."""
    if isinstance(messageable, discord.TextChannel):
        channel = messageable
    elif isinstance(messageable, discord.Message):
        channel = messageable.channel
    else:
        # Always fetch fresh to ensure full permissions
        channel = await bot.fetch_channel(messageable.channel_id)
    webhook = await get_pet_webhook(channel, pet_name)
    kwargs = {}
    if content:
        kwargs["content"] = content
    if file:
        kwargs["file"] = file
    await webhook.send(**kwargs)


class CustomReasonModal(discord.ui.Modal, title="What's on your mind?"):
    """Text input modal for typing a custom reason."""

    reason_input = discord.ui.TextInput(
        label="Reason",
        placeholder="Type your reason here...",
        style=discord.TextStyle.short,
        max_length=200,
    )

    def __init__(self, user_name, mood_emoji):
        super().__init__()
        self.user_name = user_name
        self.mood_emoji = mood_emoji

    async def on_submit(self, interaction: discord.Interaction):
        await handle_reason_response(interaction, self.user_name, self.mood_emoji, self.reason_input.value)


async def handle_reason_response(interaction, user_name, mood_emoji, reason):
    await interaction.response.defer(thinking=True)
    mood = mood_map[mood_emoji]
    response, theme, pet = await generate_response(mood, reason, user_name)
    log_mood(user_name, mood, reason, response, theme)

    streak = get_streak(user_name)
    msg = response
    if get_unrewarded_streak(user_name) >= 7:
        msg += f"\n🔥 **{streak}-day streak!** You've earned a reward — treat yourself to a drink or skip a chore today!"
        record_streak_reward(user_name, date.today())

    # Send text immediately as the pet
    await send_as_pet(interaction, pet, msg)
    # Dismiss the "thinking" state
    await interaction.followup.send("✅", ephemeral=True)

    # Occasional image follow-up — arrives when ready
    if random.random() < IMAGE_CHANCE:
        img_bytes = await generate_image(mood, reason, theme)
        if img_bytes:
            file = discord.File(io.BytesIO(img_bytes), filename="mood.png")
            await send_as_pet(interaction, pet, file=file)


FIXED_REASONS = ["School/Work", "Tired", "Bored"]
RANDOM_REASONS = [
    "Friends/Drama", "Family", "Anxious", "Hungry",
    "Lonely", "Excited", "Overthinking", "Heartbreak",
    "Money", "Health", "FOMO", "Nostalgia",
]


class ReasonView(discord.ui.View):
    """Buttons for selecting a reason — 3 fixed + 3 random + Skip + Custom."""

    def __init__(self, user_name, mood_emoji):
        super().__init__(timeout=60)
        self.user_name = user_name
        self.mood_emoji = mood_emoji

        # Row 0: fixed reasons
        for reason in FIXED_REASONS:
            btn = discord.ui.Button(label=reason, style=discord.ButtonStyle.primary, row=0)
            btn.callback = self._make_callback(reason)
            self.add_item(btn)

        # Row 1: 3 random reasons
        extras = random.sample(RANDOM_REASONS, 3)
        for reason in extras:
            btn = discord.ui.Button(label=reason, style=discord.ButtonStyle.primary, row=1)
            btn.callback = self._make_callback(reason)
            self.add_item(btn)

        # Row 2: Skip + Custom
        skip_btn = discord.ui.Button(label="Skip", style=discord.ButtonStyle.secondary, row=2)
        skip_btn.callback = self._make_callback("quick check-in")
        self.add_item(skip_btn)

        custom_btn = discord.ui.Button(label="✏️ Custom", style=discord.ButtonStyle.success, row=2)
        custom_btn.callback = self._custom_callback
        self.add_item(custom_btn)

    def _make_callback(self, reason):
        async def callback(interaction: discord.Interaction):
            await handle_reason_response(interaction, self.user_name, self.mood_emoji, reason)
            self.stop()
        return callback

    async def _custom_callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(CustomReasonModal(self.user_name, self.mood_emoji))


class MoodView(discord.ui.View):
    """Emoji buttons for selecting current mood."""

    def __init__(self):
        super().__init__(timeout=None)

    async def _handle_mood(self, interaction: discord.Interaction, emoji: str):
        user = interaction.user.name
        checkins = get_user_checkins_today(user)
        if checkins >= 7:
            await interaction.response.send_message(
                "You've already checked in 7 times today — come back tomorrow! 💤",
                ephemeral=True,
            )
            return
        await interaction.response.send_message(
            f"You chose {emoji} — what's the main reason?",
            view=ReasonView(user, emoji),
            ephemeral=True,
        )

    @discord.ui.button(label="😄", style=discord.ButtonStyle.success)
    async def good(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._handle_mood(interaction, "😄")

    @discord.ui.button(label="🙂", style=discord.ButtonStyle.primary)
    async def okay(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._handle_mood(interaction, "🙂")

    @discord.ui.button(label="😐", style=discord.ButtonStyle.secondary)
    async def meh(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._handle_mood(interaction, "😐")

    @discord.ui.button(label="😕", style=discord.ButtonStyle.danger)
    async def bad(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._handle_mood(interaction, "😕")

    @discord.ui.button(label="😡", style=discord.ButtonStyle.danger)
    async def awful(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._handle_mood(interaction, "😡")


@bot.command()
async def mood(ctx):
    """Manually trigger a mood check-in."""
    await ctx.send("How are you feeling right now?", view=MoodView())


@bot.event
async def on_message(message):
    if message.author.bot:
        return
    # Let commands (!mood) still work
    await bot.process_commands(message)
    # Don't reply to commands
    if message.content.startswith("!"):
        return
    async with message.channel.typing():
        reply, pet = await generate_chat_response(message.content, message.author.name)
    await send_as_pet(message, pet, reply)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    if not random_prompt.is_running():
        random_prompt.start()


@tasks.loop(hours=4)
async def random_prompt():
    """Send random mood prompts to all text channels. Quiet hours: 10pm–10am."""
    from datetime import datetime
    hour = datetime.now().hour
    if hour >= 22 or hour < 10:
        return
    for guild in bot.guilds:
        # Pick a random text channel
        text_channels = [ch for ch in guild.text_channels if ch.permissions_for(guild.me).send_messages]
        if not text_channels:
            continue
        channel = random.choice(text_channels)
        await channel.send("⏰ Random mood check! How's everyone feeling?", view=MoodView())


@random_prompt.before_loop
async def before_random_prompt():
    await bot.wait_until_ready()


bot.run(TOKEN)
