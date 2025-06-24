import discord
from discord.ext import commands
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
import random
import logging

class Diversao(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.client = None
        self.db = None
        self.collection = None
        self._connection_ready = False
        # Inicializa a conexão com MongoDB
        self.bot.loop.create_task(self.init_database())

    async def init_database(self):
        """Inicializa a conexão com MongoDB"""
        try:
            mongo_uri = os.getenv("MONGO_URI")
            
            if not mongo_uri:
                print("❌ MONGO_URI não encontrada nas variáveis de ambiente!")
                return
            
            print("🔄 Conectando ao MongoDB (Diversão)...")
            self.client = AsyncIOMotorClient(mongo_uri)
            
            # Testa a conexão
            await self.client.admin.command('ping')
            
            self.db = self.client['discord_bot']
            self.collection = self.db['diversao_data']
            self._connection_ready = True
            
            print("✅ Conectado ao MongoDB (Diversão) com sucesso!")
            
        except Exception as e:
            print(f"❌ Erro ao conectar com MongoDB (Diversão): {e}")
            self._connection_ready = False

    async def ensure_connection(self):
        """Garante que a conexão com MongoDB está ativa"""
        if not self._connection_ready:
            await self.init_database()
        return self._connection_ready

    # ============ COMANDOS DE EVENTO ============
    @commands.group(invoke_without_command=True, aliases=["evento"])
    async def evento(self, ctx):
        embed = discord.Embed(
            title="🎉 Evento de Reações",
            description="**Comandos disponíveis:**\n• `!evento entrar` - Entrar no evento\n• `!evento stats` - Ver estatísticas\n• `!evento inventario` - Ver inventário\n• `!evento rank` - Ver ranking\n• `!evento sair` - Sair do evento",
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)

    @evento.command(name="entrar")
    async def evento_entrar(self, ctx):
        embed = discord.Embed(
            title="✅ Evento Entrar",
            description=f"{ctx.author.mention}, você entrou no Evento de Reações!",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @evento.command(name="stats")
    async def evento_stats(self, ctx):
        embed = discord.Embed(
            title="📊 Estatísticas do Evento",
            description=f"**{ctx.author.display_name}**\n🎁 Presentes coletados: 0\n⭐ Pontos: 0\n🏆 Posição: #1",
            color=discord.Color.orange()
        )
        await ctx.send(embed=embed)

    @evento.command(name="inventario", aliases=["inventário"])
    async def evento_inventario(self, ctx):
        embed = discord.Embed(
            title="🎒 Inventário do Evento",
            description="Seu inventário está vazio. Participe do evento para coletar itens!",
            color=discord.Color.purple()
        )
        await ctx.send(embed=embed)

    @evento.command(name="rank")
    async def evento_rank(self, ctx):
        embed = discord.Embed(
            title="🏆 Ranking do Evento",
            description="**Top 10 coletores de presentes:**\n1. Ninguém ainda\n2. Seja o primeiro!\n3. ...",
            color=discord.Color.gold()
        )
        await ctx.send(embed=embed)

    @evento.command(name="sair")
    async def evento_sair(self, ctx):
        embed = discord.Embed(
            title="❌ Evento Sair",
            description=f"{ctx.author.mention}, você saiu do Evento de Reações.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)

    # ============ COMANDOS DE JOGOS ============
    @commands.command(aliases=["dançascadeiras"])
    async def dancadascadeiras(self, ctx):
        embed = discord.Embed(
            title="💃 Dança das Cadeiras",
            description="🎵 Vamos brincar de Dança das Cadeiras! A música começou!",
            color=discord.Color.magenta()
        )
        await ctx.send(embed=embed)

    @commands.command(aliases=["shippar"])
    async def ship(self, ctx, member1: discord.Member = None, member2: discord.Member = None):
        if member1 is None or member2 is None:
            embed = discord.Embed(
                title="💕 Ship",
                description="Você precisa mencionar **dois membros** para shippar!\nExemplo: `!ship @pessoa1 @pessoa2`",
                color=discord.Color.red()
            )
        else:
            compatibility = random.randint(0, 100)
            hearts = "💖" if compatibility >= 80 else "💝" if compatibility >= 60 else "💛" if compatibility >= 40 else "💔"
            embed = discord.Embed(
                title="💕 Ship Result",
                description=f"{hearts} **{member1.display_name}** x **{member2.display_name}**\n\n**Compatibilidade: {compatibility}%**",
                color=discord.Color.pink()
            )
        await ctx.send(embed=embed)

    @commands.command(aliases=["dice", "dado"])
    async def rolar(self, ctx, dados: int = 1, lados: int = 6):
        if dados > 10:
            dados = 10
        if lados > 100:
            lados = 100
            
        results = [random.randint(1, lados) for _ in range(dados)]
        total = sum(results)
        
        embed = discord.Embed(
            title="🎲 Rolar Dados",
            description=f"**{dados}d{lados}**\n\n🎯 Resultados: {', '.join(map(str, results))}\n📊 Total: **{total}**",
            color=discord.Color.dark_blue()
        )
        await ctx.send(embed=embed)

    @commands.command(aliases=["flipcoin", "caracoroa"])
    async def girarmoeda(self, ctx):
        result = random.choice(["Cara", "Coroa"])
        emoji = "🟡" if result == "Cara" else "⚪"
        embed = discord.Embed(
            title="🪙 Girar Moeda",
            description=f"{emoji} **{result}**!",
            color=discord.Color.gold()
        )
        await ctx.send(embed=embed)

    @commands.command()
    async def vieirinha(self, ctx, *, pergunta: str = None):
        if not pergunta:
            embed = discord.Embed(
                title="🔮 Vieirinha",
                description="Faça uma pergunta para a Vieirinha!\nExemplo: `!vieirinha Vai chover hoje?`",
                color=discord.Color.blue()
            )
        else:
            responses = [
                "Sim, com certeza!", "Não, de jeito nenhum.", "Talvez...", 
                "É muito provável.", "Não conte com isso.", "Definitivamente sim!",
                "Melhor não te falar agora.", "Não posso prever isso.", "Claro que sim!"
            ]
            answer = random.choice(responses)
            embed = discord.Embed(
                title="🔮 Resposta da Vieirinha",
                description=f"**Pergunta:** {pergunta}\n\n**Resposta:** {answer}",
                color=discord.Color.purple()
            )
        await ctx.send(embed=embed)

    @commands.command(aliases=["hg"])
    async def jogosvorazes(self, ctx, *participantes: discord.Member):
        if len(participantes) < 2:
            embed = discord.Embed(
                title="⚔️ Jogos Vorazes",
                description="Mencione pelo menos **2 participantes** para simular os Jogos Vorazes!\nExemplo: `!jogosvorazes @pessoa1 @pessoa2 @pessoa3`",
                color=discord.Color.red()
            )
        else:
            vencedor = random.choice(participantes)
            participantes_nomes = [p.display_name for p in participantes]
            
            embed = discord.Embed(
                title="⚔️ Jogos Vorazes",
                description=f"**Participantes:** {', '.join(participantes_nomes)}\n\n🏆 **Vencedor:** {vencedor.mention}\n\n*Que os jogos comecem!*",
                color=discord.Color.dark_red()
            )
        await ctx.send(embed=embed)

    @commands.command(aliases=["pedrapapeltesoura", "ppt"])
    async def jankenpon(self, ctx, escolha: str = None):
        opcoes = ["pedra", "papel", "tesoura"]
        emojis = {"pedra": "🗿", "papel": "📄", "tesoura": "✂️"}
        
        if escolha is None or escolha.lower() not in opcoes:
            embed = discord.Embed(
                title="✂️ Jankenpon",
                description="Escolha: **pedra**, **papel** ou **tesoura**\nExemplo: `!jankenpon pedra`",
                color=discord.Color.greyple()
            )
        else:
            escolha_user = escolha.lower()
            escolha_bot = random.choice(opcoes)
            
            # Determina o resultado
            if escolha_user == escolha_bot:
                resultado = "Empate!"
                cor = discord.Color.yellow()
            elif (escolha_user == "pedra" and escolha_bot == "tesoura") or \
                 (escolha_user == "papel" and escolha_bot == "pedra") or \
                 (escolha_user == "tesoura" and escolha_bot == "papel"):
                resultado = "Você ganhou!"
                cor = discord.Color.green()
            else:
                resultado = "Você perdeu!"
                cor = discord.Color.red()
            
            embed = discord.Embed(
                title="✂️ Jankenpon",
                description=f"Você: {emojis[escolha_user]} **{escolha_user}**\nBot: {emojis[escolha_bot]} **{escolha_bot}**\n\n**{resultado}**",
                color=cor
            )
        await ctx.send(embed=embed)

    # ============ COMANDOS DE AVALIAÇÃO ============
    @commands.command(aliases=["ratewaifu", "avaliarwaifu"])
    async def avaliar_waifu(self, ctx, *, waifu: str = None):
        if not waifu:
            embed = discord.Embed(
                title="💖 Avaliar Waifu",
                description="Forneça o nome da waifu para avaliarmos!\nExemplo: `!avaliar_waifu Zero Two`",
                color=discord.Color.red()
            )
        else:
            nota = random.randint(1, 10)
            stars = "⭐" * nota + "☆" * (10 - nota)
            embed = discord.Embed(
                title="💖 Avaliar Waifu",
                description=f"**{waifu}**\n\n{stars}\n**Nota: {nota}/10**",
                color=discord.Color.pink()
            )
        await ctx.send(embed=embed)

    @commands.command(aliases=["ratehusbando", "avaliarhusbando"])
    async def avaliar_husbando(self, ctx, *, husbando: str = None):
        if not husbando:
            embed = discord.Embed(
                title="💙 Avaliar Husbando",
                description="Forneça o nome do husbando para avaliarmos!\nExemplo: `!avaliar_husbando Levi`",
                color=discord.Color.red()
            )
        else:
            nota = random.randint(1, 10)
            stars = "⭐" * nota + "☆" * (10 - nota)
            embed = discord.Embed(
                title="💙 Avaliar Husbando",
                description=f"**{husbando}**\n\n{stars}\n**Nota: {nota}/10**",
                color=discord.Color.blue()
            )
        await ctx.send(embed=embed)

    # ============ COMANDOS DE TEXTO ============
    def vaporwave_text(self, text: str) -> str:
        return ''.join(chr(0xFF01 + (ord(c) - 33)) if 33 <= ord(c) <= 126 else c for c in text)

    @commands.command()
    async def vaporwave(self, ctx, *, message: str):
        transformed = self.vaporwave_text(message)
        embed = discord.Embed(
            title="🌊 Texto Vaporwave",
            description=transformed,
            color=discord.Color.purple()
        )
        await ctx.send(embed=embed)

    @commands.command()
    async def maiusculo(self, ctx, *, message: str):
        embed = discord.Embed(
            title="🔤 Texto Maiúsculo",
            description=message.upper(),
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)

    @commands.command()
    async def minusculo(self, ctx, *, message: str):
        embed = discord.Embed(
            title="🔡 Texto Minúsculo",
            description=message.lower(),
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)

    @commands.command()
    async def zombar(self, ctx, *, message: str):
        transformed = ''.join(c.upper() if random.random() > 0.5 else c.lower() for c in message)
        embed = discord.Embed(
            title="🤡 Texto Zombar",
            description=transformed,
            color=discord.Color.dark_purple()
        )
        await ctx.send(embed=embed)

    @commands.command()
    async def palmas(self, ctx, *, message: str):
        transformed = "👏".join(message.split())
        embed = discord.Embed(
            title="👏 Texto Palmas",
            description=transformed,
            color=discord.Color.gold()
        )
        await ctx.send(embed=embed)

    # ============ COMANDOS DE INVOCAÇÃO ============
    @commands.command(aliases=["tiodopave", "piada"])
    async def invocar_tiodopave(self, ctx):
        piadas = [
            "É pra vê ou pra comer? 🥧",
            "Qual é o cúmulo da sorte? Encontrar um fósforo em cima de uma caixa de fósforos!",
            "Por que o pássaro foi ao médico? Porque ele estava com a asa quebrada!"
        ]
        piada = random.choice(piadas)
        embed = discord.Embed(
            title="👨‍🦳 Tio do Pavê Invocado",
            description=piada,
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @commands.command(aliases=["faustao"])
    async def invocar_faustao(self, ctx):
        frases = [
            "Êêêê... Macarrão!",
            "Você quer dinheiro?",
            "Oloco, meu!"
        ]
        frase = random.choice(frases)
        embed = discord.Embed(
            title="📺 Faustão Invocado",
            description=f"**{frase}**\n\nO amado Faustão chegou ao seu servidor!",
            color=discord.Color.orange()
        )
        await ctx.send(embed=embed)

    @commands.command(aliases=["kenji"])
    async def invocar_kenji(self, ctx):
        embed = discord.Embed(
            title="🎌 Kenji Invocado",
            description="**Hai minasan genki deska!**\n\nKenji chegou direto do Loop Infinito!",
            color=discord.Color.teal()
        )
        await ctx.send(embed=embed)

    # ============ COMANDOS DE MEME ============
    @commands.command()
    async def cancelar(self, ctx, member: discord.Member = None):
        if member:
            target = member.display_name
        else:
            target = "alguém aleatório"
        
        embed = discord.Embed(
            title="🚫 CANCELADO",
            description=f"**{target}** foi cancelado pela cultura de cancelamento do Twitter!",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)

    @commands.command()
    async def tristerealidade(self, ctx):
        embed = discord.Embed(
            title="😔 Triste Realidade",
            description="A triste realidade é que todos nós vamos morrer um dia... mas pelo menos temos memes!",
            color=discord.Color.dark_gray()
        )
        await ctx.send(embed=embed)

    @commands.command()
    async def todogrupotem(self, ctx):
        tipos = [
            "👑 O líder", "🤡 O palhaço", "😴 O que sempre dorme",
            "📱 O viciado no celular", "🍕 O que sempre tem fome",
            "💰 O rico", "😭 O dramático", "🧠 O inteligente",
            "🎮 O gamer", "📚 O nerd"
        ]
        
        embed = discord.Embed(
            title="👥 Todo Grupo Tem",
            description="**Todo grupo tem:**\n" + "\n".join(tipos),
            color=discord.Color.dark_orange()
        )
        await ctx.send(embed=embed)

    # ============ COMANDO DE AJUDA ============
    @commands.command(name='helpdiversao')
    async def help_diversao(self, ctx):
        embed = discord.Embed(
            title="🎮 Sistema de Diversão - Ajuda",
            description="Lista de comandos disponíveis:",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="🎉 Eventos",
            value="`!evento` - Ver comandos do evento\n`!evento entrar/sair/stats/rank/inventario`",
            inline=False
        )
        
        embed.add_field(
            name="🎲 Jogos",
            value="`!ship @user1 @user2` - Shipp entre usuários\n`!rolar [dados] [lados]` - Rolar dados\n`!girarmoeda` - Cara ou coroa\n`!jankenpon pedra/papel/tesoura`",
            inline=False
        )
        
        embed.add_field(
            name="🎨 Texto",
            value="`!vaporwave texto` - Estilo vaporwave\n`!maiusculo/minusculo texto`\n`!zombar texto` - Texto alternado\n`!palmas texto` - Separar com palmas",
            inline=False
        )
        
        embed.add_field(
            name="⭐ Avaliação",
            value="`!avaliar_waifu nome` - Avaliar waifu\n`!avaliar_husbando nome` - Avaliar husbando",
            inline=False
        )
        
        embed.add_field(
            name="🎭 Diversão",
            value="`!vieirinha pergunta` - Perguntar à Vieirinha\n`!cancelar [@user]` - Cancelar alguém\n`!todogrupotem` - Tipos de pessoas",
            inline=False
        )
        
        await ctx.send(embed=embed)

    async def cog_unload(self):
        """Fecha a conexão com MongoDB quando o cog é descarregado"""
        if self.client:
            self.client.close()
            print("🔌 Conexão com MongoDB (Diversão) fechada")

async def setup(bot):
    await bot.add_cog(Diversao(bot))