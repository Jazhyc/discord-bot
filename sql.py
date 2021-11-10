"""This file contains all the code required to use the POSTGRES server so that bot has access to permanent storage"""

def createTable(cursor):
    """Creates specified table if it does not exist"""
    
    command = "CREATE TABLE IF NOT EXISTS leaderboard (username varchar(50) NOT NULL, score INT NOT NULL)"
    cursor.execute(command)

def checkExists(cursor, user):
    """Checks if a user is present in the table"""

    command = "SELECT EXISTS(SELECT 1 FROM leaderboard WHERE username = %s)"
    cursor.execute(command, (user,))

    # The function returns a tuple
    return cursor.fetchone()[0]

def createScore(cursor, user, value):
    """Creates an entry for a new user"""

    command = "INSERT into leaderboard Values (%s, %s)"
    cursor.execute(command, (user,value))

def getSQLScore(cursor, user):
    """Gets the score of a user"""

    command = "SELECT score from leaderboard where username = %s"
    cursor.execute(command, (user,))

    return cursor.fetchone()[0]

def incrementScore(cursor, user, score):
    """Increments the score of a user by 1"""

    command = "UPDATE leaderboard set score = %s where username = %s"
    cursor.execute(command, (score + 1, user))

def getSQLLeaderboard(cursor):
    """Gets the top 10 players globally"""

    command = "Select * from leaderboard order by score DESC LIMIT 10"
    cursor.execute(command)

    return cursor.fetchall()