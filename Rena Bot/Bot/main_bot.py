# ≪参照設定≫
import multiprocessing
import threading
import asyncio
import discord
from discord.ext import commands, tasks
from common import bot
import json
from cogs import music, tools
import random

# ≪インスタンス≫

status = ['♬']
queue = []  # キュー1の初期化
queue2 = []  # キュー2の初期化


# モジュールを追加
bot.add_cog(music.MusicCog(bot))
bot.add_cog(tools.ToolsCog(bot))


# =======================================================================================================================

# ≪インフォメーション≫



# レイテンシの確認
@bot.command()
async def ping(ctx):
    await ctx.send(f'**Pong!** Latency: {round(bot.latency * 1000)}ms')


# 挨拶（こんにちは）
@bot.command()
async def hello(ctx):
    author = ctx.message.author
    await ctx.send(f'{author.mention}さん、こんにちは!')



# ===========================================================================================================================



# 起動完了ログ
@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Game(random.choice(status)))
    await music.load_playlists()  # music.pyのload_playlists関数を呼び出す
    print('{- 神堂 零奈 -}準備が整いました')
    print("VC監視を開始します。")
    await check_vc_state.start() 


@tasks.loop(seconds=2)
async def check_vc_state():
    global queue, queue2

    for guild in bot.guilds:
        voice_client = guild.voice_client
        if voice_client is None:
            # ボットがVCに接続していない場合
            if queue or queue2:  # キューが空でない場合
                queue.clear()  # キュー1をクリア
                queue2.clear()  # キュー2をクリア
                print(f"キューがクリアされました。Guild: {guild.name}")

# check_vc_state をループで実行する間隔を設定
@check_vc_state.before_loop
async def before_check_vc_state():
    await bot.wait_until_ready()





# サーバー参加者へのDM挨拶
@bot.event
async def on_member_join(member):
    await member.create_dm()
    await member.dm_channel.send(
        f'{member.name}さん、サーバーに入ってくれてありがとう!  何か気になることや、トラブルがあったらサーバー代表≪Xzh≫までDMしてね。      ※これはサーバー代表が構築したBotです。'
    )





# ≪Bot起動トークン≫
bot.run('TOKEN')