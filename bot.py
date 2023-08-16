import freeGPT
from io import BytesIO
from aiosqlite import connect
from asyncio import sleep, run
from discord.ui import Button, View
from discord.ext.commands import Bot
from discord import Intents, Embed, File, Status, Activity, ActivityType, Colour
from discord.app_commands import (
    describe,
    checks,
    BotMissingPermissions,
    MissingPermissions,
    CommandOnCooldown,
)

intents = Intents.default()
intents.message_content = True
bot = Bot(command_prefix="!", intents=intents, help_command=None)
db = None
textCompModels = ["gpt3", "gpt4", "alpaca_7b", "falcon_40b"]
imageGenModels = ["prodia", "pollinations"]


@bot.event
async def on_ready():
    print(f"\033[1;94m INFO \033[0m| {bot.user} has connected to Discord.")
    global db
    db = await connect("database.db")
    async with db.cursor() as cursor:
        await cursor.execute(
            "CREATE TABLE IF NOT EXISTS database(guilds INTEGER, channels INTEGER, models TEXT)"
        )
    print("\033[1;94m INFO \033[0m| Database connection successful.")
    sync_commands = await bot.tree.sync()
    print(f"\033[1;94m INFO \033[0m| Synced {len(sync_commands)} command(s).")
    while True:
        await bot.change_presence(
            status=Status.online,
            activity=Activity(
                type=ActivityType.watching,
                name=f"{len(bot.guilds)} servers | /help",
            ),
        )
        await sleep(300)


@bot.tree.command(name="help", description="Get help.")
async def help(interaction):
    embed = Embed(
        title="Help Menu",
        color=0x00FFFF,
    )
    embed.set_thumbnail(url=bot.user.avatar.url)
    embed.add_field(
        name="Models:",
        value=f"**Text Completion:** `{', '.join(textCompModels)}`\n**Image Generation:** `{', '.join(imageGenModels)}`",
        inline=False,
    )

    embed.add_field(
        name="Chatbot",
        value="Setup the chatbot: `/setup-chatbot`.\nReset the chatbot: `/reset-chatbot`.",
        inline=False,
    )
    view = View()
    view.add_item(
        Button(
            label="Invite Me",
            url="https://dsc.gg/freeGPT-discord",
        )
    )
    view.add_item(
        Button(
            label="Support Server",
            url="https://discord.com/invite/UxJZMUqbsb",
        )
    )
    view.add_item(
        Button(
            label="Source",
            url="https://github.com/Ruu3f/freeGPT-discord",
        )
    )
    await interaction.response.send_message(embed=embed, view=view)


@bot.tree.command(name="imagine", description="Generate a image based on a prompt.")
@describe(model=f"Model to use. Choose between {', '.join(imageGenModels)}")
@describe(prompt="Your prompt.")
async def imagine(interaction, model: str, prompt: str):
    if model.lower() not in imageGenModels:
        await interaction.response.send_message(
            f"**Error:** Model not found! Choose a model between `{', '.join(imageGenModels)}`."
        )
        return
    try:
        await interaction.response.defer()
        resp = await getattr(freeGPT, model.lower()).Generation().create(prompt=prompt)
        file = File(fp=BytesIO(resp), filename="image.png", spoiler=True)
        await interaction.followup.send(
            "**Generated image might be NSFW!** Click the spoiler at your own risk.",
            file=file,
        )

    except Exception as e:
        await interaction.followup.send(str(e))


@bot.tree.command(name="ask", description="Ask a model a question.")
@describe(model=f"Model to use. Choose between {', '.join(textCompModels)}")
@describe(prompt="Your prompt.")
async def ask(interaction, model: str, prompt: str):
    if model.lower() not in textCompModels:
        await interaction.response.send_message(
            f"**Error:** Model not found! Choose a model between `{', '.join(textCompModels)}`."
        )
        return
    try:
        await interaction.response.defer()
        resp = await getattr(freeGPT, model.lower()).Completion().create(prompt=prompt)
        if len(resp) <= 2000:
            await interaction.followup.send(resp)
        else:
            file = File(fp=BytesIO(resp.encode("utf-8")), filename="message.txt")
            await interaction.followup.send(file=file)

    except Exception as e:
        await interaction.followup.send(str(e))


@bot.tree.command(name="setup-chatbot", description="Setup the chatbot.")
@checks.has_permissions(manage_channels=True)
@checks.bot_has_permissions(manage_channels=True)
@describe(model=f"Model to use. Choose between {', '.join(textCompModels)}")
async def setup_chatbot(interaction, model: str):
    if model.lower() not in textCompModels:
        await interaction.response.send_message(
            f"**Error:** Model not found! Choose a model between `{', '.join(textCompModels)}`."
        )
        return

    cursor = await db.execute(
        "SELECT channels, models FROM database WHERE guilds = ?",
        (interaction.guild.id,),
    )
    data = await cursor.fetchone()
    if data:
        await interaction.response.send_message(
            "**Error:** The chatbot is already set up. Use the `/reset-chatbot` command to fix this error."
        )
        return

    if model.lower() in textCompModels:
        channel = await interaction.guild.create_text_channel(
            "freegpt-chat", slowmode_delay=15
        )

        await db.execute(
            "INSERT OR REPLACE INTO database (guilds, channels, models) VALUES (?, ?, ?)",
            (
                interaction.guild.id,
                channel.id,
                model,
            ),
        )
        await db.commit()
        await interaction.response.send_message(
            f"**Success:** The chatbot has been set up. The channel is {channel.mention}."
        )
    else:
        await interaction.response.send_message(
            f"**Error:** Model not found! Choose a model between `{', '.join(textCompModels)}`."
        )


@bot.tree.command(name="reset-chatbot", description="Reset the chatbot.")
@checks.has_permissions(manage_channels=True)
@checks.bot_has_permissions(manage_channels=True)
async def reset_chatbot(interaction):
    cursor = await db.execute(
        "SELECT channels, models FROM database WHERE guilds = ?",
        (interaction.guild.id,),
    )
    data = await cursor.fetchone()
    if data:
        channel = await bot.fetch_channel(data[0])
        await channel.delete()
        await db.execute(
            "DELETE FROM database WHERE guilds = ?", (interaction.guild.id,)
        )
        await db.commit()
        await interaction.response.send_message(
            "**Success:** The chatbot has been reset."
        )

    else:
        await interaction.response.send_message(
            "**Error:** The chatbot is not set up. Use the `/setup-chatbot` command to fix this error."
        )


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if db:
        cursor = await db.execute(
            "SELECT channels, models FROM database WHERE guilds = ?",
            (message.guild.id,),
        )
        data = await cursor.fetchone()
        if data:
            channel_id, model = data
            if message.channel.id == channel_id:
                await message.channel.edit(slowmode_delay=15)
                async with message.channel.typing():
                    try:
                        resp = (
                            await getattr(freeGPT, model.lower())
                            .Completion()
                            .create(prompt=message.content)
                        )
                        if (
                            "@everyone" in resp
                            or "@here" in resp
                            or "<@" in resp
                            and ">" in resp
                        ):
                            resp = (
                                resp.replace("@everyone", "@ everyone")
                                .replace("@here", "@ here")
                                .replace("<@", "<@ ")
                            )
                        if len(resp) <= 2000:
                            await message.reply(resp)
                        else:
                            resp_file = File(
                                fp=BytesIO(resp.encode("utf-8")), filename="message.txt"
                            )
                            await message.reply(file=resp_file)

                    except Exception as e:
                        await message.reply(str(e))


@bot.tree.error
async def on_app_command_error(interaction, error):
    if isinstance(error, CommandOnCooldown):
        embed = Embed(
            description=f"This command is on cooldown, try again in {error.retry_after:.2f} seconds.",
            colour=Colour.gray(),
        )
        await interaction.response.send_message(embed=embed)
    elif isinstance(error, MissingPermissions):
        embed = Embed(
            description=f"**Error:** You are missing the `{error.missing_permissions[0]}` permission to run this command.",
            colour=Colour.red(),
        )
    elif isinstance(error, BotMissingPermissions):
        embed = Embed(
            description=f"**Error:** I am missing the `{error.missing_permissions[0]}` permission to run this command.",
            colour=Colour.red(),
        )
        await interaction.response.send_message(embed=embed)
    else:
        embed = Embed(
            title="An error occurred:",
            description=error,
            color=Colour.red(),
        )
        view = View()
        view.add_item(
            Button(
                label="Report this error",
                url="https://discord.com/invite/UxJZMUqbsb",
            )
        )
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


@bot.event
async def on_guild_remove(guild):
    await db.execute("DELETE FROM database WHERE guilds = ?", (guild.id,))
    await db.commit()


if __name__ == "__main__":
    TOKEN = ""
    run(bot.run(TOKEN))
