# ≪参照設定≫
import multiprocessing
import threading
import asyncio
import discord
from discord.ext import commands, tasks
from urllib import parse
from urllib import request
from common import bot
from discord.voice_client import VoiceClient
import yt_dlp as youtube_dl
from bs4 import BeautifulSoup
import json
import random
import requests
import re
from discord.utils import get
import time




# インスタンス化
queue = []
queue2 = []
loop_enabled = False  # LOOPのON/OFFを管理する変数

class MusicCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

# ≪YoutubeDLに関する設定≫


youtube_dl.utils.bug_reports_message = lambda: ''
ytdl_format_options = {
    'format': 'bestaudio',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': False,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '256',
    }],
}


ffmpeg_options = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn -b:a 256k'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)


class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.01):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')

    def get_title(self):
        return self.title

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=True):
        loop = loop or asyncio.get_event_loop()
        try:
            data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
            if 'entries' in data:
                data = data['entries'][0]
            filename = data['url'] if stream else ytdl.prepare_filename(data)
            return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)
        except youtube_dl.DownloadError as e:
            raise youtube_dl.DownloadError(f"Failed to download audio: {str(e)}")



# ---------------------------------------------------------------------------------------------------------------

# ≪音楽再生機能≫

# 再生
@bot.command()
async def p(ctx, *, search):
    query_string = parse.urlencode({'search_query': search})
    html_content = request.urlopen(
        'http://www.youtube.com/results?' + query_string)
    search_results = re.findall(
        'watch\?v=(.{11})', html_content.read().decode('utf-8'))
    
    if not search_results:
        await ctx.send("検索結果が見つかりませんでした。")
        return


    url = 'https://www.youtube.com/watch?v=' + search_results[0]
    await ctx.send('https://www.youtube.com/watch?v=' + search_results[0])
    await join(ctx)
    await queue_(ctx, url)
    await play(ctx)
    


@bot.command(pass_context=True)
async def play(ctx):
    global queue, queue2
    print(queue)
    
    if not ctx.message.author.voice:
        await ctx.send("VCに入ってね♪")
        return

    if len(queue) == 0:
        await ctx.send('曲を追加してね!')
        return

    try:
        channel = ctx.message.author.voice.channel
        await channel.connect()
    except:
        pass

    server = ctx.message.guild
    voice_channel = server.voice_client
    
    while queue:
        try:
            while voice_channel.is_playing() or voice_channel.is_paused():
                await asyncio.sleep(2)
        except AttributeError:
            pass

        try:
            async with ctx.typing():
                player = await YTDLSource.from_url(queue[0], loop=bot.loop)
                voice_channel.play(player, after=lambda e: print(
                    'Player error: %s' % e) if e else None)

                queue2.append(queue[0])  # 再生が終わった曲を queue2 に追加
                del queue[0]
                
            await ctx.send('**再生中♪:** {}'.format(player.title))
            
            # ループが有効で再生キューが空の場合、queue2 の曲を再生キューに追加して再生を再開
            if loop_enabled and len(queue) == 0 and len(queue2) > 0:
                queue.extend(queue2)
                queue2.clear()
                
        except Exception as e:
            print(f"An error occurred during playback: {e}")
            break  # エラーが発生したらループを終了する


@bot.command()
async def loop(ctx):
    global loop_enabled, queue, queue2

    if not ctx.voice_client:
        await ctx.send("ボイスチャンネルに接続していません。")
        return

    loop_enabled = not loop_enabled 
    if loop_enabled:
        await ctx.send("ループが有効になりました.")
        
    else:
        await ctx.send("ループが無効になりました.")



    

# BotのVC招待
@bot.command(pass_context=True)
async def join(ctx):
    canal = ctx.message.author.voice.channel
    voz = get(bot.voice_clients, guild=ctx.guild)
    if voz and voz.is_connected():
        await ctx.send("ボットはすでに音声チャンネルに接続しています。")
        return
    if voz and voz.is_playing():
        voz.stop()
    await canal.connect()


# BotのVC切断
@bot.command(pass_context=True)
async def exit(ctx):
    canal = ctx.message.author.voice.channel
    voz = get(bot.voice_clients, guild=ctx.guild)
    await voz.disconnect()
    await clear_queue(ctx)

# キューのクリア
@bot.command()
async def clear_queue(ctx):
    global queue, queue2
    if queue or queue2:
        queue.clear()
        queue2.clear()
        print(f"キューがクリアされました。Guild: {ctx.guild.name}")


# リストを表示
@bot.command(aliases=['list_queue', 'll'])
async def list_current_queue(ctx):
    global queue, queue2

    await ctx.send('現在のキュー:')
    index = 1
    
    if queue:
        for url in queue:
            source = await YTDLSource.from_url(url)
            title = source.get_title()
            await ctx.send(f"1-{index}. {title}")
            index += 1

    if queue2:
        for url in queue2:
            source = await YTDLSource.from_url(url)
            title = source.get_title()
            await ctx.send(f"2-{index}. {title}")
            index += 1



# リストに追加
@bot.command(aliases=['q'])
async def queue_(ctx, url):
    global queue

    queue.append(url)
    await ctx.send(f'`{url}` が再生リストに追加されたよ!')

    # ボットがボイスチャンネルに接続している場合、音声再生中でない場合に再生をトリガー
    if ctx.voice_client and not ctx.voice_client.is_playing() and len(queue) == 1:
        await play(ctx)


# リストから削除
@bot.command()
async def remove(ctx):
    global queue, queue2

    if queue:
        removed_url = queue.pop(0)
        await ctx.send(f'`{removed_url}` が削除されました!')
    if queue2:
        removed_url = queue2.pop(0)
        await ctx.send(f' `{removed_url}` が削除されました!')

    if not queue and not queue2:
        await ctx.send('現在再生中のキューは空です。')


# 一時停止/再開
@bot.command(pass_context=True, aliases=['tp'])
async def toggle_pause(ctx):
    voz = get(bot.voice_clients, guild=ctx.guild)
    
    if voz:
        if voz.is_playing():
            print("楽曲停止")
            voz.pause()
            await ctx.send("停止 Ⅱ")
        elif voz.is_paused():
            print("楽曲再開")
            voz.resume()
            await ctx.send("再開 ▶")
        else:
            print("No se esta Reproduciendo")
            await ctx.send("曲を追加しよう!")

    


    else:
        print("No se encuentra en un canal de voz")
        await ctx.send("VCに招待してね!")


# 音量設定
@bot.command(aliases=['vol'])
async def volume(ctx, volume: int = None):
    if ctx.voice_client is None:
        return await ctx.send("ボイスチャンネルに接続していません。")

    if volume is None:
        current_volume = int(ctx.voice_client.source.volume * 100)
        await ctx.send(f"現在のボリュームは{current_volume}%です。")
    else:
        ctx.voice_client.source.volume = volume / 100
        await ctx.send(f"音量を{volume}%に設定しました。")


# 次曲へ
@bot.command(aliases=['n'])
async def next(ctx):
    voz = get(bot.voice_clients, guild=ctx.guild)

    if not voz.is_playing():
        raise NoMoreTracks

    voz.stop()
    await ctx.send("次➡")


# キューをシャッフル
@bot.command(aliases=['shuffle_queue', 'sf'])
async def shuffle_current_queue(ctx):
    global queue

    if queue:
        random.shuffle(queue)
        await ctx.send('現在再生中のキューをシャッフルしました!')

# シャッフルされたキューを表示
@bot.command(aliases=['list_shuffled_queue', 'lsq'])
async def list_shuffled_current_queue(ctx):
    global queue

    shuffled_queue = queue.copy()

    random.shuffle(shuffled_queue)

    if not shuffled_queue and not shuffled_queue2:
        await ctx.send('現在のシャッフルされたキューは空です。')
        return

    await ctx.send('現在のシャッフルされたキュー:')
    index = 1

    for url in shuffled_queue1:
        source = await YTDLSource.from_url(url)
        title = source.get_title()
        await ctx.send(f"{index}. {title}")
        index += 1







# プレイリストを管理する辞書
playlists = {}

# プレイリストの再生位置を管理する辞書
playlist_positions = {}

# プレイリスト情報の保存先ファイル
playlist_file = 'playlists.json'



# プレイリストをファイルに保存する関数
async def save_playlists():
    with open(playlist_file, 'w') as file:
        json.dump(playlists, file)

# プレイリストをファイルから読み込む関数
async def load_playlists():
    try:
        with open(playlist_file, 'r') as file:
            data = json.load(file)
            playlists.update(data)
    except FileNotFoundError:
        pass




# プレイリストの作成
@bot.command(aliases=['cp'])
async def create_playlists(ctx, playlist_name):
    if playlist_name not in playlists:
        playlists[playlist_name] = []
        await ctx.send(f'新しいプレイリストを作成しました: {playlist_name}')
        await save_playlists()  # プレイリストを作成した後に保存
    else:
        await ctx.send('すでに存在するプレイリストです.')

# プレイリストにURLを追加する
@bot.command(aliases=['adp'])
async def add_playlists(ctx, playlist_name, url):
    if playlist_name in playlists:
        # URLを追加
        playlists[playlist_name].append(url)
        await ctx.send(f'プレイリストにURLを追加しました: {url}')
        await save_playlists()  # プレイリストを変更した後に保存
    else:
        await ctx.send('指定したプレイリストは存在しません.')

# プレイリストを表示
@bot.command(aliases=['lpm'])
async def look_playlists_music(ctx, playlist_name):
    if playlist_name in playlists:
        await ctx.send(f'プレイリスト: {playlist_name}')
        for index, url in enumerate(playlists[playlist_name], start=1):
            source = await YTDLSource.from_url(url)
            title = source.get_title()  # タイトルを取得
            await ctx.send(f"{index}. {title}")
    else:
        await ctx.send('指定したプレイリストは存在しません.')

# プレイリスト名一覧を表示する
@bot.command(aliases=['lpn'])
async def look_playlists_name(ctx):
    if playlists:
        await ctx.send("利用可能なプレイリスト一覧:")
        for playlist_name in playlists.keys():
            await ctx.send(f'》 {playlist_name}')
    else:
        await ctx.send("プレイリストが存在しません。")


# プレイリストを再生するコマンド
@bot.command(aliases=['pp'])
async def play_playlists(ctx, playlist_name):
    if playlist_name in playlists:
            
        # プレイリストからURLリストを取得
        playlist_urls = playlists[playlist_name]

        if not playlist_urls:
            await ctx.send('プレイリストに曲がありません。')
            return

        # プレイリスト内のすべての曲をキューに追加
        for url in playlist_urls:
            if url:
                await queue_(ctx, url)

        # 最初の曲を再生（キューに追加された曲が自動的に再生されます）
        await play(ctx)
        
    else:
        await ctx.send('指定したプレイリストは存在しません。')


# プレイリストを削除する
@bot.command(aliases=['dp'])
async def delete_playlists(ctx, playlist_name):
    if playlist_name in playlists:
        del playlists[playlist_name]
        await ctx.send(f'プレイリストを削除しました: {playlist_name}')
        await save_playlists()  # プレイリストを削除した後に保存
    else:
        await ctx.send('指定したプレイリストは存在しません.')


# プレイリストから楽曲を削除する
@bot.command(aliases=['rp'])
async def remove_from_playlists(ctx, playlist_name, index):
    if playlist_name in playlists:
        try:
            index = int(index)
            if 1 <= index <= len(playlists[playlist_name]):
                removed_url = playlists[playlist_name].pop(index - 1)
                await ctx.send(f'プレイリストから楽曲を削除しました: {removed_url}')
                await save_playlists()  # プレイリストを変更した後に保存
            else:
                await ctx.send('無効な楽曲インデックスです。')
        except ValueError:
            await ctx.send('楽曲インデックスは整数で指定してください。')
    else:
        await ctx.send('指定したプレイリストは存在しません.')




def setup(bot):
    bot.add_cog(MusicCog(bot))