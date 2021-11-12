"""
Bot Created by Jazhyc
Contains some fun features that rely on a bunch of APIs
"""

import discord, asyncio
import csv
import wolframalpha
import psycopg2
from jikanpy import Jikan

# Custom library that contains all the code required for the bot to work
from helper import *

# Custom library that contains commands necessary to maintain the leaderboard
from sql import *

# Keys required for accessing various APIs
from keys import *

# Global Variables, these need to dissapear
inQuiz = warning = False
quizzee = mystery = quizchannel = quizmessage = ''
quiztime = start = stop = 0

def main():
    """Brains of the Operation. Works Magically"""
    client = discord.Client()
    wolfclient = wolframalpha.Client(WOLFRAM_KEY)
    puns = load_jokes('jokes.txt')

    # Generate anime selector object
    jikan = Jikan()
    animes = loadAnimes(jikan)

    # Creates connection to Postgres Database
    connection = psycopg2.connect(DATABASE_URL)
    cur = connection.cursor()

    # Creates Table in Database
    createTable(cur)

    # Indicator that loading is successful
    @client.event
    async def on_ready():
        print(f'Logged in as {client.user}')
        await client.change_presence(activity=discord.Game(name="Countdown till the Singularity"))

    async def quiz_timer():
        """Only one instance is created therefore the quiz function should not work in different guilds"""
        
        print('quiz_timer loaded')
        await client.wait_until_ready()
        global inQuiz, quiztime, quizchannel, mystery, warning, start, quizmessage

        while not client.is_closed():

            if (quizmessage != ''):
                voice_player = quizmessage.guild.voice_client

            start = time.perf_counter()

            while inQuiz:
                end = time.perf_counter()
                quiztime = end - start

                # For debugging if the timer is working properly
                print(quiztime)

                if quiztime > 45 and not warning:
                    await quizmessage.channel.send('Video Stopped\nGive Me your best Guess')
                    voice_player.stop()
                    warning = True
            
                if quiztime >= 60:
                    quiztime = 0
                    inQuiz = False
                    warning = False
                    voice_player.stop()
                    await quizmessage.channel.send(f'That\'s too bad, the anime was {mystery}')
                    voice_player.play(discord.FFmpegPCMAudio('Sounds/failure.mp3'))
                    break

                await asyncio.sleep(5)

            await asyncio.sleep(5)

    # Listens and responds to messages
    @client.event
    async def on_message(message):

        # What possessed me to use these earlier?
        global inQuiz, quizzee, mystery, quiztime, warning, start, stop, quizmessage, quiz_voice

        # Sanity check to stop the time counter
        if not inQuiz:
            start = time.perf_counter()

        # Prevents bot from replying to itself
        if message.author == client.user:
            return

        # Plays the video specified in the message
        inQuiz, warning, quizzee, quiztime = await playVideo(message, re, urllib, YoutubeDL, inQuiz, warning, quizzee, quiztime, quizmessage, mystery)

        # Stops the quiz
        inQuiz, warning, quiztime = await stopQuiz(message, inQuiz, warning, quiztime, quizmessage, mystery)
        
        # Checks if the correct answer is received
        inQuiz, quizzee, warning, quiztime = await correctAnswer(message, inQuiz, quizzee, warning, quiztime, mystery, cur)

        # Starts the quiz and selects a random song
        inQuiz, quizzee, warning, quiztime, mystery, quizmessage, start = await startQuiz(message, inQuiz, quizzee, warning, quiztime, mystery, quizmessage, animes, start)

        # Leaves the VC while also turning off the quiz
        inQuiz = await leaveVC(message, inQuiz)

        await joinVC(message)

        await greetUser(message)
        
        await queryHealth(message)

        await getJoke(message, puns)

        await getHelp(message)

        await getTime(message)
        
        await banUser(message)
        
        await sendWeather(message, weatherUrl, weatherKey)

        await queryWikipedia(message)

        await queryWolfram(message, wolfclient)
        
        await getDogBreeds(message)

        await generateDog(message)

        await getScore(message, cur)

        await getLeaderboard(message, cur)

        # Commits whatever change the cursors may have made
        # This might not scale as the bot gets introduced to more servers
        connection.commit()
        
    # Token, must be a secret
    client.loop.create_task(quiz_timer())
    client.run(discordKey)

if __name__ == '__main__':
    main()