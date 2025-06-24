import discord
from discord.ext import commands
import asyncio
import random
from datetime import datetime, timedelta
import os
from motor.motor_asyncio import AsyncIOMotorClient

class Economia(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.client = None
        self.db = None
        self.users_collection = None
        self.shop_collection = None
        self.vip_collection = None
        self._connection_ready = False
        self.bot.loop.create_task(self.init_database())
        
        # Configurações base
        self.daily_reward = 1000
        self.work_cooldown = 3600
        self.crime_cooldown = 7200
        
        # Jobs e crimes
        self.jobs = {
            "entregador": {"salary": (200, 800), "desc": "Entrega comidas"},
            "caixa": {"salary": (300, 600), "desc": "Atende clientes"},
            "programador": {"salary": (1000, 1500), "desc": "Desenvolve apps"},
            "medico": {"salary": (1500, 2500), "desc": "Cuida da saúde"}
        }
        
        self.crimes = {
            "roubar_loja": {"min": 100, "max": 1000, "success": 60},
            "hackear": {"min": 500, "max": 3000, "success": 30},
            "furto": {"min": 50, "max": 300, "success": 80}
        }

    async def init_database(self):
        try:
            mongo_uri = os.getenv("MONGO_URI")
            if not mongo_uri:
                return
            
            self.client = AsyncIOMotorClient(mongo_uri)
            await self.client.admin.command('ping')
            
            self.db = self.client['discord_bot']
            self.users_collection = self.db['users']
            self.shop_collection = self.db['shop']
            self.vip_collection = self.db['vip_data']
            self._connection_ready = True
            
            await self.initialize_shop_data()
        except Exception as e:
            self._connection_ready = False

    async def ensure_connection(self):
        if not self._connection_ready:
            await self.init_database()
        return self._connection_ready

    async def initialize_shop_data(self):
        try:
            if not await self.ensure_connection():
                return
            count = await self.shop_collection.count_documents({})
            if count == 0:
                items = [
                    {"item": "smartphone", "price": 1500, "desc": "Smartphone moderno"},
                    {"item": "notebook", "price": 3000, "desc": "Notebook para trabalho"},
                    {"item": "carro", "price": 50000, "desc": "Carro popular"},
                    {"item": "casa", "price": 200000, "desc": "Casa própria"}
                ]
                await self.shop_collection.insert_many(items)
        except:
            pass

    async def is_vip(self, user_id, guild_id):
        """Verifica se usuário é VIP usando a collection VIP"""
        try:
            if not await self.ensure_connection():
                return False
            
            vip_data = await self.vip_collection.find_one({
                "user_id": str(user_id),
                "guild_id": str(guild_id)
            })
            
            if vip_data:
                expiry = vip_data['expiry']
                return datetime.now() < expiry
            return False
        except:
            return False

    async def get_vip_multipliers(self, user_id, guild_id):
        """Retorna multiplicadores VIP"""
        if await self.is_vip(user_id, guild_id):
            return {
                "daily": 2.0,
                "work": 1.5, 
                "crime_success": 15,
                "rob_success": 20,
                "bet_luck": 10
            }
        return {
            "daily": 1.0,
            "work": 1.0,
            "crime_success": 0,
            "rob_success": 0,
            "bet_luck": 0
        }

    async def get_user_data(self, user_id):
        try:
            if not await self.ensure_connection():
                return self.get_default_user_data(str(user_id))
            user_id = str(user_id)
            data = await self.users_collection.find_one({"user_id": user_id})
            if not data:
                data = self.get_default_user_data(user_id)
                await self.users_collection.insert_one(data)
            return data
        except:
            return self.get_default_user_data(str(user_id))

    def get_default_user_data(self, user_id):
        return {
            "user_id": user_id, "balance": 0, "bank": 0, "inventory": {},
            "job": None, "last_daily": None, "last_work": None, "last_crime": None,
            "is_boss": False, "employees": []
        }

    async def update_user_data(self, user_id, data):
        try:
            if not await self.ensure_connection():
                return False
            await self.users_collection.update_one(
                {"user_id": str(user_id)}, {"$set": data}, upsert=True
            )
            return True
        except:
            return False

    def format_money(self, amount):
        return f"R$ {amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    @commands.command(name='saldo', aliases=['bal', 'balance'])
    async def balance(self, ctx, user: discord.Member = None):
        if user is None:
            user = ctx.author
        data = await self.get_user_data(user.id)
        is_vip_user = await self.is_vip(user.id, ctx.guild.id)
        
        embed = discord.Embed(title=f"💰 {user.display_name}", color=0xFFD700 if is_vip_user else 0x00ff00)
        embed.add_field(name="Carteira", value=self.format_money(data["balance"]), inline=True)
        embed.add_field(name="Banco", value=self.format_money(data["bank"]), inline=True)
        embed.add_field(name="Total", value=self.format_money(data["balance"] + data["bank"]), inline=True)
        if data["job"]:
            embed.add_field(name="Emprego", value=data["job"].title(), inline=False)
        if is_vip_user:
            embed.add_field(name="👑 Status", value="VIP ATIVO - Bônus em todas atividades!", inline=False)
        await ctx.send(embed=embed)

    @commands.command(name='diario', aliases=['daily'])
    async def daily(self, ctx):
        data = await self.get_user_data(ctx.author.id)
        now = datetime.now()
        multipliers = await self.get_vip_multipliers(ctx.author.id, ctx.guild.id)
        
        if data["last_daily"]:
            last = datetime.fromisoformat(data["last_daily"])
            if now - last < timedelta(days=1):
                left = timedelta(days=1) - (now - last)
                h, m = int(left.total_seconds() // 3600), int((left.total_seconds() % 3600) // 60)
                return await ctx.send(embed=discord.Embed(title="⏰ Cooldown", description=f"Volte em {h}h {m}m", color=0xff0000))
        
        reward = int(self.daily_reward * multipliers["daily"])
        success = await self.update_user_data(ctx.author.id, {"balance": data["balance"] + reward, "last_daily": now.isoformat()})
        
        if success:
            is_vip = multipliers["daily"] > 1.0
            embed = discord.Embed(title="🎁 Recompensa Diária", description=f"Você recebeu {self.format_money(reward)}!", color=0xFFD700 if is_vip else 0x00ff00)
            if is_vip:
                embed.add_field(name="👑 Bônus VIP", value="2x recompensa aplicada!", inline=False)
            await ctx.send(embed=embed)

    @commands.command(name='trabalhar', aliases=['work'])
    async def work(self, ctx):
        data = await self.get_user_data(ctx.author.id)
        now = datetime.now()
        multipliers = await self.get_vip_multipliers(ctx.author.id, ctx.guild.id)
        
        if not data["job"]:
            job = random.choice(list(self.jobs.keys()))
            await self.update_user_data(ctx.author.id, {"job": job})
            data["job"] = job
            return await ctx.send(embed=discord.Embed(title="💼 Novo Emprego", description=f"Você conseguiu trabalho como {job}!", color=0x00ff00))
        
        if data["last_work"]:
            last = datetime.fromisoformat(data["last_work"])
            if now - last < timedelta(seconds=self.work_cooldown):
                left = timedelta(seconds=self.work_cooldown) - (now - last)
                m = int(left.total_seconds() // 60)
                return await ctx.send(embed=discord.Embed(title="⏰ Cooldown", description=f"Volte em {m} min", color=0xff0000))
        
        job = data["job"]
        min_sal, max_sal = self.jobs[job]["salary"]
        earnings = int(random.randint(min_sal, max_sal) * multipliers["work"])
        
        success = await self.update_user_data(ctx.author.id, {"balance": data["balance"] + earnings, "last_work": now.isoformat()})
        if success:
            is_vip = multipliers["work"] > 1.0
            embed = discord.Embed(title="💼 Trabalho Concluído", description=f"Trabalhou como {job} e ganhou {self.format_money(earnings)}!", color=0xFFD700 if is_vip else 0x00ff00)
            if is_vip:
                embed.add_field(name="👑 Bônus VIP", value="50% extra aplicado!", inline=False)
            await ctx.send(embed=embed)

    @commands.command(name='crime')
    async def crime(self, ctx):
        data = await self.get_user_data(ctx.author.id)
        now = datetime.now()
        multipliers = await self.get_vip_multipliers(ctx.author.id, ctx.guild.id)
        
        if data["last_crime"]:
            last = datetime.fromisoformat(data["last_crime"])
            if now - last < timedelta(seconds=self.crime_cooldown):
                left = timedelta(seconds=self.crime_cooldown) - (now - last)
                h = int(left.total_seconds() // 3600)
                return await ctx.send(embed=discord.Embed(title="⏰ Cooldown", description=f"Volte em {h}h", color=0xff0000))
        
        crime = random.choice(list(self.crimes.keys()))
        crime_data = self.crimes[crime]
        success_rate = crime_data["success"] + multipliers["crime_success"]
        
        if random.randint(1, 100) <= success_rate:
            reward = random.randint(crime_data["min"], crime_data["max"])
            success = await self.update_user_data(ctx.author.id, {"balance": data["balance"] + reward, "last_crime": now.isoformat()})
            if success:
                is_vip = multipliers["crime_success"] > 0
                embed = discord.Embed(title="🎭 Crime Bem-sucedido", description=f"Você conseguiu {self.format_money(reward)} com {crime.replace('_', ' ')}!", color=0x00ff00)
                if is_vip:
                    embed.add_field(name="👑 Bônus VIP", value="+15% chance de sucesso!", inline=False)
        else:
            fine = random.randint(100, 500)
            new_balance = max(0, data["balance"] - fine)
            success = await self.update_user_data(ctx.author.id, {"balance": new_balance, "last_crime": now.isoformat()})
            if success:
                embed = discord.Embed(title="🚔 Crime Fracassou", description=f"Você foi pego e pagou {self.format_money(fine)} de multa!", color=0xff0000)
        
        await ctx.send(embed=embed)

    @commands.command(name='roubar', aliases=['rob'])
    async def rob(self, ctx, user: discord.Member):
        if user == ctx.author:
            return await ctx.send("❌ Você não pode roubar a si mesmo!")
        
        robber_data = await self.get_user_data(ctx.author.id)
        victim_data = await self.get_user_data(user.id)
        multipliers = await self.get_vip_multipliers(ctx.author.id, ctx.guild.id)
        
        if victim_data["balance"] < 100:
            return await ctx.send("❌ Esta pessoa é muito pobre para ser roubada!")
        
        success_rate = 40 + multipliers["rob_success"]
        
        if random.randint(1, 100) <= success_rate:
            stolen = min(victim_data["balance"] // 4, 5000)
            await self.update_user_data(ctx.author.id, {"balance": robber_data["balance"] + stolen})
            await self.update_user_data(user.id, {"balance": victim_data["balance"] - stolen})
            is_vip = multipliers["rob_success"] > 0
            embed = discord.Embed(title="💰 Roubo Bem-sucedido", description=f"Você roubou {self.format_money(stolen)} de {user.display_name}!", color=0x00ff00)
            if is_vip:
                embed.add_field(name="👑 Bônus VIP", value="+20% chance de sucesso!", inline=False)
        else:
            fine = random.randint(200, 800)
            new_balance = max(0, robber_data["balance"] - fine)
            await self.update_user_data(ctx.author.id, {"balance": new_balance})
            embed = discord.Embed(title="🚔 Roubo Fracassou", description=f"Você foi pego e pagou {self.format_money(fine)}!", color=0xff0000)
        
        await ctx.send(embed=embed)

    @commands.command(name='apostar', aliases=['bet'])
    async def bet(self, ctx, amount: int):
        data = await self.get_user_data(ctx.author.id)
        multipliers = await self.get_vip_multipliers(ctx.author.id, ctx.guild.id)
        
        if amount <= 0 or amount > data["balance"]:
            return await ctx.send("❌ Valor inválido ou saldo insuficiente!")
        
        win_chance = 45 + multipliers["bet_luck"]
        
        if random.randint(1, 100) <= win_chance:
            winnings = amount * 2
            new_balance = data["balance"] + amount
            is_vip = multipliers["bet_luck"] > 0
            embed = discord.Embed(title="🎰 Você Ganhou!", description=f"Ganhou {self.format_money(winnings)}!", color=0x00ff00)
            if is_vip:
                embed.add_field(name="👑 Bônus VIP", value="+10% chance de vitória!", inline=False)
        else:
            new_balance = data["balance"] - amount
            embed = discord.Embed(title="🎰 Você Perdeu!", description=f"Perdeu {self.format_money(amount)}!", color=0xff0000)
        
        await self.update_user_data(ctx.author.id, {"balance": new_balance})
        await ctx.send(embed=embed)

    @commands.command(name='inventario', aliases=['inv'])
    async def inventory(self, ctx, user: discord.Member = None):
        if user is None:
            user = ctx.author
        data = await self.get_user_data(user.id)
        inv = data.get("inventory", {})
        
        embed = discord.Embed(title=f"🎒 Inventário de {user.display_name}", color=0x0099ff)
        if inv:
            for item, qty in inv.items():
                embed.add_field(name=item.title(), value=f"Quantidade: {qty}", inline=True)
        else:
            embed.description = "Inventário vazio"
        await ctx.send(embed=embed)

    @commands.command(name='depositar', aliases=['dep'])
    async def deposit(self, ctx, amount: str):
        data = await self.get_user_data(ctx.author.id)
        
        if amount.lower() == "all":
            amount = data["balance"]
        else:
            try:
                amount = int(amount)
            except:
                return await ctx.send("❌ Valor inválido!")
        
        if amount <= 0 or amount > data["balance"]:
            return await ctx.send("❌ Valor inválido ou saldo insuficiente!")
        
        success = await self.update_user_data(ctx.author.id, {"balance": data["balance"] - amount, "bank": data["bank"] + amount})
        if success:
            await ctx.send(embed=discord.Embed(title="🏦 Depósito", description=f"Depositado {self.format_money(amount)}!", color=0x00ff00))

    @commands.command(name='sacar', aliases=['withdraw'])
    async def withdraw(self, ctx, amount: str):
        data = await self.get_user_data(ctx.author.id)
        
        if amount.lower() == "all":
            amount = data["bank"]
        else:
            try:
                amount = int(amount)
            except:
                return await ctx.send("❌ Valor inválido!")
        
        if amount <= 0 or amount > data["bank"]:
            return await ctx.send("❌ Valor inválido ou saldo bancário insuficiente!")
        
        success = await self.update_user_data(ctx.author.id, {"balance": data["balance"] + amount, "bank": data["bank"] - amount})
        if success:
            await ctx.send(embed=discord.Embed(title="🏦 Saque", description=f"Sacado {self.format_money(amount)}!", color=0x00ff00))

    @commands.command(name='loja', aliases=['shop'])
    async def shop(self, ctx):
        try:
            shop_data = {}
            if await self.ensure_connection():
                async for item in self.shop_collection.find():
                    shop_data[item["item"]] = {"price": item["price"], "desc": item["desc"]}
            
            embed = discord.Embed(title="🛒 Loja", color=0x0099ff)
            for item, data in shop_data.items():
                embed.add_field(name=item.title(), value=f"{data['desc']}\n{self.format_money(data['price'])}", inline=True)
            embed.set_footer(text="Use !comprar <item>")
            await ctx.send(embed=embed)
        except:
            await ctx.send("❌ Erro ao carregar loja")

    @commands.command(name='comprar', aliases=['buy'])
    async def buy(self, ctx, *, item_name: str):
        data = await self.get_user_data(ctx.author.id)
        item_name = item_name.lower()
        
        try:
            shop_item = await self.shop_collection.find_one({"item": item_name})
            if not shop_item:
                return await ctx.send("❌ Item não encontrado!")
            
            price = shop_item["price"]
            if data["balance"] < price:
                return await ctx.send("❌ Saldo insuficiente!")
            
            inv = data.get("inventory", {})
            inv[item_name] = inv.get(item_name, 0) + 1
            
            success = await self.update_user_data(ctx.author.id, {"balance": data["balance"] - price, "inventory": inv})
            if success:
                await ctx.send(embed=discord.Embed(title="🛒 Compra Realizada", description=f"Comprou {item_name} por {self.format_money(price)}!", color=0x00ff00))
        except:
            await ctx.send("❌ Erro na compra")

    @commands.command(name='vantagens', aliases=['vipinfo'])
    async def vip_benefits(self, ctx):
        """Mostra as vantagens VIP"""
        embed = discord.Embed(title="👑 Vantagens VIP", description="Benefícios exclusivos para membros VIP:", color=0xFFD700)
        embed.add_field(name="💰 Recompensa Diária", value="**2x** mais dinheiro", inline=True)
        embed.add_field(name="💼 Trabalho", value="**50%** mais salário", inline=True)
        embed.add_field(name="🎭 Crime", value="**+15%** chance sucesso", inline=True)
        embed.add_field(name="💰 Roubo", value="**+20%** chance sucesso", inline=True)
        embed.add_field(name="🎰 Apostas", value="**+10%** chance vitória", inline=True)
        embed.add_field(name="👑 Status", value="Badge VIP exclusivo", inline=True)
        embed.set_footer(text="Adquira VIP com um administrador!")
        await ctx.send(embed=embed)

    @commands.has_permissions(administrator=True)
    @commands.command(name='dar', aliases=['give'])
    async def give_money(self, ctx, user: discord.Member, amount: int):
        data = await self.get_user_data(user.id)
        success = await self.update_user_data(user.id, {"balance": data["balance"] + amount})
        
        if success:
            embed = discord.Embed(title="💰 Dinheiro Dado", description=f"Você deu {self.format_money(amount)} para {user.display_name}!", color=0x00ff00)
            await ctx.send(embed=embed)

    async def cog_unload(self):
        if self.client:
            self.client.close()

async def setup(bot):
    await bot.add_cog(Economia(bot))