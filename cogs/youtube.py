import discord
from discord.ext import commands, tasks
import motor.motor_asyncio
import aiohttp
import os
import feedparser
import re

class YouTube(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.mongo_client = motor.motor_asyncio.AsyncIOMotorClient(os.getenv("MONGO_URL"))
        self.db = self.mongo_client["natanbot"]
        self.collection = self.db["canais_youtube"]
        self.api_key = os.getenv("YT_API_KEY")
        self.verificar_novos_videos.start()

    def cog_unload(self):
        self.verificar_novos_videos.cancel()

    def extrair_channel_id(self, url):
        if "channel/" in url:
            return url.split("channel/")[1].split("/")[0]
        return None

    async def obter_channel_id_por_username(self, url):
        match = re.search(r"@([\w\-]+)", url)
        if not match:
            return None
        username = match.group(1)
        base_url = "https://www.googleapis.com/youtube/v3/channels"
        params = {
            "part": "id",
            "forUsername": username,
            "key": self.api_key
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(base_url, params=params) as resp:
                data = await resp.json()
                if "items" in data and data["items"]:
                    return data["items"][0]["id"]
                else:
                    return None

    @commands.command(name="canalyt")
    @commands.has_permissions(administrator=True)
    async def canalyt(self, ctx, url: str, canal: discord.TextChannel):
        await ctx.defer()
        canal_id = self.extrair_channel_id(url)

        if not canal_id:
            canal_id = await self.obter_channel_id_por_username(url)
            if not canal_id:
                return await ctx.send("❌ Não foi possível extrair o ID do canal. Use uma URL válida.")

        await self.collection.update_one(
            {"channel_id": canal_id},
            {"$set": {
                "channel_id": canal_id,
                "url": url,
                "discord_channel_id": canal.id,
                "ultimo_video": None,
                "mensagem": "📢 Novo vídeo postado!"
            }},
            upsert=True
        )
        await ctx.send(f"✅ Canal `{url}` adicionado com sucesso para {canal.mention}.")

    @commands.command(name="removeryt")
    @commands.has_permissions(administrator=True)
    async def removeryt(self, ctx, url: str):
        canal_id = self.extrair_channel_id(url)
        if not canal_id:
            canal_id = await self.obter_channel_id_por_username(url)
            if not canal_id:
                return await ctx.send("❌ URL inválida.")

        result = await self.collection.delete_one({"channel_id": canal_id})
        if result.deleted_count:
            await ctx.send(f"✅ Canal `{url}` removido com sucesso.")
        else:
            await ctx.send("❌ Canal não encontrado.")

    @commands.command(name="msgyt")
    @commands.has_permissions(administrator=True)
    async def msgyt(self, ctx, url: str, *, nova_mensagem: str):
        canal_id = self.extrair_channel_id(url)
        if not canal_id:
            canal_id = await self.obter_channel_id_por_username(url)
            if not canal_id:
                return await ctx.send("❌ URL inválida.")

        result = await self.collection.update_one(
            {"channel_id": canal_id},
            {"$set": {"mensagem": nova_mensagem}}
        )
        if result.matched_count:
            await ctx.send("✅ Mensagem personalizada atualizada com sucesso.")
        else:
            await ctx.send("❌ Canal não encontrado no banco.")

    @commands.command(name="listaryt")
    async def listaryt(self, ctx):
        canais = []
        async for doc in self.collection.find({}):
            canais.append(f"🔗 `{doc['url']}` → <#{doc['discord_channel_id']}>")

        if not canais:
            return await ctx.send("📭 Nenhum canal de YouTube cadastrado ainda.")

        embed = discord.Embed(
            title="📺 Canais do YouTube Monitorados",
            description="\n".join(canais),
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)

    @commands.command(name="testaryt")
    @commands.has_permissions(administrator=True)
    async def testaryt(self, ctx, url: str):
        canal_id = self.extrair_channel_id(url)
        if not canal_id:
            canal_id = await self.obter_channel_id_por_username(url)
            if not canal_id:
                return await ctx.send("❌ URL inválida.")

        doc = await self.collection.find_one({"channel_id": canal_id})
        if not doc:
            return await ctx.send("❌ Canal não cadastrado.")

        feed_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={canal_id}"
        feed = feedparser.parse(feed_url)
        if not feed.entries:
            return await ctx.send("❌ Nenhum vídeo encontrado no feed.")

        video = feed.entries[0]
        video_url = video.link
        titulo = video.title
        canal = self.bot.get_channel(doc["discord_channel_id"])
        mensagem = doc.get("mensagem", "📢 Novo vídeo postado!")

        embed = discord.Embed(
            title=titulo,
            description=mensagem,
            url=video_url,
            color=discord.Color.red()
        )
        embed.set_author(name="Novo vídeo no YouTube 🎬")
        embed.set_thumbnail(url="https://www.iconpacks.net/icons/2/free-youtube-logo-icon-2431-thumb.png")
        embed.set_footer(text="NatanBot • Notificação de vídeo")

        if canal:
            await canal.send(embed=embed)
            await ctx.send("✅ Teste enviado com sucesso!")
        else:
            await ctx.send("❌ Canal do Discord não encontrado.")

    @tasks.loop(minutes=5)
    async def verificar_novos_videos(self):
        await self.bot.wait_until_ready()
        async for doc in self.collection.find({}):
            canal_id = doc["channel_id"]
            discord_channel_id = doc["discord_channel_id"]
            ultimo_video = doc.get("ultimo_video")
            mensagem = doc.get("mensagem", "📢 Novo vídeo postado!")

            feed_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={canal_id}"
            try:
                feed = feedparser.parse(feed_url)
                if not feed.entries:
                    continue

                video = feed.entries[0]
                video_id = video.yt_videoid
                video_url = video.link
                titulo = video.title

                if video_id != ultimo_video:
                    canal = self.bot.get_channel(discord_channel_id)
                    if canal:
                        embed = discord.Embed(
                            title=titulo,
                            description=mensagem,
                            url=video_url,
                            color=discord.Color.red()
                        )
                        embed.set_author(name="Novo vídeo no YouTube 🎬")
                        embed.set_thumbnail(url="https://www.iconpacks.net/icons/2/free-youtube-logo-icon-2431-thumb.png")
                        embed.set_footer(text="NatanBot • Notificação de vídeo")

                        await canal.send(embed=embed)

                    await self.collection.update_one(
                        {"channel_id": canal_id},
                        {"$set": {"ultimo_video": video_id}}
                    )
            except Exception as e:
                print(f"[Erro ao verificar canal {canal_id}] {e}")

    @verificar_novos_videos.before_loop
    async def before_loop(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(YouTube(bot))
