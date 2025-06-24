import discord
from discord.ext import commands, tasks
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import aiohttp
import feedparser
from datetime import datetime, timedelta
import re

class YouTubeSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.client = None
        self.db = None
        self.collection = None
        self._connection_ready = False
        # Inicializa a conexão com MongoDB
        self.bot.loop.create_task(self.init_database())
        # Inicia o loop de verificação de novos vídeos
        self.check_new_videos.start()

    async def init_database(self):
        """Inicializa a conexão com MongoDB"""
        try:
            # URL de conexão do MongoDB (vem de variável de ambiente)
            mongo_uri = os.getenv("MONGO_URI")
            
            if not mongo_uri:
                print("❌ MONGO_URI não encontrada nas variáveis de ambiente!")
                return
            
            print("🔄 Conectando ao MongoDB (YouTube System)...")
            self.client = AsyncIOMotorClient(mongo_uri)
            
            # Testa a conexão
            await self.client.admin.command('ping')
            
            self.db = self.client['discord_bot']
            self.collection = self.db['youtube_config']
            self._connection_ready = True
            
            print("✅ Conectado ao MongoDB com sucesso! (YouTube System)")
            
        except Exception as e:
            print(f"❌ Erro ao conectar com MongoDB (YouTube): {e}")
            self._connection_ready = False

    async def ensure_connection(self):
        """Garante que a conexão com MongoDB está ativa"""
        if not self._connection_ready:
            await self.init_database()
        return self._connection_ready

    async def get_guild_config(self, guild_id):
        """Obtém a configuração de um servidor específico do MongoDB"""
        try:
            if not await self.ensure_connection():
                print("❌ Conexão com MongoDB não está disponível")
                return {}
                
            config = await self.collection.find_one({"guild_id": str(guild_id)})
            return config.get('config', {}) if config else {}
            
        except Exception as e:
            print(f"❌ Erro ao buscar configuração YouTube: {e}")
            return {}

    async def set_guild_config(self, guild_id, key, value):
        """Define uma configuração para um servidor específico no MongoDB"""
        try:
            if not await self.ensure_connection():
                print("❌ Conexão com MongoDB não está disponível")
                return False
            
            guild_id = str(guild_id)
            
            # Usa upsert para criar ou atualizar
            await self.collection.update_one(
                {"guild_id": guild_id},
                {"$set": {f"config.{key}": value}},
                upsert=True
            )
            
            print(f"✅ Configuração YouTube salva: {key} = {value} para guild {guild_id}")
            return True
                
        except Exception as e:
            print(f"❌ Erro ao salvar configuração YouTube: {e}")
            return False

    async def add_youtube_channel(self, guild_id, channel_url, discord_channel_id):
        """Adiciona um canal do YouTube à lista de monitoramento"""
        try:
            if not await self.ensure_connection():
                return False
            
            guild_id = str(guild_id)
            channel_id = self.extract_channel_id(channel_url)
            
            if not channel_id:
                return False
            
            # Busca configuração atual
            config = await self.get_guild_config(guild_id)
            youtube_channels = config.get('youtube_channels', [])
            
            # Verifica se o canal já existe
            for channel in youtube_channels:
                if channel['channel_id'] == channel_id:
                    return False  # Canal já existe
            
            # Adiciona novo canal
            new_channel = {
                'channel_id': channel_id,
                'channel_url': channel_url,
                'discord_channel_id': discord_channel_id,
                'last_video_id': None,
                'added_date': datetime.utcnow().isoformat()
            }
            
            youtube_channels.append(new_channel)
            
            await self.set_guild_config(guild_id, 'youtube_channels', youtube_channels)
            return True
            
        except Exception as e:
            print(f"❌ Erro ao adicionar canal YouTube: {e}")
            return False

    async def remove_youtube_channel(self, guild_id, channel_url):
        """Remove um canal do YouTube da lista de monitoramento"""
        try:
            if not await self.ensure_connection():
                return False
            
            guild_id = str(guild_id)
            channel_id = self.extract_channel_id(channel_url)
            
            if not channel_id:
                return False
            
            # Busca configuração atual
            config = await self.get_guild_config(guild_id)
            youtube_channels = config.get('youtube_channels', [])
            
            # Remove o canal
            youtube_channels = [ch for ch in youtube_channels if ch['channel_id'] != channel_id]
            
            await self.set_guild_config(guild_id, 'youtube_channels', youtube_channels)
            return True
            
        except Exception as e:
            print(f"❌ Erro ao remover canal YouTube: {e}")
            return False

    def extract_channel_id(self, url):
        """Extrai o ID do canal do YouTube da URL"""
        patterns = [
            r'youtube\.com/channel/([a-zA-Z0-9_-]+)',
            r'youtube\.com/c/([a-zA-Z0-9_-]+)',
            r'youtube\.com/user/([a-zA-Z0-9_-]+)',
            r'youtube\.com/@([a-zA-Z0-9_.-]+)',
            r'youtu\.be/channel/([a-zA-Z0-9_-]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None

    async def resolve_channel_id(self, channel_identifier):
        """Resolve handle/username para channel ID real"""
        try:
            # Se já é um channel ID (começa com UC), retorna
            if channel_identifier.startswith('UC'):
                return channel_identifier
                
            # Tenta diferentes URLs de RSS feed
            urls_to_try = [
                f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_identifier}",
                f"https://www.youtube.com/feeds/videos.xml?user={channel_identifier}"
            ]
            
            async with aiohttp.ClientSession() as session:
                for url in urls_to_try:
                    try:
                        async with session.get(url, timeout=10) as response:
                            if response.status == 200:
                                content = await response.text()
                                feed = feedparser.parse(content)
                                if feed.entries:
                                    return channel_identifier
                    except:
                        continue
                        
            return None
            
        except Exception as e:
            print(f"❌ Erro ao resolver channel ID: {e}")
            return None

    async def get_channel_rss_feed(self, channel_id):
        """Obtém o feed RSS do canal do YouTube"""
        try:
            # Tenta diferentes formatos de URL
            urls_to_try = []
            
            if channel_id.startswith('UC'):
                urls_to_try.append(f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}")
            else:
                urls_to_try.extend([
                    f"https://www.youtube.com/feeds/videos.xml?user={channel_id}",
                    f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
                ])
            
            async with aiohttp.ClientSession() as session:
                for rss_url in urls_to_try:
                    try:
                        async with session.get(rss_url, timeout=15) as response:
                            if response.status == 200:
                                content = await response.text()
                                feed = feedparser.parse(content)
                                if feed.entries:
                                    return feed
                    except asyncio.TimeoutError:
                        print(f"⏰ Timeout ao buscar feed: {rss_url}")
                        continue
                    except Exception as e:
                        print(f"❌ Erro ao buscar feed {rss_url}: {e}")
                        continue
                        
            return None
            
        except Exception as e:
            print(f"❌ Erro geral ao buscar feed RSS: {e}")
            return None

    async def check_config_channel(self, ctx):
        """Verifica se o comando está sendo usado no canal correto"""
        # Busca configuração de welcome para usar o mesmo canal de config
        welcome_config = await self.get_welcome_config(ctx.guild.id)
        canal_config = welcome_config.get('canal_config')
        
        if not canal_config:
            embed = discord.Embed(
                title="❌ Canal de Configuração Não Definido",
                description="Primeiro defina um canal de configuração com `!canalconfig #canal`",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return False
            
        if ctx.channel.id != canal_config:
            canal = self.bot.get_channel(canal_config)
            canal_mention = canal.mention if canal else f"<#{canal_config}>"
            embed = discord.Embed(
                title="❌ Canal Incorreto",
                description=f"Use este comando apenas no canal configurado: {canal_mention}",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return False
            
        return True

    async def get_welcome_config(self, guild_id):
        """Obtém configuração do sistema de welcome para usar o mesmo canal de config"""
        try:
            if not await self.ensure_connection():
                return {}
            
            welcome_collection = self.db['welcome_config']
            config = await welcome_collection.find_one({"guild_id": str(guild_id)})
            return config.get('config', {}) if config else {}
            
        except Exception as e:
            print(f"❌ Erro ao buscar configuração welcome: {e}")
            return {}

    @commands.command(name='adicionaryt')
    @commands.has_permissions(administrator=True)
    async def adicionar_youtube(self, ctx, channel_url: str, canal_discord: discord.TextChannel):
        """Adiciona um canal do YouTube para monitoramento
        
        Uso: !adicionaryt <URL_do_canal> #canal-discord
        """
        if not await self.check_config_channel(ctx):
            return

        # Valida URL do YouTube
        if 'youtube.com' not in channel_url and 'youtu.be' not in channel_url:
            embed = discord.Embed(
                title="❌ URL Inválida",
                description="Por favor, forneça uma URL válida do YouTube.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        # Envia mensagem de carregamento
        loading_embed = discord.Embed(
            title="⏳ Processando...",
            description="Verificando canal do YouTube...",
            color=discord.Color.orange()
        )
        loading_msg = await ctx.send(embed=loading_embed)

        success = await self.add_youtube_channel(ctx.guild.id, channel_url, canal_discord.id)
        
        if success:
            embed = discord.Embed(
                title="✅ Canal YouTube Adicionado",
                description=f"**Canal:** {channel_url}\n**Notificações em:** {canal_discord.mention}",
                color=discord.Color.green()
            )
        else:
            embed = discord.Embed(
                title="❌ Erro",
                description="Não foi possível adicionar o canal. Verifique se a URL está correta ou se o canal já foi adicionado.",
                color=discord.Color.red()
            )
        
        await loading_msg.edit(embed=embed)

    @commands.command(name='removeryt')
    @commands.has_permissions(administrator=True)
    async def remover_youtube(self, ctx, channel_url: str):
        """Remove um canal do YouTube do monitoramento
        
        Uso: !removeryt <URL_do_canal>
        """
        if not await self.check_config_channel(ctx):
            return

        success = await self.remove_youtube_channel(ctx.guild.id, channel_url)
        
        if success:
            embed = discord.Embed(
                title="✅ Canal YouTube Removido",
                description=f"Canal removido: {channel_url}",
                color=discord.Color.green()
            )
        else:
            embed = discord.Embed(
                title="❌ Erro",
                description="Não foi possível remover o canal. Verifique se a URL está correta.",
                color=discord.Color.red()
            )
        
        await ctx.send(embed=embed)

    @commands.command(name='mensagemyt')
    @commands.has_permissions(administrator=True)
    async def mensagem_youtube(self, ctx, *, mensagem):
        """Define a mensagem para notificações de novos vídeos
        
        Variáveis disponíveis:
        {title} - Título do vídeo
        {channel} - Nome do canal
        {url} - URL do vídeo
        """
        if not await self.check_config_channel(ctx):
            return

        success = await self.set_guild_config(ctx.guild.id, 'youtube_message', mensagem)
        
        if success:
            embed = discord.Embed(
                title="✅ Mensagem YouTube Definida",
                description=f"**Mensagem:** {mensagem}\n\n**Variáveis disponíveis:**\n`{title}` - Título do vídeo\n`{channel}` - Nome do canal\n`{url}` - URL do vídeo",
                color=discord.Color.green()
            )
        else:
            embed = discord.Embed(
                title="❌ Erro",
                description="Não foi possível salvar a configuração.",
                color=discord.Color.red()
            )
            
        await ctx.send(embed=embed)

    @commands.command(name='listaryt')
    @commands.has_permissions(administrator=True)
    async def listar_youtube(self, ctx):
        """Lista todos os canais do YouTube configurados"""
        if not await self.check_config_channel(ctx):
            return

        config = await self.get_guild_config(ctx.guild.id)
        youtube_channels = config.get('youtube_channels', [])
        youtube_message = config.get('youtube_message', 'Não configurada')

        embed = discord.Embed(
            title="📺 Configuração YouTube",
            color=discord.Color.blue()
        )

        if youtube_channels:
            channels_text = []
            for i, channel in enumerate(youtube_channels, 1):
                discord_channel = self.bot.get_channel(channel['discord_channel_id'])
                channel_mention = discord_channel.mention if discord_channel else "Canal não encontrado"
                channels_text.append(f"**{i}.** {channel['channel_url']}\n📍 {channel_mention}")
            
            embed.add_field(
                name="📺 Canais Monitorados",
                value="\n\n".join(channels_text),
                inline=False
            )
        else:
            embed.add_field(
                name="📺 Canais Monitorados",
                value="❌ Nenhum canal configurado",
                inline=False
            )

        embed.add_field(
            name="💬 Mensagem de Notificação",
            value=youtube_message if youtube_message != 'Não configurada' else "❌ Não configurada",
            inline=False
        )

        embed.set_footer(text="Use !adicionaryt, !removeryt e !mensagemyt para configurar")
        await ctx.send(embed=embed)

    def format_youtube_message(self, message, title, channel_name, video_url):
        """Formata a mensagem substituindo as variáveis"""
        formatted = message.replace('{title}', title)
        formatted = formatted.replace('{channel}', channel_name)
        formatted = formatted.replace('{url}', video_url)
        return formatted

    @tasks.loop(minutes=10)  # Aumentado para 10 minutos para evitar rate limits
    async def check_new_videos(self):
        """Verifica novos vídeos nos canais monitorados"""
        if not self._connection_ready:
            return

        try:
            # Busca todas as configurações de guilds
            async for guild_doc in self.collection.find({}):
                guild_id = guild_doc['guild_id']
                config = guild_doc.get('config', {})
                youtube_channels = config.get('youtube_channels', [])
                youtube_message = config.get('youtube_message')

                if not youtube_channels or not youtube_message:
                    continue

                for channel_config in youtube_channels:
                    await self.check_channel_for_new_videos(guild_id, channel_config, youtube_message)
                    # Pequena pausa entre verificações para evitar rate limits
                    await asyncio.sleep(2)

        except Exception as e:
            print(f"❌ Erro na verificação de vídeos: {e}")

    async def check_channel_for_new_videos(self, guild_id, channel_config, youtube_message):
        """Verifica novos vídeos em um canal específico"""
        try:
            channel_id = channel_config['channel_id']
            discord_channel_id = channel_config['discord_channel_id']
            last_video_id = channel_config.get('last_video_id')

            # Busca feed RSS
            feed = await self.get_channel_rss_feed(channel_id)
            if not feed or not feed.entries:
                print(f"⚠️ Nenhum vídeo encontrado para canal {channel_id}")
                return

            # Pega o vídeo mais recente
            latest_video = feed.entries[0]
            
            # Extrai ID do vídeo de diferentes formatos possíveis
            video_id = None
            if hasattr(latest_video, 'id'):
                if ':' in latest_video.id:
                    video_id = latest_video.id.split(':')[-1]
                else:
                    video_id = latest_video.id
            elif hasattr(latest_video, 'link'):
                # Extrai ID da URL do vídeo
                video_match = re.search(r'watch\?v=([a-zA-Z0-9_-]+)', latest_video.link)
                if video_match:
                    video_id = video_match.group(1)

            if not video_id:
                print(f"⚠️ Não foi possível extrair ID do vídeo para canal {channel_id}")
                return

            # Se é um novo vídeo
            if video_id != last_video_id:
                # Atualiza o último vídeo ID
                await self.update_last_video_id(guild_id, channel_id, video_id)

                # Envia notificação (apenas se não for o primeiro check)
                if last_video_id is not None:
                    await self.send_video_notification(
                        discord_channel_id,
                        latest_video.title,
                        feed.feed.title,
                        latest_video.link,
                        youtube_message
                    )
                    print(f"📺 Novo vídeo detectado para canal {channel_id}: {latest_video.title}")

        except Exception as e:
            print(f"❌ Erro ao verificar canal {channel_config.get('channel_id', 'unknown')}: {e}")

    async def update_last_video_id(self, guild_id, channel_id, video_id):
        """Atualiza o ID do último vídeo verificado"""
        try:
            await self.collection.update_one(
                {
                    "guild_id": str(guild_id),
                    "config.youtube_channels.channel_id": channel_id
                },
                {
                    "$set": {
                        "config.youtube_channels.$.last_video_id": video_id
                    }
                }
            )
        except Exception as e:
            print(f"❌ Erro ao atualizar último vídeo ID: {e}")

    async def send_video_notification(self, discord_channel_id, title, channel_name, video_url, message_template):
        """Envia notificação de novo vídeo"""
        try:
            channel = self.bot.get_channel(discord_channel_id)
            if not channel:
                print(f"❌ Canal Discord {discord_channel_id} não encontrado")
                return

            formatted_message = self.format_youtube_message(message_template, title, channel_name, video_url)

            embed = discord.Embed(
                title="🎥 Novo Vídeo Publicado!",
                description=formatted_message,
                color=discord.Color.red(),
                url=video_url
            )
            embed.add_field(name="📺 Canal", value=channel_name, inline=True)
            embed.add_field(name="🎬 Vídeo", value=f"[{title}]({video_url})", inline=False)
            embed.timestamp = datetime.utcnow()

            await channel.send(embed=embed)
            print(f"✅ Notificação enviada para {channel.name}")

        except discord.Forbidden:
            print(f"❌ Sem permissão para enviar no canal {discord_channel_id}")
        except discord.HTTPException as e:
            print(f"❌ Erro HTTP ao enviar notificação: {e}")
        except Exception as e:
            print(f"❌ Erro ao enviar notificação: {e}")

    @check_new_videos.before_loop
    async def before_check_videos(self):
        """Aguarda o bot estar pronto antes de iniciar o loop"""
        await self.bot.wait_until_ready()
        print("🔄 Sistema YouTube iniciado - verificação a cada 10 minutos")

    @check_new_videos.error
    async def check_videos_error_handler(self, error):
        """Lida com erros no loop de verificação"""
        print(f"❌ Erro no loop de verificação YouTube: {error}")
        # Aguarda um pouco antes de tentar novamente
        await asyncio.sleep(60)

    @commands.command(name='helpyt')
    async def help_youtube(self, ctx):
        """Mostra ajuda sobre os comandos do sistema YouTube"""
        embed = discord.Embed(
            title="📺 Sistema YouTube - Ajuda",
            description="Lista de comandos disponíveis:",
            color=discord.Color.red()
        )
        
        embed.add_field(
            name="➕ Adicionar Canal",
            value="`!adicionaryt <URL> #canal` - Adiciona canal para monitoramento",
            inline=False
        )
        
        embed.add_field(
            name="➖ Remover Canal",
            value="`!removeryt <URL>` - Remove canal do monitoramento",
            inline=False
        )
        
        embed.add_field(
            name="💬 Configurar Mensagem",
            value="`!mensagemyt <mensagem>` - Define mensagem de notificação",
            inline=False
        )
        
        embed.add_field(
            name="📋 Listar Configurações",
            value="`!listaryt` - Ver todos os canais configurados",
            inline=False
        )
        
        embed.add_field(
            name="📝 Variáveis para Mensagem",
            value="`{title}` - Título do vídeo\n`{channel}` - Nome do canal\n`{url}` - URL do vídeo",
            inline=False
        )
        
        embed.set_footer(text="Todos os comandos requerem permissão de Administrador • Verificação automática a cada 10 minutos")
        await ctx.send(embed=embed)

    async def cog_unload(self):
        """Para o loop e fecha a conexão quando o cog é descarregado"""
        self.check_new_videos.cancel()
        if self.client:
            self.client.close()
            print("🔌 Conexão YouTube com MongoDB fechada")

async def setup(bot):
    await bot.add_cog(YouTubeSystem(bot))