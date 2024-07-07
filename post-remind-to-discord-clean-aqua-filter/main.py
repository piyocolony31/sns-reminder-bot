import sys
import discord
from discord.ext import commands
from discord import Intents

def main(token, content, button_label, button_response):
    intents = Intents.default()
    intents.message_content = True
    bot = commands.Bot(command_prefix="!", intents=intents)

    @bot.event
    async def on_ready():
        print(f'Logged in as {bot.user}')
        await send_button()
        await bot.close()

    async def send_button():
        channel = bot.get_channel(bot.guilds[0].text_channels[0].id)
        button = discord.ui.Button(label=button_label, style=discord.ButtonStyle.primary, custom_id="button_click")
        
        async def button_callback(interaction):
            await interaction.response.send_message(button_response, ephemeral=True)
        
        button.callback = button_callback
        view = discord.ui.View()
        view.add_item(button)
        await channel.send(content, view=view)

    bot.run(token)

if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Usage: python post-remind-to-discord-clean-aqua-filter/main.py <token> <content> <button_label> <button_response>")
        sys.exit(1)
    
    token = sys.argv[1]
    content = sys.argv[2]
    button_label = sys.argv[3]
    button_response = sys.argv[4]
    
    main(token, content, button_label, button_response)