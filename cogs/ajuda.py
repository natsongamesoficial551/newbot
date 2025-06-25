import discord
from discord.ext import commands

class Ajuda(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
        # Dicionário com todas as categorias e seus comandos
        self.categorias = {
            "aniversario": {
                "emoji": "🎉",
                "nome": "Aniversário",
                "comandos": {
                    "🛠️ **Configuração:**": [
                        "`!configurarcanal`, `!setbdchannel` - Define canal de aniversários",
                        "`!testeaniversario`, `!testbd` - Testa mensagem de aniversário",
                        "`!statuscanal`, `!bdchannelinfo` - Mostra status do canal"
                    ],
                    "🗂️ **Gerenciamento:**": [
                        "`!adicionardata <DD/MM>`, `!addbd <DD/MM>` - Adiciona seu aniversário",
                        "`!removeraniversario`, `!rmbd` - Remove seu aniversário"
                    ],
                    "🔍 **Consulta:**": [
                        "`!aniversariantes`, `!bds` - Lista todos os aniversários",
                        "`!meuaniversario`, `!mybd` - Mostra seu aniversário",
                        "`!proximosaniversarios`, `!nextbds` - Próximos aniversários",
                        "`!aniversariohoje`, `!bdtoday` - Aniversários de hoje"
                    ]
                }
            },
            "antipalavrao": {
                "emoji": "🛡️",
                "nome": "Antipalavrão",
                "comandos": {
                    "🚫 **Filtro de Palavrões:**": [
                        "`!adicionarpalavrao <palavra>` - Adiciona palavra à lista",
                        "`!removerpalavrao <palavra>` - Remove palavra da lista",
                        "`!palavroes` - Mostra lista de palavrões",
                        "`!togglefiltro` - Liga/desliga o filtro"
                    ]
                }
            },
            "sorteios": {
                "emoji": "🎁",
                "nome": "Sorteios",
                "comandos": {
                    "🎲 **Gerenciar Sorteios:**": [
                        "`!comecarsorteio <premio>` - Inicia um sorteio",
                        "`!vencedor` - Sorteia um vencedor",
                        "`!encerrarsorteio` - Encerra o sorteio atual",
                        "`!canaldecomando #canal` - Define canal de comandos",
                        "`!canaldosorteio #canal` - Define canal do sorteio"
                    ]
                }
            },
            "xp": {
                "emoji": "📈",
                "nome": "Sistema XP",
                "comandos": {
                    "⚙️ **Configuração XP:**": [
                        "`!mensagemporxp <min> <max>` - XP por mensagem",
                        "`!basexp <valor>` - XP base para subir de nível",
                        "`!adicionarxppornivel <valor>` - XP adicional por nível",
                        "`!tempodexp <normal> [vip]` - Tempo entre ganhos de XP",
                        "`!configxp` - Mostra configurações atuais"
                    ]
                }
            },
            "vip": {
                "emoji": "💎",
                "nome": "Sistema VIP",
                "comandos": {
                    "👑 **Gerenciar VIP:**": [
                        "`!vip @user dias` - Adiciona VIP a usuário",
                        "`!removervip @user` - Remove VIP de usuário",
                        "`!configvip` - Configurações VIP",
                        "`!cargovip <ID>` - Define cargo VIP",
                        "`!listvip` - Lista usuários VIP",
                        "`!checkvip [@user]` - Verifica status VIP"
                    ]
                }
            },
            "moderacao": {
                "emoji": "🔨",
                "nome": "Moderação",
                "comandos": {
                    "⚖️ **Punições:**": [
                        "`!aviso @user [motivo]` - Aplica aviso",
                        "`!removeraviso @user [número]` - Remove aviso",
                        "`!avisos [@user]` - Lista avisos",
                        "`!mutar @user tempo [motivo]` - Muta usuário",
                        "`!desmutar @user` - Desmuta usuário"
                    ],
                    "🚫 **Ações Severas:**": [
                        "`!banir @user` - Bane usuário",
                        "`!expulsar @user` - Expulsa usuário",
                        "`!limparmensagem [quantidade]` - Limpa mensagens",
                        "`!configmod` - Configurações de moderação"
                    ]
                }
            },
            "boasvindas": {
                "emoji": "👋",
                "nome": "Boas-Vindas",
                "comandos": {
                    "🚪 **Configurar Mensagens:**": [
                        "`!canalconfig #canal` - Canal de configuração",
                        "`!canalentrada #canal` - Canal de entrada",
                        "`!canalsaida #canal` - Canal de saída",
                        "`!msgentrada mensagem` - Mensagem de entrada",
                        "`!msgsaida mensagem` - Mensagem de saída"
                    ],
                    "🧪 **Testes:**": [
                        "`!configmsg` - Ver configurações",
                        "`!testentrada` - Testar entrada",
                        "`!testsaida` - Testar saída"
                    ]
                }
            },
            "economia": {
                "emoji": "💰",
                "nome": "Economia",
                "comandos": {
                    "💵 **Básico:**": [
                        "`!saldo`, `!bal` - Ver saldo",
                        "`!diario`, `!daily` - Bônus diário",
                        "`!inventario`, `!inv` - Ver inventário",
                        "`!depositar`, `!dep` - Depositar no banco",
                        "`!sacar`, `!withdraw` - Sacar do banco"
                    ],
                    "💼 **Trabalho:**": [
                        "`!trabalhar`, `!work` - Trabalhar",
                        "`!empregos`, `!jobs` - Ver empregos",
                        "`!contratar`, `!hire` - Contratar funcionário",
                        "`!demitir`, `!fire` - Demitir funcionário"
                    ],
                    "🛒 **Loja:**": [
                        "`!loja`, `!shop` - Ver loja",
                        "`!comprar`, `!buy` - Comprar item",
                        "`!vender`, `!sell` - Vender item"
                    ],
                    "🎰 **Riscos:**": [
                        "`!crime` - Cometer crime",
                        "`!roubar`, `!rob` - Roubar usuário",
                        "`!apostar`, `!bet` - Apostar dinheiro"
                    ]
                }
            },
            "diversao": {
                "emoji": "🎮",
                "nome": "Diversão",
                "comandos": {
                    "🎲 **Jogos:**": [
                        "`!dado [lados]` - Rolar dado",
                        "`!moeda` - Cara ou coroa",
                        "`!rps <pedra/papel/tesoura>` - Pedra, papel, tesoura",
                        "`!8ball <pergunta>` - Bola 8 mágica"
                    ],
                    "😄 **Entretenimento:**": [
                        "`!piada` - Piada aleatória",
                        "`!curiosidade` - Curiosidade",
                        "`!pergunta` - Pergunta aleatória",
                        "`!escolher <opções>` - Escolher opção",
                        "`!love @user1 @user2` - Compatibilidade",
                        "`!motivar [@usuário]` - Frase motivacional"
                    ]
                }
            },
            "utilidades": {
                "emoji": "🔧",
                "nome": "Utilidades",
                "comandos": {
                    "ℹ️ **Informações:**": [
                        "`!botinfo` - Info do bot",
                        "`!userinfo` - Info do usuário",
                        "`!serverinfo` - Info do servidor",
                        "`!ping` - Latência do bot",
                        "`!uptime` - Tempo online"
                    ],
                    "🖼️ **Perfil:**": [
                        "`!avatar` - Avatar do usuário",
                        "`!banner` - Banner do usuário",
                        "`!membercount` - Contador de membros"
                    ]
                }
            }
        }

    @commands.command(name="cmds", aliases=["comandos", "categorias"])
    async def listar_categorias(self, ctx):
        """Lista todas as categorias disponíveis"""
        embed = discord.Embed(
            title="📚 Categorias de Comandos",
            description="Use `!ajuda <categoria>` para ver os comandos específicos\n"
                       "Exemplo: `!ajuda economia`",
            color=discord.Color.gold()
        )
        
        categorias_texto = ""
        for key, categoria in self.categorias.items():
            categorias_texto += f"{categoria['emoji']} **{categoria['nome']}** - `{key}`\n"
        
        embed.add_field(
            name="📋 Categorias Disponíveis:",
            value=categorias_texto,
            inline=False
        )
        
        embed.add_field(
            name="💡 Outros Comandos:",
            value="🎭 `roleplay` - Comandos de roleplay\n"
                  "📜 `logs` - Sistema de logs\n"
                  "🎫 `tickets` - Sistema de tickets\n"
                  "📡 `status` - Configurar status do bot",
            inline=False
        )
        
        embed.set_footer(text="💡 Use !ajuda <categoria> para ver comandos específicos")
        await ctx.send(embed=embed)

    @commands.command(name="ajuda", aliases=["help"])
    async def ajuda_categoria(self, ctx, categoria: str = None):
        """Mostra comandos de uma categoria específica ou todas"""
        
        if not categoria:
            # Se não especificar categoria, mostra o menu principal
            await self.listar_categorias(ctx)
            return
        
        categoria = categoria.lower()
        
        # Categorias especiais que não estão no dicionário principal
        if categoria in ["roleplay", "rp"]:
            await self.ajuda_roleplay(ctx)
            return
        elif categoria in ["logs", "log"]:
            await self.ajuda_logs(ctx)
            return
        elif categoria in ["tickets", "ticket"]:
            await self.ajuda_tickets(ctx)
            return
        elif categoria in ["status"]:
            await self.ajuda_status(ctx)
            return
        
        # Verifica se a categoria existe
        if categoria not in self.categorias:
            embed = discord.Embed(
                title="❌ Categoria não encontrada",
                description=f"A categoria `{categoria}` não existe.\n"
                           f"Use `!cmds` para ver todas as categorias disponíveis.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        # Mostra comandos da categoria
        cat_info = self.categorias[categoria]
        embed = discord.Embed(
            title=f"{cat_info['emoji']} {cat_info['nome']}",
            description=f"Comandos da categoria **{cat_info['nome']}**",
            color=discord.Color.blue()
        )
        
        for secao, comandos in cat_info['comandos'].items():
            comandos_texto = "\n".join(comandos)
            embed.add_field(
                name=secao,
                value=comandos_texto,
                inline=False
            )
        
        embed.set_footer(text="Use !cmds para ver todas as categorias")
        await ctx.send(embed=embed)

    async def ajuda_roleplay(self, ctx):
        """Comandos de roleplay"""
        embed = discord.Embed(
            title="🎭 Roleplay",
            description="Comandos de interação entre usuários",
            color=discord.Color.purple()
        )
        
        embed.add_field(
            name="💕 **Carinhosos:**",
            value="`!abracar @usuário` - Abraçar alguém\n"
                  "`!beijar @usuário` - Beijar alguém\n"
                  "`!cafune @usuário` - Fazer cafuné\n"
                  "`!tocaaqui @usuário` - Toca aqui",
            inline=False
        )
        
        embed.add_field(
            name="😤 **Agressivos:**",
            value="`!bofetada @usuário` - Dar bofetada\n"
                  "`!atacar @usuário` - Atacar alguém",
            inline=False
        )
        
        embed.add_field(
            name="🕺 **Outros:**",
            value="`!dancar @usuário` - Dançar com alguém\n"
                  "`!roleplay` - Ver todos comandos RP",
            inline=False
        )
        
        await ctx.send(embed=embed)

    async def ajuda_logs(self, ctx):
        """Sistema de logs"""
        embed = discord.Embed(
            title="📜 Sistema de Logs",
            description="Configure logs para monitorar atividades",
            color=discord.Color.orange()
        )
        
        embed.add_field(
            name="📝 **Configuração:**",
            value="`!canaldelogs #canal` - Define canal de logs",
            inline=False
        )
        
        await ctx.send(embed=embed)

    async def ajuda_tickets(self, ctx):
        """Sistema de tickets"""
        embed = discord.Embed(
            title="🎫 Sistema de Tickets",
            description="Sistema de suporte com tickets",
            color=discord.Color.green()
        )
        
        embed.add_field(
            name="🎫 **Gerenciar Tickets:**",
            value="`!ticket` - Criar novo ticket\n"
                  "`!fecharticket` - Fechar ticket atual\n"
                  "`!adicionarcategoriaticket ID` - Adicionar categoria\n"
                  "`!canaldecomandoticket #canal` - Canal de comandos\n"
                  "`!configticket` - Ver configurações",
            inline=False
        )
        
        await ctx.send(embed=embed)

    async def ajuda_status(self, ctx):
        """Sistema de status do bot"""
        embed = discord.Embed(
            title="📡 Status do Bot",
            description="Configure o status e atividade do bot",
            color=discord.Color.blurple()
        )
        
        embed.add_field(
            name="🤖 **Configurar Status:**",
            value="`!statusmodo` - Alterar modo do status\n"
                  "`!listarstatus` - Listar status disponíveis\n"
                  "`!statusintervalo <minutos>` - Intervalo de mudança\n"
                  "`!statusmanual` - Definir status manual",
            inline=False
        )
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Ajuda(bot))