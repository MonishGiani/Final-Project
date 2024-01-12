import discord
from discord.ext import commands
import random
import requests

# Create a bot instance
bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())

# Dictionary to store each game's information for each server
tic_tac_toe_games = {}
rps_game_info = {}
guessing_game_info = {}

#API for facts command
USELESS_FACTS_API_URL = 'https://uselessfacts.jsph.pl/random.json'

#8 ball responses
magic_8_ball_responses = [
    "Yes",
    "No",
    "Ask again later",
    "Cannot predict now",
    "Don't count on it",
    "Most likely",
    "Outlook not so good",
    "You may rely on it"
]

# Command to start Magic 8-Ball
@bot.command(name='8ball')
async def magic_8_ball(ctx, *, question: str = "Will I get good luck today?"):
    # Select a random response from the list
    response = random.choice(magic_8_ball_responses)

    # Send the response to the user
    await ctx.send(f"**Question:** {question}\n**Answer:** {response}")

#command to generate facts
@bot.command(name='fact')
async def get_useless_fact(ctx):
    try:
        response = requests.get(USELESS_FACTS_API_URL)
        data = response.json()
        useless_fact = data['text']
        await ctx.send(f"Here's a random useless fact: {useless_fact}")
    except Exception as e:
        print(f"An error occurred: {e}")
        await ctx.send("Error: Unable to fetch a random useless fact at the moment.")



# Function to display the Tic-Tac-Toe board
def display_board(board):
    return '\n'.join([' '.join(row) for row in board])

# Function to check if a player has won
def check_winner(board, symbol):
    # Check rows, columns, and diagonals
    for i in range(3):
        if all(board[i][j] == symbol for j in range(3)) or all(board[j][i] == symbol for j in range(3)):
            return True
    if all(board[i][i] == symbol for i in range(3)) or all(board[i][2 - i] == symbol for i in range(3)):
        return True
    return False

# Command to start a new Tic-Tac-Toe game
@bot.command(name='tictactoe')
async def start_tic_tac_toe(ctx):
    # Check if a game is already in progress for this server
    if ctx.guild.id in tic_tac_toe_games:
        await ctx.send("A Tic-Tac-Toe game is already in progress!")
        return

    # Initialize a new game board
    board = [['-' for _ in range(3)] for _ in range(3)]
    tic_tac_toe_games[ctx.guild.id] = {'board': board, 'current_player': 'X'}

    # Display the initial game board
    await ctx.send(f"New Tic-Tac-Toe game started!\n{display_board(board)}\nPlayer X's turn.")

# Command to make a move in the Tic-Tac-Toe game
@bot.command(name='move')
async def make_move(ctx, row: int, col: int):
    # Check if a game is in progress for this server
    if ctx.guild.id not in tic_tac_toe_games:
        await ctx.send("No Tic-Tac-Toe game in progress. Start one with !tictactoe.")
        return

    game_info = tic_tac_toe_games[ctx.guild.id]
    board = game_info['board']
    current_player = game_info['current_player']

    # Check if the move is valid
    if 0 <= row < 3 and 0 <= col < 3 and board[row][col] == '-':
        # Make the move
        board[row][col] = current_player

        # Display the updated game board
        await ctx.send(f"Move made by {current_player}:\n{display_board(board)}")

        # Check for a winner
        if check_winner(board, current_player):
            await ctx.send(f"Player {current_player} wins!")
            del tic_tac_toe_games[ctx.guild.id]  # Remove game information
        else:
            # Switch to the next player
            game_info['current_player'] = 'O' if current_player == 'X' else 'X'
            await ctx.send(f"Player {game_info['current_player']}'s turn.")
    else:
        await ctx.send("Invalid move. Please try again.")

#Command to start RPS Game
class RPSGame:
    def __init__(self):
        self.choices = ["rock", "paper", "scissors"]
        self.bot_choice = None

    def start_game(self):
        self.bot_choice = random.choice(self.choices)

    def determine_winner(self, player_choice):
        if player_choice == self.bot_choice:
            return f"It's a tie! I also chose {self.bot_choice}."
        elif (
            (player_choice == "rock" and self.bot_choice == "scissors")
            or (player_choice == "paper" and self.bot_choice == "rock")
            or (player_choice == "scissors" and self.bot_choice == "paper")
        ):
            return f"You win! I chose {self.bot_choice}."
        else:
            return f"You lose! I chose {self.bot_choice}."

# Command for the player to make a move in the Rock, Paper, Scissors game
@bot.command(name='rps')
async def make_move(ctx, player_choice: str = None):
    global rps_game_info

    if ctx.guild.id not in rps_game_info:
        rps_game_info[ctx.guild.id] = RPSGame()
        rps_game_info[ctx.guild.id].start_game()

    rps_game = rps_game_info[ctx.guild.id]

    if player_choice:
        result = rps_game.determine_winner(player_choice.lower())
        del rps_game_info[ctx.guild.id]  # Remove game information
        await ctx.send(result)
    else:
        await ctx.send("Please provide your move: !rps [rock/paper/scissors].")


#command to start guessing game
@bot.command(name='guess')
async def start_guessing(ctx):
    # Check if a game is already in progress for this server
    if ctx.guild.id in guessing_game_info:
        await ctx.send("A guessing game is already in progress!")
        return

    # Generate a random number for the user to guess (between 1 and 100)
    secret_number = random.randint(1, 100)

    # Store game information for this server
    guessing_game_info[ctx.guild.id] = {'secret_number': secret_number, 'attempts': 0}

    await ctx.send("Welcome to the Guessing Game! I have selected a number between 1 and 100.")

# Event to handle user messages
@bot.event
async def on_message(message):
    # Check if a game is in progress for this server
    if message.guild and message.guild.id in guessing_game_info:
        try:
            number = int(message.content)
            await guess_number(message.guild.id, number, message.channel)
        except ValueError:
            pass

    await bot.process_commands(message)

async def guess_number(guild_id, number, channel):
    # Check if a game is in progress for this server
    if guild_id not in guessing_game_info:
        return

    game_info = guessing_game_info[guild_id]
    game_info['attempts'] += 1

    # Check if the guessed number is correct
    secret_number = game_info['secret_number']
    attempts = game_info['attempts']

    if number == secret_number:
        del guessing_game_info[guild_id]  # Remove game information
        await channel.send(f"Congratulations! You guessed the number {secret_number} in {attempts} attempts.")
    elif number < secret_number:
        await channel.send("Too low! Try again.")
    else:
        await channel.send("Too high! Try again.")

# Event to run when the bot is ready
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')

#use bot token
bot.run('MTE5MzU1MTczNjQ4OTY2MDQzNg.GyO0r1.7Vodr6Z8DJkBUqXiPxyEtId8ZZn45YFjdsThck')