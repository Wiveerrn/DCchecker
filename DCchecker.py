import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GUILD_ID_RAW = os.getenv("DISCORD_GUILD_ID")
API_URL = os.getenv("DC_API_URL")

if not TOKEN:
    raise RuntimeError("環境変数 DISCORD_BOT_TOKEN が未設定です。")

if not GUILD_ID_RAW:
    raise RuntimeError("環境変数 DISCORD_GUILD_ID が未設定です。")

if not API_URL:
    raise RuntimeError("環境変数 DC_API_URL が未設定です。")

GUILD_ID = int(GUILD_ID_RAW)

class WaitingwayBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=commands.when_mentioned, intents=discord.Intents.default())

    async def setup_hook(self):
        guild = discord.Object(id=GUILD_ID)
        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)
        print("Botが起動し、スラッシュコマンドを同期しました！")

bot = WaitingwayBot()

@bot.tree.command(name="dctravel", description="現在のDC Travelの可否状況を可視化します")
@app_commands.describe(dc_name="確認したいDC名 (例: Mana, Elemental, Gaia, Meteor, Aether)")
async def dctravel(interaction: discord.Interaction, dc_name: str = "Mana"):
    # 処理に少し時間がかかる可能性があるため、Discord側に待機状態を伝える
    await interaction.response.defer()

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(API_URL) as response:
                if response.status != 200:
                    await interaction.followup.send(f"⚠️ データを取得できませんでした (Status: {response.status})")
                    return
                
                data = await response.json()
                
                # JSONから各リストを取得
                datacenters = data.get("datacenters", [])
                worlds = data.get("worlds", [])

                # 1. ユーザーが入力したDC名から、DCのIDを特定する
                target_dc = next((dc for dc in datacenters if dc["name"].lower() == dc_name.lower()), None)

                if not target_dc:
                    await interaction.followup.send(
                        f"⚠️ `{dc_name}` というデータセンターが見つかりませんでした。\n"
                        "正しい名前（例: Mana, Gaia, Aether）を入力してください。"
                    )
                    return

                dc_id = target_dc["id"]
                dc_proper_name = target_dc["name"] # 大文字小文字が正しい正式名称

                # 2. 該当するDCのIDを持つワールド（サーバー）を抽出
                target_worlds = [w for w in worlds if w.get("datacenter_id") == dc_id]
                
                # 見栄えを良くするため、ワールド名をアルファベット順にソート
                target_worlds.sort(key=lambda x: x.get("name", ""))

                # 3. Discord上で可視化 (Embedの作成)
                embed = discord.Embed(
                    title=f"🌐 {dc_proper_name} データセンター トラベル状況",
                    color=discord.Color.blue()
                )

                for world in target_worlds:
                    world_name = world.get("name", "不明")
                    
                    # travel_prohibited（トラベル禁止フラグ）を確認
                    # False（禁止されていない）なら受け入れ可、Trueなら停止中
                    is_prohibited = world.get("travel_prohibited", True)

                    if not is_prohibited:
                        value = "🟢 受け入れ可"
                    else:
                        value = "🔴 停止中"

                    # サーバーを横並びに表示
                    embed.add_field(name=world_name, value=value, inline=True)

                # 平均移動時間（average_travel_time）があればフッターに表示
                avg_time = data.get("average_travel_time")
                footer_text = "Data provided by Waitingway"
                if avg_time is not None:
                    footer_text += f" | 全体平均移動時間: 約{avg_time}分"
                embed.set_footer(text=footer_text)
                
                # 4. メッセージを送信
                await interaction.followup.send(embed=embed)

        except Exception as e:
            await interaction.followup.send(f"⚠️ エラーが発生しました: `{e}`")

if __name__ == "__main__":
    bot.run(TOKEN)