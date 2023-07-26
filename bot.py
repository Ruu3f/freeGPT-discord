import freeGPT
from io import BytesIO
from aiosqlite import connect
from asyncio import sleep, run
from discord.ui import Button, View
from discord.ext.commands import Bot
from discord.app_commands import describe, checks, errors
from discord import Intents, Embed, File, Status, Activity, ActivityType

intents = Intents.default()
intents.message_content = True
bot = Bot(command_prefix="!", intents=intents, help_command=None)
db = None
textCompModels = ["gpt3", "gpt4", "alpaca_7b"]
imageGenModels = ["prodia", "pollinations"]


@bot.event
async def on_ready():
    print(f"\033[1;94m INFO \033[0m| {bot.user.name} has connected to Discord.")
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
        description=f"Available models: `{', '.join(textCompModels)}`",
        color=0x00FFFF,
    )
    embed.add_field(
        name="setup",
        value="Usage: `/setup {model}`",
    )
    embed.add_field(name="reset", value="Usage: `/reset`")
    embed.set_footer(text="Powered by github.com/Ruu3f/freeGPT")
    view = View()
    view.add_item(
        Button(
            label="Invite",
            url="https://dsc.gg/freeGPT",
        )
    )
    view.add_item(
        Button(
            label="Server",
            url="https://discord.gg/XH6pUGkwRr",
        )
    )
    view.add_item(
        Button(
            label="Source",
            url="https://github.com/Ruu3f/freeGPT-discord-bot",
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
        resp = await getattr(freeGPT, model.lower()).Generation.create(prompt=prompt)
        file = File(fp=BytesIO(resp), filename="image.png")
        await interaction.followup.send(file=file)

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
        resp = await getattr(freeGPT, model.lower()).Completion.create(prompt=prompt)
        if len(resp) <= 2000:
            await interaction.followup.send(resp)
        else:
            file = File(fp=BytesIO(resp.encode("utf-8")), filename="message.txt")
            await interaction.followup.send(file=file)

    except Exception as e:
        await interaction.followup.send(str(e))


@bot.tree.command(name="setup", description="Setup the chatbot.")
@checks.has_permissions(manage_channels=True)
@checks.bot_has_permissions(manage_channels=True)
@describe(model=f"Model to use. Choose between {', '.join(textCompModels)}")
async def setup(interaction, model: str):
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
            "**Error:** The chatbot is already set up. Use the `/reset` command to fix this error."
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


@setup.error
async def setup_err(interaction, error):
    if isinstance(error, errors.BotMissingPermissions):
        await interaction.response.send_message(
            "**Error:** I don't have the required permission to use this command."
        )
    elif isinstance(error, errors.MissingPermissions):
        await interaction.response.send_message(
            "**Error:** You don't have the required permission to use this command."
        )


@bot.tree.command(name="reset", description="Reset the chatbot.")
@checks.has_permissions(manage_channels=True)
@checks.bot_has_permissions(manage_channels=True)
async def reset(interaction):
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
            "**Error:** The chatbot is not set up. Use the `/setup` command to fix this error."
        )


@reset.error
async def reset_err(interaction, error):
    if isinstance(error, errors.BotMissingPermissions):
        await interaction.response.send_message(
            "**Error:** I don't have the required permission to use this command."
        )
    elif isinstance(error, errors.MissingPermissions):
        await interaction.response.send_message(
            "**Error:** You don't have the required permission to use this command."
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
                        resp = await getattr(freeGPT, model.lower()).Completion.create(
                            prompt=message.content
                        )
                        if len(resp) <= 2000:
                            await message.reply(resp)
                        else:
                            resp = File(
                                fp=BytesIO(resp.encode("utf-8")), filename="message.txt"
                            )
                            await message.reply(file=resp)

                    except Exception as e:
                        await message.reply(str(e))


@bot.event
async def on_guild_remove(guild):
    await db.execute("DELETE FROM database WHERE guilds = ?", (guild.id,))
    await db.commit()


if __name__ == "__main__":
    TOKEN = ""
    run(bot.run(TOKEN))
