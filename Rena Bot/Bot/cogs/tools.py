# ≪参照設定≫
import multiprocessing
import threading
import asyncio
import discord
from discord.ext import commands, tasks
from common import bot
import sympy
import random
import requests
import re
from datetime import datetime
from random import choice


# ≪ツール≫


class ToolsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


# 計算ツール
@bot.command()
async def math(ctx, *, expression):
    try:
        result = sympy.sympify(expression)
        await ctx.send(f'Result: {result}')
    except Exception as e:
        await ctx.send('Invalid expression. Please provide a valid mathematical expression.')



# コイントス
@bot.command(aliases=['cf'])
async def coinflip(ctx):
    if choice(["cara", "cruz"]) == "cara":
        await ctx.send("◎")
    else:
        await ctx.send("✕")


# ランダム数排出
@bot.command()
async def rand(ctx, min_value: int, max_value: int):
    if min_value >= max_value:
        await ctx.send('最小値は最大値未満である必要があります。')
        return
    
    random_value = random.randint(min_value, max_value)
    await ctx.send(f'{random_value}')

def setup(bot):
    bot.add_cog(ToolsCog(bot))