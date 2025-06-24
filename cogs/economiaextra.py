import discord
from discord.ext import commands
import random
import os
from motor.motor_asyncio import AsyncIOMotorClient

class EconomiaExtra(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.client = AsyncIOMotorClient(os.getenv("MONGO_URI"))
        self.db = self.client["economia"]
        self.users = self.db["users"]
        self.shop = self.db["shop"]
        self.jobs = {
            "entregador": {"salary": (200, 800), "desc": "Entrega comidas"},
            "caixa": {"salary": (300, 600), "desc": "Atende clientes"},
            "programador": {"salary": (1000, 1500), "desc": "Desenvolve apps"},
            "medico": {"salary": (1500, 2500), "desc": "Cuida da saúde"}
        }

    def format_money(self, value):
        return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    async def get_data(self, user_id):
        user_id = str(user_id)
        data = await self.users.find_one({"_id": user_id})
        if not data:
            data = {"_id": user_id, "balance": 0, "bank": 0, "inventory": {}, "job": None, "employees": []}
            await self.users.insert_one(data)
        return data

    async def update_data(self, user_id, new_data):
        await self.users.update_one({"_id": str(user_id)}, {"$set": new_data})

    @commands.command()
    @commands.cooldown(1, 86400, commands.BucketType.user)
    async def loteria(self, ctx):
        try:
            data = await self.get_data(ctx.author.id)
            preco = 1000
            if data["balance"] < preco:
                return await ctx.send("❌ Você precisa de R$ 1.000 para jogar na loteria.")

            data["balance"] -= preco
            chance = random.randint(1, 100)
            if chance <= 5:
                premio = random.randint(10000, 50000)
                data["balance"] += premio
                await ctx.send(f"🎉 Você ganhou na loteria! Prêmio: {self.format_money(premio)}")
            else:
                await ctx.send("😢 Você não ganhou na loteria desta vez.")

            await self.update_data(ctx.author.id, data)
        except Exception as e:
            await ctx.send("❌ Erro ao processar loteria.")

    @commands.command()
    async def empregos(self, ctx):
        try:
            embed = discord.Embed(title="💼 Lista de Empregos", color=0x00ff00)
            for nome, info in self.jobs.items():
                sal_min = self.format_money(info['salary'][0])
                sal_max = self.format_money(info['salary'][1])
                embed.add_field(
                    name=nome.title(), 
                    value=f"{info['desc']}\nSalário: {sal_min} - {sal_max}", 
                    inline=False
                )
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send("❌ Erro ao carregar empregos.")

    @commands.command()
    async def vender(self, ctx, *, item):
        try:
            item = item.lower().strip()
            data = await self.get_data(ctx.author.id)
            inv = data.get("inventory", {})
            
            if not inv.get(item, 0):
                return await ctx.send("❌ Você não possui este item!")

            shop_item = await self.shop.find_one({"item": item})
            if not shop_item:
                return await ctx.send("❌ Este item não pode ser vendido!")

            valor = max(1, int(shop_item["price"] * 0.5))
            inv[item] -= 1
            if inv[item] <= 0:
                del inv[item]
            
            data["inventory"] = inv
            data["balance"] += valor
            await self.update_data(ctx.author.id, data)
            await ctx.send(f"💸 Você vendeu **{item.title()}** por {self.format_money(valor)}!")
        except Exception as e:
            await ctx.send("❌ Erro ao vender item.")

    @commands.command()
    async def contratar(self, ctx, membro: discord.Member):
        try:
            if membro.bot:
                return await ctx.send("❌ Você não pode contratar bots!")
            
            if membro.id == ctx.author.id:
                return await ctx.send("❌ Você não pode se contratar!")

            data = await self.get_data(ctx.author.id)
            employees = data.get("employees", [])
            
            if membro.id in employees:
                return await ctx.send("❌ Este usuário já trabalha para você.")

            if len(employees) >= 10:
                return await ctx.send("❌ Você já tem o máximo de funcionários (10).")

            employees.append(membro.id)
            data["employees"] = employees
            await self.update_data(ctx.author.id, data)
            await ctx.send(f"📋 Você contratou {membro.mention}!")
        except Exception as e:
            await ctx.send("❌ Erro ao contratar usuário.")

    @commands.command()
    async def demitir(self, ctx, membro: discord.Member):
        try:
            data = await self.get_data(ctx.author.id)
            employees = data.get("employees", [])
            
            if membro.id not in employees:
                return await ctx.send("❌ Este usuário não trabalha para você.")

            employees.remove(membro.id)
            data["employees"] = employees
            await self.update_data(ctx.author.id, data)
            await ctx.send(f"📋 Você demitiu {membro.mention}.")
        except Exception as e:
            await ctx.send("❌ Erro ao demitir usuário.")

    @commands.has_permissions(administrator=True)
    @commands.command(name='dar')
    async def give_money(self, ctx, user: discord.Member, amount: int):
        try:
            if amount <= 0:
                return await ctx.send("❌ O valor deve ser positivo!")
            
            if amount > 1000000:
                return await ctx.send("❌ Valor muito alto! Máximo: R$ 1.000.000")

            data = await self.get_data(user.id)
            data["balance"] += amount
            await self.update_data(user.id, data)
            await ctx.send(f"💰 Você deu {self.format_money(amount)} para {user.mention}!")
        except Exception as e:
            await ctx.send("❌ Erro ao dar dinheiro.")

    @commands.command()
    async def funcionarios(self, ctx):
        try:
            data = await self.get_data(ctx.author.id)
            employees = data.get("employees", [])
            
            if not employees:
                return await ctx.send("❌ Você não tem funcionários.")

            embed = discord.Embed(title="👥 Seus Funcionários", color=0x3498db)
            funcionarios_text = ""
            
            for i, emp_id in enumerate(employees[:10], 1):
                try:
                    user = self.bot.get_user(emp_id)
                    if user:
                        funcionarios_text += f"{i}. {user.mention}\n"
                    else:
                        funcionarios_text += f"{i}. Usuário não encontrado\n"
                except:
                    continue
            
            if funcionarios_text:
                embed.description = funcionarios_text
            else:
                embed.description = "Nenhum funcionário válido encontrado."
                
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send("❌ Erro ao listar funcionários.")

async def setup(bot):
    await bot.add_cog(EconomiaExtra(bot))