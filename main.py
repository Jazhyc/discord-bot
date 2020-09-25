"""
Bot Created by Jazhyc
Contains some fun features that rely on a bunch of APIs
Use as you see fit
"""

import discord
import time, random
import requests, json
import wikipedia
from youtube_dl import YoutubeDL

weatherKey = "65ee9edb7a7e7a3186aea38f8429dc84"
discordKey = "NzQ0MjY3MDI4NDI0Mjk0NTAx.Xzgurw.IS8uNiGjJWke6LAb1QO_CzdCDIo"
weatherUrl = "http://api.openweathermap.org/data/2.5/weather?"

options = [
    '$Hello',
    '$How are you?',
    '$Tell me a joke',
    '$Time',
    '$Weather [City]',
    '$ban',
    '$Wikipedia [Webpage]',
    '$play [URL]'
]

inchannel = False

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
        except:
            message = 'Query was too Ambiguous, or the Details you are looking for does not exist.'
    return message


def main():
    """Brains of the Operation. Works Magically"""
    client = discord.Client()

    puns = load_jokes('jokes.txt')

    # Indicator that loading is succesful
    @client.event
    async def on_ready():
        print(f'Logged in as {client.user}')

    # Listens and responds to messages
    @client.event
    async def on_message(message):
        # Prevents bot from replying to itself
        if message.author == client.user:
            return

        if message.content.startswith('$join'):
            channel = message.author.voice.channel
            inchannel = True
            await channel.connect()

        if message.content.startswith('$leave'):
            server = message.guild.voice_client
            inchannel = False
            await server.disconnect()
        
        if message.content.startswith('$play'):
            """Not Really in a function but it works; plays video from any youtube url"""
            YDL_OPTIONS = {'format': 'bestaudio', 'noplaylist':'True'}
            FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
            video_link = message.content.split(' ', 1)[1]

            with YoutubeDL(YDL_OPTIONS) as ydl:
                info = ydl.extract_info(video_link, download=False)
            URL = info['formats'][0]['url']
            voice_player = await message.author.voice.channel.connect()
            voice_player.play(discord.FFmpegPCMAudio(executable="C:/Program Files/ffmpeg/ffmpeg.exe", source=URL, **FFMPEG_OPTIONS))
    
        try:
            if message.content.split()[0].lower() in ('$hi', '$hello', '$howdy'):
                await message.channel.send(f'Hello {message.author}!')
        except:
            pass
        
        if message.content.lower().startswith('$how are you?'):
            await message.channel.send("I'm Wonderful, Thanks for asking")
        
        if message.content.lower().startswith('$tell me a joke'):
            joke = random.choice(puns)
            await message.channel.send(joke)
        
        if message.content.lower().startswith('$help'):
            actions = '\n'.join(options)
            await message.channel.send(f'```These are my current Commands: \n{actions}```')
        
        if message.content.lower().startswith('$time'):
            await message.channel.send(f'It\'s currently {time.ctime()} in Kuwait')
        
        if message.content.lower().startswith('$ban'):
            user = message.content.split()[1]
            await message.channel.send(f'Ban {user}? [y/n]')
            time.sleep(2)
            await message.channel.send(f'Banning {user}')
            time.sleep(1)
            await message.channel.send('JK I Can\'t do that\nUnless.....')
        
        if message.content.lower().startswith('$weather'):
            channel = message.channel
            city = message.content.split(' ', 1)[1]
            text = getWeather(city, channel)
            await message.channel.send(text)
        
        if message.content.lower().startswith('$wikipedia') or message.content.lower().startswith('$wiki'):
            channel = message.channel
            content = message.content.split(' ', 1)[1]
            summary = getSummary(content)
            await message.channel.send(f"```{summary}```")

    # Token, must be a secret
    client.run(discordKey)

if __name__ == '__main__':
    main()