import discord
from discord.ext import commands
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import random
from datetime import datetime, timedelta

class EconomySystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.client = None
        self.db = None
        self.collection = None
        self._connection_ready = False
        # Lista de empregos disponíveis
        self.empregos = {
            "programador": {"salario": 5000, "descricao": "💻 Desenvolve sistemas e aplicações"},
            "medico": {"salario": 8000, "descricao": "🏥 Cuida da saúde das pessoas"},
            "professor": {"salario": 3500, "descricao": "📚 Ensina e educa estudantes"},
            "empresario": {"salario": 12000, "descricao": "💼 Gerencia negócios e empresas"},
            "artista": {"salario": 4000, "descricao": "🎨 Cria obras de arte e entretenimento"}
        }
        self.bot.loop.create_task(self.init_database())

    async def init_database(self):
        """Inicializa a conexão com MongoDB"""
        try:
            mongo_uri = os.getenv("MONGO_URI")
            if not mongo_uri:
                print("❌ MONGO_URI não encontrada nas variáveis de ambiente!")
                return
            
            print("🔄 Conectando ao MongoDB (Economy)...")
            self.client = AsyncIOMotorClient(mongo_uri)
            await self.client.admin.command('ping')
            
            self.db = self.client['discord_bot']
            self.collection = self.db['economy_data']
            self._connection_ready = True
            
            print("✅ Conectado ao MongoDB (Economy) com sucesso!")
            
        except Exception as e:
            print(f"❌ Erro ao conectar com MongoDB (Economy): {e}")
            self._connection_ready = False

    async def ensure_connection(self):
        """Garante que a conexão com MongoDB está ativa"""
        if not self._connection_ready:
            await self.init_database()
        return self._connection_ready

    async def get_user_data(self, user_id, guild_id):
        """Obtém dados do usuário do MongoDB"""
        try:
            if not await self.ensure_connection():
                return {}
                
            data = await self.collection.find_one({"user_id": str(user_id), "guild_id": str(guild_id)})
            return data if data else {}
            
        except Exception as e:
            print(f"❌ Erro ao buscar dados do usuário: {e}")
            return {}

    async def update_user_data(self, user_id, guild_id, update_data):
        """Atualiza dados do usuário no MongoDB"""
        try:
            if not await self.ensure_connection():
                return False
            
            await self.collection.update_one(
                {"user_id": str(user_id), "guild_id": str(guild_id)},
                {"$set": update_data},
                upsert=True
            )
            return True
                
        except Exception as e:
            print(f"❌ Erro ao atualizar dados do usuário: {e}")
            return False

    @commands.command(name='empregos')
    async def empregos(self, ctx):
        """Mostra todos os empregos disponíveis"""
        embed = discord.Embed(
            title="💼 Empregos Disponíveis",
            description="Escolha sua profissão e comece a ganhar dinheiro!",
            color=discord.Color.blue()
        )
        
        for emprego, info in self.empregos.items():
            embed.add_field(
                name=f"{emprego.title()}",
                value=f"{info['descricao']}\n💰 Salário: R$ {info['salario']:,}/dia",
                inline=True
            )
        
        embed.set_footer(text="Use !contratar <emprego> para se candidatar a um emprego")
        await ctx.send(embed=embed)

    @commands.command(name='contratar')
    async def contratar(self, ctx, *, emprego=None):
        """Contrata o usuário para um emprego"""
        if not emprego:
            embed = discord.Embed(
                title="❌ Emprego Não Especificado",
                description="Use: `!contratar <nome_do_emprego>`\nVeja os empregos disponíveis com `!empregos`",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        emprego = emprego.lower()
        if emprego not in self.empregos:
            embed = discord.Embed(
                title="❌ Emprego Não Encontrado",
                description=f"O emprego '{emprego}' não existe.\nUse `!empregos` para ver os disponíveis.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        user_data = await self.get_user_data(ctx.author.id, ctx.guild.id)
        
        if user_data.get('emprego'):
            embed = discord.Embed(
                title="❌ Já Tem Emprego",
                description=f"Você já trabalha como **{user_data['emprego'].title()}**.\nUse `!demitir` primeiro se quiser trocar de emprego.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        # Contrata o usuário
        update_data = {
            'emprego': emprego,
            'ultimo_salario': datetime.utcnow().isoformat()
        }
        
        success = await self.update_user_data(ctx.author.id, ctx.guild.id, update_data)
        
        if success:
            info = self.empregos[emprego]
            embed = discord.Embed(
                title="✅ Contratado!",
                description=f"Parabéns! Você foi contratado como **{emprego.title()}**!\n\n{info['descricao']}\n💰 Salário: R$ {info['salario']:,}/dia",
                color=discord.Color.green()
            )
            embed.set_footer(text="Você pode receber seu salário a cada 24 horas!")
        else:
            embed = discord.Embed(
                title="❌ Erro",
                description="Não foi possível processar a contratação.",
                color=discord.Color.red()
            )
        
        await ctx.send(embed=embed)

    @commands.command(name='demitir')
    async def demitir(self, ctx):
        """Demite o usuário do emprego atual"""
        user_data = await self.get_user_data(ctx.author.id, ctx.guild.id)
        
        if not user_data.get('emprego'):
            embed = discord.Embed(
                title="❌ Sem Emprego",
                description="Você não tem um emprego atual.\nUse `!empregos` para ver as vagas disponíveis.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        emprego_atual = user_data['emprego']
        
        # Remove o emprego
        update_data = {
            'emprego': None,
            'ultimo_salario': None
        }
        
        success = await self.update_user_data(ctx.author.id, ctx.guild.id, update_data)
        
        if success:
            embed = discord.Embed(
                title="✅ Demitido",
                description=f"Você se demitiu do cargo de **{emprego_atual.title()}**.\nPode se candidatar a um novo emprego quando quiser!",
                color=discord.Color.green()
            )
        else:
            embed = discord.Embed(
                title="❌ Erro",
                description="Não foi possível processar a demissão.",
                color=discord.Color.red()
            )
        
        await ctx.send(embed=embed)

    @commands.command(name='funcionarios')
    async def funcionarios(self, ctx):
        """Mostra todos os funcionários do servidor"""
        try:
            if not await self.ensure_connection():
                embed = discord.Embed(
                    title="❌ Erro de Conexão",
                    description="Não foi possível conectar ao banco de dados.",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return

            # Busca todos os usuários com emprego neste servidor
            funcionarios = await self.collection.find(
                {"guild_id": str(ctx.guild.id), "emprego": {"$ne": None}}
            ).to_list(length=None)

            if not funcionarios:
                embed = discord.Embed(
                    title="📋 Lista de Funcionários",
                    description="Nenhum funcionário encontrado neste servidor.",
                    color=discord.Color.blue()
                )
                await ctx.send(embed=embed)
                return

            # Agrupa funcionários por emprego
            empregos_count = {}
            funcionarios_list = []

            for func in funcionarios:
                emprego = func['emprego']
                user = self.bot.get_user(int(func['user_id']))
                user_name = user.display_name if user else f"Usuário {func['user_id']}"
                
                funcionarios_list.append(f"• {user_name} - **{emprego.title()}**")
                empregos_count[emprego] = empregos_count.get(emprego, 0) + 1

            embed = discord.Embed(
                title="📋 Lista de Funcionários",
                description=f"**Total: {len(funcionarios)} funcionários**\n\n" + "\n".join(funcionarios_list[:20]),
                color=discord.Color.blue()
            )

            # Adiciona estatísticas por emprego
            stats = "\n".join([f"**{emp.title()}:** {count}" for emp, count in empregos_count.items()])
            embed.add_field(name="📊 Por Profissão", value=stats, inline=False)
            
            if len(funcionarios) > 20:
                embed.set_footer(text=f"Mostrando apenas os primeiros 20 de {len(funcionarios)} funcionários")
            
            await ctx.send(embed=embed)

        except Exception as e:
            print(f"❌ Erro no comando funcionarios: {e}")
            embed = discord.Embed(
                title="❌ Erro",
                description="Ocorreu um erro ao buscar os funcionários.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

    @commands.command(name='presentear')
    async def presentear(self, ctx, membro: discord.Member, quantia: int):
        """Presenteia outro membro com dinheiro"""
        if membro == ctx.author:
            embed = discord.Embed(
                title="❌ Ação Inválida",
                description="Você não pode presentear a si mesmo!",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        if quantia <= 0:
            embed = discord.Embed(
                title="❌ Quantia Inválida",
                description="A quantia deve ser maior que zero!",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        # Busca dados de ambos usuários
        sender_data = await self.get_user_data(ctx.author.id, ctx.guild.id)
        receiver_data = await self.get_user_data(membro.id, ctx.guild.id)

        sender_balance = sender_data.get('saldo', 0)
        
        if sender_balance < quantia:
            embed = discord.Embed(
                title="❌ Saldo Insuficiente",
                description=f"Você tem apenas R$ {sender_balance:,}!\nQuantia solicitada: R$ {quantia:,}",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        # Realiza a transferência
        new_sender_balance = sender_balance - quantia
        new_receiver_balance = receiver_data.get('saldo', 0) + quantia

        sender_success = await self.update_user_data(ctx.author.id, ctx.guild.id, {'saldo': new_sender_balance})
        receiver_success = await self.update_user_data(membro.id, ctx.guild.id, {'saldo': new_receiver_balance})

        if sender_success and receiver_success:
            embed = discord.Embed(
                title="🎁 Presente Enviado!",
                description=f"**{ctx.author.mention}** presenteou **{membro.mention}** com R$ {quantia:,}!",
                color=discord.Color.green()
            )
            embed.add_field(name="💰 Seu Saldo", value=f"R$ {new_sender_balance:,}", inline=True)
            embed.add_field(name="🎯 Saldo do Presenteado", value=f"R$ {new_receiver_balance:,}", inline=True)
        else:
            embed = discord.Embed(
                title="❌ Erro",
                description="Não foi possível processar o presente.",
                color=discord.Color.red()
            )

        await ctx.send(embed=embed)

    @commands.command(name='transferir')
    async def transferir(self, ctx, membro: discord.Member, quantia: int):
        """Transfere dinheiro para outro membro"""
        if membro == ctx.author:
            embed = discord.Embed(
                title="❌ Ação Inválida",
                description="Você não pode transferir dinheiro para si mesmo!",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        if quantia <= 0:
            embed = discord.Embed(
                title="❌ Quantia Inválida",
                description="A quantia deve ser maior que zero!",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        # Taxa de transferência (2%)
        taxa = max(1, int(quantia * 0.02))
        total_necessario = quantia + taxa

        sender_data = await self.get_user_data(ctx.author.id, ctx.guild.id)
        receiver_data = await self.get_user_data(membro.id, ctx.guild.id)

        sender_balance = sender_data.get('saldo', 0)
        
        if sender_balance < total_necessario:
            embed = discord.Embed(
                title="❌ Saldo Insuficiente",
                description=f"Você precisa de R$ {total_necessario:,}!\n(R$ {quantia:,} + R$ {taxa:,} de taxa)\nSeu saldo: R$ {sender_balance:,}",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        # Realiza a transferência
        new_sender_balance = sender_balance - total_necessario
        new_receiver_balance = receiver_data.get('saldo', 0) + quantia

        sender_success = await self.update_user_data(ctx.author.id, ctx.guild.id, {'saldo': new_sender_balance})
        receiver_success = await self.update_user_data(membro.id, ctx.guild.id, {'saldo': new_receiver_balance})

        if sender_success and receiver_success:
            embed = discord.Embed(
                title="💸 Transferência Realizada!",
                description=f"**{ctx.author.mention}** transferiu R$ {quantia:,} para **{membro.mention}**",
                color=discord.Color.green()
            )
            embed.add_field(name="💰 Seu Saldo", value=f"R$ {new_sender_balance:,}", inline=True)
            embed.add_field(name="🎯 Saldo do Destinatário", value=f"R$ {new_receiver_balance:,}", inline=True)
            embed.add_field(name="📊 Taxa Cobrada", value=f"R$ {taxa:,} (2%)", inline=True)
        else:
            embed = discord.Embed(
                title="❌ Erro",
                description="Não foi possível processar a transferência.",
                color=discord.Color.red()
            )

        await ctx.send(embed=embed)

    @commands.command(name='vender')
    async def vender(self, ctx, *, item=None):
        """Vende itens por dinheiro"""
        if not item:
            embed = discord.Embed(
                title="❌ Item Não Especificado",
                description="Use: `!vender <nome_do_item>`",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        # Lista de itens que podem ser vendidos
        itens_venda = {
            "sucata": {"preco": 50, "descricao": "🔧 Peças de metal velhas"},
            "madeira": {"preco": 30, "descricao": "🪵 Tábuas de madeira"},
            "pedra": {"preco": 20, "descricao": "🪨 Pedras comuns"},
            "ferro": {"preco": 100, "descricao": "⚙️ Barras de ferro"},
            "ouro": {"preco": 500, "descricao": "✨ Pepitas de ouro"},
            "diamante": {"preco": 1000, "descricao": "💎 Diamantes raros"}
        }

        item = item.lower()
        if item not in itens_venda:
            embed = discord.Embed(
                title="❌ Item Inválido",
                description=f"'{item}' não pode ser vendido.\n**Itens vendáveis:** " + ", ".join(itens_venda.keys()),
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        # Simula ter o item (em um sistema real, verificaria o inventário)
        chance_ter_item = random.randint(1, 100)
        if chance_ter_item <= 30:  # 30% de chance de não ter o item
            embed = discord.Embed(
                title="❌ Item Não Encontrado",
                description=f"Você não possui **{item}** para vender!",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        # Vende o item
        user_data = await self.get_user_data(ctx.author.id, ctx.guild.id)
        item_info = itens_venda[item]
        preco_venda = random.randint(int(item_info['preco'] * 0.8), int(item_info['preco'] * 1.2))
        
        new_balance = user_data.get('saldo', 0) + preco_venda
        success = await self.update_user_data(ctx.author.id, ctx.guild.id, {'saldo': new_balance})

        if success:
            embed = discord.Embed(
                title="💰 Item Vendido!",
                description=f"Você vendeu **{item.title()}** por R$ {preco_venda:,}!",
                color=discord.Color.green()
            )
            embed.add_field(name="🏷️ Descrição", value=item_info['descricao'], inline=False)
            embed.add_field(name="💵 Novo Saldo", value=f"R$ {new_balance:,}", inline=True)
        else:
            embed = discord.Embed(
                title="❌ Erro",
                description="Não foi possível processar a venda.",
                color=discord.Color.red()
            )

        await ctx.send(embed=embed)

    async def cog_unload(self):
        """Fecha a conexão com MongoDB quando o cog é descarregado"""
        if self.client:
            self.client.close()
            print("🔌 Conexão com MongoDB (Economy) fechada")

async def setup(bot):
    await bot.add_cog(EconomySystem(bot))