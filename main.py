"""
Lorem Ipsum
Bot Created by Jazhyc
Contains some fun features that rely on a bunch of APIs
Use as you see fit
"""

import discord, asyncio
import time, random
import requests, json
import wikipedia
import urllib.request, re
import dog_api as dog
import csv, time
from youtube_dl import YoutubeDL
import wolframalpha

weatherKey = "65ee9edb7a7e7a3186aea38f8429dc84"
discordKey = "NzQ0MjY3MDI4NDI0Mjk0NTAx.Xzgurw.IS8uNiGjJWke6LAb1QO_CzdCDIo"
weatherUrl = "http://api.openweathermap.org/data/2.5/weather?"
random.seed(time.perf_counter())
WIKI_REQUEST = 'http://en.wikipedia.org/w/api.php?action=query&prop=pageimages&format=json&piprop=original&titles='

options = [
    'Hello',
    'How are you?',
    'Joke',
    'Time',
    'Weather [City]',
    'Ban (User)',
    'Wikipedia [Webpage]',
    'Join',
    'Leave',
    'Play [video]',
    'Rdog (Breed)?',
    'Dogbreeds',
    'Quiz',
    'Wolfram [Query]'
]

def load_jokes(file):
    """Loads jokes from a text file into a list object"""
    joke_file = open(file)
    return joke_file.read().split('\n')

def getWeather(city, channel):
    """Gets Weather Parameters from OpenWeather's API"""
    complete_url = weatherUrl + "appid=" + weatherKey + "&q=" + city
    response = requests.get(complete_url)
    alldata = response.json()

    if alldata['cod'] != '404':
        data = alldata["main"]
        temp = data["temp"] - 273.15
        pressure = data["pressure"]
        humidity = data["humidity"]
        weather = alldata["weather"]
        description = weather[0]["description"].capitalize()
        return f"The Weather Parameters in {city}\nTemperature: {temp:.2f} C\nPressure: {pressure} Pa\nHumidity: {humidity}%\nDescription: {description}"
    else:
        return "Invalid City"

def getSummary(content):
    """A bit Overkill for a single Function"""
    if content == 'Trump':
        message = wikipedia.summary('Circus Clown', sentences=1)
    else:
        try:
            message = wikipedia.summary(content, sentences=3)
            success = True
        except:
            message = 'Query was too Ambiguous, or the Details you are looking for does not exist.'
            success = False
    return message, success

def getVideo(link):
    """Gets Video Player Object and Title from Youtube"""
    YDL_OPTIONS = {'format': 'bestaudio', 'noplaylist':'True'}
    link = '-'.join(link.split())
    search_keyword = re.sub("['\"]",'', link)
    html = urllib.request.urlopen("https://www.youtube.com/results?search_query=" + search_keyword)
    video_ids = re.findall(r"watch\?v=(\S{11})", html.read().decode())
    url = "https://www.youtube.com/watch?v=" + video_ids[0]

    with YoutubeDL(YDL_OPTIONS) as ydl:
        info = ydl.extract_info(url, download=False)
    URL = info['formats'][0]['url']
    title = info['title']
    return URL, title


def main():
    """Brains of the Operation. Works Magically"""
    client = discord.Client()
    wolfclient = wolframalpha.Client('THG7TR-3K77KYVH6V')
    puns = load_jokes('jokes.txt')
    animes = open('anime.csv', encoding='utf-8')
    animelist = list(csv.reader(animes))

    global inquiz, quizzee, mystery, quiztime, warning, start, stop, quizchannel, quizmessage
    inquiz = warning = False
    quizzee = mystery = quizchannel = ''
    quiztime = start = stop = 0

    # Indicator that loading is succesful
    @client.event
    async def on_ready():
        print(f'Logged in as {client.user}')
    
    async def quiz_timer():
        print('quiz_timer loaded')
        await client.wait_until_ready()
        global inquiz, quiztime, quizchannel, mystery, warning, start, quizmessage, quiz_voice
        while not client.is_closed():

            start = time.perf_counter()
            while inquiz:
                end = time.perf_counter()
                quiztime = end - start

                if quiztime > 25 and not warning:
                    await quizmessage.channel.send('Video Stopped\nGive Me your best Guess')
                    quiz_voice.stop()
                    warning = True
            
                if quiztime >= 35:
                    quiztime = 0
                    inquiz = False
                    warning = False
                    quiz_voice.stop()
                    await quizmessage.channel.send(f'That\'s too bad, the anime was {mystery}')
                    quiz_voice.play(discord.FFmpegPCMAudio('Sounds/failure.mp3'))
                    break

                await asyncio.sleep(0.000000001)
            inquiz = False # Just to make sure

            await asyncio.sleep(0.000000001)

    # Listens and responds to messages
    @client.event
    async def on_message(message):

        global inquiz, quizzee, mystery, quiztime, warning, start, stop, quizmessage, quiz_voice
        FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

        if not inquiz:
            quiztime = 0

        # Prevents bot from replying to itself
        if message.author == client.user:
            return

        if message.content.lower() in mystery.lower() and len(message.content) >= 4 and inquiz:
            await message.channel.send(f"Congratulations, the Anime is {mystery}")
            voice_player = message.guild.voice_client
            voice_player.stop()
            voice_player.play(discord.FFmpegPCMAudio('Sounds/success.mp3'))
            inquiz = False
            quizzee = ''
            warning = False
            quiztime = 0

        if message.content.lower().startswith('$join'):
            voice_player = await message.author.voice.channel.connect()
            await message.channel.send('Joined Voice Channel')

        if message.content.lower().startswith('$leave'):
            voice_player = message.guild.voice_client
            await voice_player.disconnect()
            await message.channel.send('Left Voice Channel')
            inquiz = False
        
        if message.content.lower().startswith('$stop'):
            voice_player = message.guild.voice_client

            if voice_player.is_playing():
                voice_player.stop()
                if inquiz:
                    await quizmessage.channel.send(f'Too bad, the anime was {mystery}')
                    inquiz = False
                    warning = False
                    quiztime = 0
                await message.channel.send('Video Stopped')
            else:
                await message.channel.send('I can\'t stop the voices in your head')
        
        if message.content.startswith('$play'):

            if inquiz:
                inquiz = False
                warning = False
                quizzee = ''
                quiztime = 0
                await quizmessage.channel.send(f'Too bad, the anime was {mystery}')

            try:
                URL, title = getVideo(message.content.split(' ', 1)[1])
                voice_player = message.guild.voice_client
                if voice_player is None:
                    voice_player = await message.author.voice.channel.connect()

                if voice_player.is_playing():
                    voice_player.stop()
                    inquiz = False

                await message.channel.send(f'Now Playing {title}')
                voice_player.play(discord.FFmpegPCMAudio(URL, **FFMPEG_OPTIONS))

            except:
               await message.channel.send('Something went wrong when trying to retrieve the Video')
    
        try:
            if message.content.split()[0].lower() in ('$hi', '$hello', '$howdy'):
                await message.channel.send(f'Hello {message.author}!')
        except:
            pass

        if message.content.lower().startswith('$quiz'):

            try:
                # Threading can lead to some problems in sharing memory
                if inquiz:
                    await quizmessage.channel.send(f"Too bad, the anime was {mystery}")
                    inquiz = False
                    warning = False
                quizmessage = message
                quizzee = message.author
                await message.channel.send(f'Starting Quiz with {quizzee}')
                mystery = animelist[random.randint(0, 250)][1]
                URL, title = getVideo(mystery + ' Anime Opening')
                voice_player = message.guild.voice_client

                if voice_player is None:
                    voice_player = await message.author.voice.channel.connect()

                quiz_voice = voice_player

                if voice_player.is_playing():
                    voice_player.stop()

                inquiz = True
                voice_player.play(discord.FFmpegPCMAudio(URL, **FFMPEG_OPTIONS))
                await message.channel.send(f'Now Playing Mystery Opening\nCan you guess this?')
                quiztime = 0
            
            except:
                await message.channel.send('Something Went Wrong')
        
        if message.content.lower().startswith('$how are you?'):
            await message.channel.send("I'm Wonderful, Thanks for asking")
        
        if message.content.lower().startswith('$joke'):
            joke = random.choice(puns)
            await message.channel.send(joke)
        
        if message.content.lower().startswith('$help'):
            actions = '\n'.join(options)
            helpbed = discord.Embed(color=0x0000ff)
            helpbed.title = 'General Purpose Bot Commands'
            helpbed.set_thumbnail(url='https://images.discordapp.net/avatars/692723897887490138/5d4e9766c52fa9142924df3bb9a1d514.png?size=512')
            helpbed.description = actions
            await message.channel.send(embed=helpbed)
        
        if message.content.lower().startswith('$time'):
            await message.channel.send(f'It\'s currently {time.ctime()} in Kuwait')
        
        if message.content.lower().startswith('$ban'):
            user = message.content.split()[1]
            await message.channel.send(f'Ban {user}? [y/n]')
            await asyncio.sleep(2)
            await message.channel.send(f'Banning {user}')
            await asyncio.sleep(1)
            await message.channel.send('JK I Can\'t do that\nUnless.....')
        
        if message.content.lower().startswith('$weather'):
            channel = message.channel
            city = message.content.split(' ', 1)[1]
            text = getWeather(city, channel)
            await message.channel.send(text)
        
        if message.content.lower().startswith('$wiki'):
            wikibed = discord.Embed(color=0x0000ff)
            content = message.content.split(' ', 1)[1]
            summary, success = getSummary(content)

            if success:
                wikipage = wikipedia.page(title=content, preload=False)
                wikibed.title = wikipage.title
                wikibed.description = summary
                wikibed.set_thumbnail(url=wikipage.images[0])
                await message.channel.send(embed=wikibed)
            else:
                await message.channel.send('Your Query was too Ambiguous, or the Details don\'t Exist')
        
        if message.content.lower().startswith('$wolfram'):
            query = message.content.split(' ', 1)[1]

            try:
                solutions = wolfclient.query(query)
                answer = next(solutions.results).text
                wolfbed = discord.Embed(color=0xffa500)
                wolfbed.title = query
                wolfbed.description = answer
                await message.channel.send(embed=wolfbed)
            except:
                await message.channel.send("Wolfram cannot find the Answer to that Question")
        
        if message.content.lower().startswith('$dogbreed'):
            breeds = dog.all_breeds()
            doglist = '\n'.join(breeds)
            await message.channel.send(f'```These are the Dog Breeds on this Planet:\n{doglist}```')
        
        if message.content.lower().startswith('$rdog'):
            words = message.content.split()
            try:
                if len(words) == 1:
                    await message.channel.send(dog.random_image())
                else:
                    await message.channel.send(dog.random_image(words[1].lower()))
            except:
                await message.channel.send("Invalid Breed")

    # Token, must be a secret
    client.loop.create_task(quiz_timer())
    client.run(discordKey)

if __name__ == '__main__':
    main()