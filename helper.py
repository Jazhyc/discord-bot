"""This file contains all the functions necessary for the main executable to work"""

from os import path
import time, random
from youtube_dl import YoutubeDL
import discord
import requests, json
import wikipedia
import urllib.request, re
import dog_api as dog
import psycopg2

# Helper SQL functions
from sql import *

# Normal helper functions

def getSummary(content):
    """A bit Overkill for a single Function"""
    success = False
    if content == 'Trump':
        message = wikipedia.summary('Circus Clown', sentences=1)
    else:
        try:
            message = wikipedia.summary(content, sentences=3)
            success = True
        except:
            message = 'Query was too Ambiguous, or the Details you are looking for does not exist.'
            
    return message, success

def getVideo(link):
    """Gets Video Player Object and Title from Youtube, URL is the url for the audio"""
    YDL_OPTIONS = {'format': 'bestaudio', 'noplaylist':'True'}
    link = '-'.join(link.split())
    search_keyword = re.sub("['\"]",'', link)
    html = urllib.request.urlopen("https://www.youtube.com/results?search_query=" + search_keyword)
    video_ids = re.findall(r"watch\?v=(\S{11})", html.read().decode())
    video_link = "https://www.youtube.com/watch?v=" + video_ids[0]

    with YoutubeDL(YDL_OPTIONS) as ydl:
        info = ydl.extract_info(video_link, download=False)
    URL = info['formats'][0]['url']
    title = info['title']
    return URL, title, video_link

def load_jokes(file):
    """Loads jokes from a text file into a list object"""
    joke_file = open(file)
    return joke_file.read().split('\n')

def getWeather(city, channel, weatherUrl, weatherKey):
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

# Asynchronous Helper Functions to execute various commands

async def joinVC(message):
    """Joins the voice chanel of the guild in which the message was sent"""
    if message.content.lower().startswith('$join'):
        voice_player = await message.author.voice.channel.connect()
        await message.channel.send('Joined Voice Channel')

async def leaveVC(message):
    """Leaves the voice channel of the guild in which the message was sent"""
    if message.content.lower().startswith('$leave'):
        voice_player = message.guild.voice_client
        await voice_player.disconnect()
        await message.channel.send('Left Voice Channel')
        inQuiz = False

async def getTime(message):
    """Gets the time of region in which the bot is located"""
    if message.content.lower().startswith('$time'):
        await message.channel.send(f'It\'s currently {time.ctime()} somewhere')

async def generateDog(message):
    """Generates a picture of a random dog using the random dog API""" 
    if message.content.lower().startswith('$rdog'):
        words = message.content.split()
        try:
            if len(words) == 1:
                await message.channel.send(dog.random_image())
            else:
                await message.channel.send(dog.random_image(words[1].lower()))
        except:
            await message.channel.send("Invalid Breed")

async def getDogBreeds(message):
    """Produces a list of all the dog breeds in the API list"""
    if message.content.lower().startswith('$dogbreed'):
        breeds = dog.all_breeds()
        doglist = '\n'.join(breeds)
        await message.channel.send(f'```These are the Dog Breeds on this Planet:\n{doglist}```')

async def queryWolfram(message, wolfclient):
    """Sends a query to Wolfram Alpha and returns the answer"""
    if message.content.lower().startswith('$wolfram'):
        query = message.content.split(' ', 1)[1]

        try:
            solutions = wolfclient.query(query)
            answer = next(solutions.results).text
            wolfbed = discord.Embed(color=0xffa500)
            wolfbed.title = query
            wolfbed.description = answer
            await message.channel.send(embed=wolfbed)
        except Exception as e:
            await message.channel.send("Wolfram cannot find the Answer to that Question")
            await message.channel.send(e)

async def queryWikipedia(message):
    """Sends a query to Wikipedia and gets details regarding the query if possible"""
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

async def sendWeather(message, weatherUrl, weatherKey):
    """Gets the weather at the specified place using the open weather API"""
    if message.content.lower().startswith('$weather'):
        channel = message.channel
        city = message.content.split(' ', 1)[1]
        text = getWeather(city, channel, weatherUrl, weatherKey)
        await message.channel.send(text)

async def banUser(message):
    """Joke command that just sends a few messages into the guild"""
    if message.content.lower().startswith('$ban'):
        user = message.content.split()[1]
        await message.channel.send(f'Ban {user}? [y/n]')
        await asyncio.sleep(2)
        await message.channel.send(f'Banning {user}')
        await asyncio.sleep(1)
        await message.channel.send('JK I Can\'t do that\nUnless.....')

async def getHelp(message):
    """Produces a list of all the available commands of a bot"""

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
    'Wolfram [Query]',
    'score',
    'leaderboard'
    ]

    if message.content.lower().startswith('$help'):
        actions = '\n'.join(options)
        helpbed = discord.Embed(color=0x0000ff)
        helpbed.title = 'General Purpose Bot Commands'
        helpbed.set_thumbnail(url='https://images.discordapp.net/avatars/692723897887490138/5d4e9766c52fa9142924df3bb9a1d514.png?size=512')
        helpbed.description = actions
        await message.channel.send(embed=helpbed)

async def queryHealth(message):
    """Incase you were wondering about the health of the bot"""
    if message.content.lower().startswith('$how are you?'):
        await message.channel.send("I'm Wonderful, Thanks for asking")

async def getJoke(message, puns):
    """Selects a random joke from the joke list and sends it to the server"""
    if message.content.lower().startswith('$joke'):
        joke = random.choice(puns)
        await message.channel.send(joke)

async def greetUser(message):
    """Greets the User"""
    try:
        if message.content.split()[0].lower() in ('$hi', '$hello', '$howdy'):
            await message.channel.send(f'Hello {message.author}!')
    except:
        pass

async def correctAnswer(message, inQuiz, quizzee, warning, quiztime, mystery, cursor):
    """Determines if the answer received is correct"""

    if message.content.lower() in mystery.lower() and len(message.content) >= 4 and inQuiz:
        await message.channel.send(f"Congratulations, the Anime is {mystery}")
        voice_player = message.guild.voice_client
        voice_player.stop()
        voice_player.play(discord.FFmpegPCMAudio('Sounds/success.mp3'))
        inQuiz = False
        quizzee = ''
        warning = False
        quiztime = 0

        user = message.author.name
        score = getSQLScore(cursor, user)

        # Increments score or creates it accordingly
        if checkExists(cursor, user):
            incrementScore(cursor, user, score)
        else:
            createScore(cursor, user, 1)
        
        await message.channel.send(f"{user}'s score is now: {score + 1}")

    return inQuiz, quizzee, warning, quiztime

async def stopQuiz(message, inQuiz, warning, quiztime, quizmessage, mystery):
    """Stops the quiz that is being played in the specified guild"""

    if message.content.lower().startswith('$stop'):
        voice_player = message.guild.voice_client

        if voice_player.is_playing():
            voice_player.stop()
            if inQuiz:
                await quizmessage.channel.send(f'Too bad, the anime was {mystery}')
                inQuiz = False
                warning = False
                quiztime = 0
            await message.channel.send('Video Stopped')
        else:
            await message.channel.send('I can\'t stop the voices in your head')

    return inQuiz, warning, quiztime

async def playVideo(message, re, urllib, YoutubeDL, inQuiz, warning, quizzee, quiztime, quizmessage, mystery):
    """Plays the specified video while also changing the quiz variables as needed"""

    FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

    if message.content.startswith('$play'):

        if inQuiz:
            inQuiz = False
            warning = False
            quizzee = ''
            quiztime = 0
            await quizmessage.channel.send(f'Too bad, the anime was {mystery}')

        try:
            URL, title, video_link = getVideo(message.content.split(' ', 1)[1])
            voice_player = message.guild.voice_client
            if voice_player is None:
                voice_player = await message.author.voice.channel.connect()

            if voice_player.is_playing():
                voice_player.stop()
                inQuiz = False

            await message.channel.send(f'Now Playing {title}')
            await message.channel.send(video_link)
            voice_player.play(discord.FFmpegPCMAudio(URL, **FFMPEG_OPTIONS))

        except Exception as e:
            await message.channel.send('Something went wrong when trying to retrieve the Video')
            await message.channel.send(e)
    
    return inQuiz, warning, quizzee, quiztime

async def startQuiz(message, inQuiz, quizzee, warning, quiztime, mystery, quizmessage, animelist):
    """Selects a random song to play from the anime list"""

    FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

    start = time.perf_counter()

    if message.content.lower().startswith('$quiz'):

        try:
            # Threading can lead to some problems in sharing memory
            if inQuiz:
                await quizmessage.channel.send(f"Too bad, the anime was {mystery}")
                warning = False

            quizmessage = message
            quizzee = message.author
            await message.channel.send(f'Starting Quiz with {quizzee}')
            mystery = animelist[random.randint(0, 150)][1]
            URL, title, video_link = getVideo(mystery + ' Anime Opening')
            voice_player = message.guild.voice_client

            if voice_player is None:
                voice_player = await message.author.voice.channel.connect()

            quiz_voice = voice_player

            if voice_player.is_playing():
                voice_player.stop()

            inQuiz = True
            voice_player.play(discord.FFmpegPCMAudio(URL, **FFMPEG_OPTIONS))

            # Logs
            print(mystery)

            await message.channel.send(f'Now Playing Mystery Opening\nCan you guess this?')
            quiztime = 0
        
        except Exception as e:
            await message.channel.send('Something Went Wrong')
    
    return inQuiz, quizzee, warning, quiztime, mystery, quizmessage, start

async def getScore(message, cursor):
    """Gets the score of the user un the quiz game. If the user never played it, create a new entry"""

    if message.content.lower().startswith("$score"):

        user = message.author.name

        if (checkExists(cursor, user)):
            score = getSQLScore(cursor, user)
            await message.channel.send(f"{user}'s score: {score}")

        else:
            createScore(cursor, user, 0)
            await message.channel.send(f"{user}'s score: 0")

async def getLeaderboard(message, cursor):
    """Prints the players who are at the top of the leaderboard"""

    if message.content.lower().startswith("$leaderboard"):

        leaderboard = getSQLLeaderboard(cursor)

        size = min(len(leaderboard), 10)

        content = '\n'.join([f"Position {i + 1} - {leaderboard[i][0]:^20} - Score: {leaderboard[i][1]:^20}" for i in range(size)])

        leaderBed = discord.Embed(color=0x0000ff)
        leaderBed.title = "Current Global Leaderboard"
        leaderBed.description = content
        leaderBed.set_thumbnail(url='https://t3.ftcdn.net/jpg/02/84/67/02/360_F_284670286_VB4EEnS01sbqlueiFka9BO3S5bEFhnx2.jpg')

        await message.channel.send(embed=leaderBed)