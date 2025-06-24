import discord
from discord.ext import commands, tasks
import random

class StatusSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.status_list = [
            {"type": "playing", "text": "!ajuda | Criador: Natan"},
            {"type": "listening", "text": "NatsonGames"},
            {"type": "playing", "text": "!saldo | Sistema de Economia"},
            {"type": "watching", "text": "você ganhar dinheiro"},
            {"type": "playing", "text": "!trabalhar | Faça seu dinheiro"},
            {"type": "listening", "text": "comandos de economia"},
            {"type": "playing", "text": "!crime | Vida de bandido"},
            {"type": "watching", "text": "o servidor crescer"},
            {"type": "playing", "text": "!loteria | Tente a sorte"},
            {"type": "streaming", "text": "NatsonGames no Twitch"},
            {"type": "playing", "text": "!loja | Compre itens legais"},
            {"type": "watching", "text": "transações bancárias"},
            {"type": "playing", "text": "!apostar | Jogue com moderação"},
            {"type": "listening", "text": "música do Natan"},
            {"type": "playing", "text": "Economia BR | Reais brasileiros"},
            {"type": "playing", "text": "!diario | Recompensa diária"},
            {"type": "watching", "text": "você se divertir"},
            {"type": "listening", "text": "suas conquistas"},
            {"type": "playing", "text": "!investir | Multiplique seu dinheiro"},
            {"type": "watching", "text": "o mercado financeiro"}
        ]
        self.interval = 10
        self.active = True
        
    @commands.Cog.listener()
    async def on_ready(self):
        if not self.change_status.is_running():
            self.change_status.start()
    
    @tasks.loop(minutes=10)
    async def change_status(self):
        if self.active:
            try:
                s = random.choice(self.status_list)
                await self._set_status(s)
            except Exception as e:
                print(f"Erro status: {e}")
    
    async def _set_status(self, s):
        if s["type"] == "playing":
            a = discord.Game(name=s["text"])
        elif s["type"] == "listening":
            a = discord.Activity(type=discord.ActivityType.listening, name=s["text"])
        elif s["type"] == "watching":
            a = discord.Activity(type=discord.ActivityType.watching, name=s["text"])
        elif s["type"] == "streaming":
            a = discord.Streaming(name=s["text"], url="https://twitch.tv/natsongames")
        else:
            a = discord.Game(name=s["text"])
        
        await self.bot.change_presence(status=discord.Status.online, activity=a)
    
    @commands.command(name='statusmodo')
    @commands.has_permissions(administrator=True)
    async def toggle_status(self, ctx):
        self.active = not self.active
        e = discord.Embed(
            title="⚙️ Status Sistema",
            description=f"Status {'ativado' if self.active else 'desativado'}",
            color=0x00ff00 if self.active else 0xff0000
        )
        await ctx.send(embed=e)
    
    @commands.command(name='statusintervalo')
    @commands.has_permissions(administrator=True)
    async def set_interval(self, ctx, min: int):
        if min < 1 or min > 1440:
            e = discord.Embed(title="❌ Erro", description="Entre 1-1440 min", color=0xff0000)
            await ctx.send(embed=e)
            return
        
        self.interval = min
        self.change_status.cancel()
        self.change_status.change_interval(minutes=min)
        self.change_status.start()
        
        e = discord.Embed(
            title="⚙️ Intervalo Alterado",
            description=f"Novo: {min} min",
            color=0x00ff00
        )
        await ctx.send(embed=e)
    
    @commands.command(name='statusmanual')
    @commands.has_permissions(administrator=True)
    async def manual_change(self, ctx):
        try:
            s = random.choice(self.status_list)
            await self._set_status(s)
            
            emojis = {"playing": "🎮", "listening": "🎵", "watching": "👀", "streaming": "📺"}
            
            e = discord.Embed(
                title="🔄 Status Alterado",
                description=f"{emojis.get(s['type'], '🎮')} {s['text']}",
                color=0x00ff00
            )
            await ctx.send(embed=e)
            
        except Exception as ex:
            e = discord.Embed(title="❌ Erro", description=str(ex), color=0xff0000)
            await ctx.send(embed=e)
    
    @commands.command(name='listarstatus')
    async def list_status(self, ctx):
        e = discord.Embed(
            title="📊 Status Disponíveis",
            description=f"Total: {len(self.status_list)} status",
            color=0x0099ff
        )
        
        # Divide em grupos de 8 para economizar espaço
        for i in range(0, len(self.status_list), 8):
            group = self.status_list[i:i+8]
            text = ""
            for s in group:
                emoji = {"playing": "🎮", "listening": "🎵", "watching": "👀", "streaming": "📺"}.get(s["type"], "🎮")
                text += f"{emoji} {s['text']}\n"
            
            e.add_field(
                name=f"Status {i+1}-{min(i+8, len(self.status_list))}",
                value=text,
                inline=False
            )
        
        e.add_field(
            name="⚙️ Config",
            value=f"Intervalo: {self.interval}min\nStatus: {'Ativo' if self.active else 'Inativo'}",
            inline=False
        )
        
        e.set_footer(text="!statusmodo | !statusintervalo <min> | !statusmanual")
        await ctx.send(embed=e)

async def setup(bot):
    await bot.add_cog(StatusSystem(bot))