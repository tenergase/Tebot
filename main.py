# main.py
import os
import discord
import csv
import asyncio
import datetime
from discord.ext import commands, timers # :) hey guys
from dotenv import load_dotenv
from discord.utils import get

load_dotenv()

prefix = "$"
bot = commands.Bot(command_prefix=prefix, case_insensitive=True)


@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')

@bot.command(name='create_roles')
async def _create_roles(ctx):
  roles_created = False
  role_names = ['exam', 'quiz', 'assignment']
  guild = ctx.guild

  for role_name in role_names:
    if not discord.utils.get(guild.roles, name=role_name):
      await ctx.guild.create_role(name=role_name)
      roles_created = True

  if roles_created:
    msg = await ctx.send("Roles created :)")
  else:
    msg = await ctx.send("Roles already created")
      
  await asyncio.sleep(5)
  await ctx.message.delete()
  await msg.delete()


@bot.command(name='hello',
             help='type $hello to have the bot greet you!',
             brief='bot responds with "Hello!"')
async def _hello(ctx):
  await ctx.send('Hello!')


# Gets type of schedule to show based off of reactions
# A for assignments, E for exams, Q for quizzes, 100 for all
@bot.command(name='schedule',
             help='pass either \'assignment\', \'quiz\', or \'exam\' to see the list of due dates',
             brief='display list of asssignments, quizzes, or exams')
async def _schedule(ctx):
    msg = await ctx.send("Which type of work would you like to see?")
    mode = await reactEQAAll(ctx, msg) # The bot reacts to the above message
    msg2 = await show_list(ctx, mode) # Passed to show_list function with a mode
    await react_close(ctx, msg2)
    await msg.delete()

# Pluralize type for use in formatting output
async def to_plural(_type):
  if _type == 'assignment':
    plural = 'assignments'
  elif _type == 'quiz':
    plural = 'quizzes'
  elif _type == 'exam':
    plural = 'exams'
  else:
    plural = ''
  return plural

# Map '_type' to corresponding file name
async def get_file_name(_type):
  print("type in get_file_name is " + _type)
  if _type == 'assignment':
    file_name = 'assignments.csv'
  elif _type == 'quiz':
    file_name = 'quizzes.csv'
  elif _type == 'exam':
    file_name = 'exams.csv'
  else:
    file_name = ""
    
  return file_name

# Display the list of either assignments, quizzes, exams, or all
# Called by _schedule()
async def show_list(ctx, _type):
    with open("schedule.csv") as fileRead:
        reader = csv.reader(fileRead, delimiter=',')
        # Executes when displaying all of the assignments, quizzes, and exams
        if (_type == 'all'):
            message = '```Current workload consists of:\n'
            typecount = [0 for i in range(3)]
            for row in reader:
                # Used to keep track of how many of each type of work there are
                # I know its a dorky implementation but theres no switch statements in Python
                # typecount[0] = Assignments
                # 1 = Quizzes
                # 2 = Exams
                # sw is a switch variable
                if (row[2] == 'assignment'):
                    sw = 0
                    typecount[0] += 1
                elif (row[2] == 'quiz'):
                    sw = 1
                    typecount[1] += 1
                elif (row[2] == 'exam'):
                    sw = 2
                    typecount[2] += 1
                else: # If it's not an assignment, quiz, or exam, it's an error
                    await ctx.send("An error occurred")
                    return

                # Text formatting in two columns
                assignment_str = "%s %d: %s" % (row[2].capitalize(), typecount[sw], row[0])
                duedate_str = "Due: %s" % row[1]
                message += "{: <35} {: <35}\n".format(assignment_str, duedate_str)
        # Executes when a single type of work has been selected to display
        else:
            i = 1
            message = '```Current {} are:\n'.format(await to_plural(_type))
            for row in reader:
                # Iterates through the entire schedule.csv, checking if the type is desired
                if (row[2] == _type):
                    # If it is, display it, and update the counter of how many of that workload there are
                    assignment_str = "%s %d: %s" % (row[2].capitalize(), i, row[0])
                    duedate_str = "Due: %s" % row[1]
                    message += "{: <35} {: <35}\n".format(assignment_str, duedate_str)
                    i += 1
        message += '```'
        # Used to close off coding message format on Discord for proper formatting
        # (Discord characters are not uniform width
        return await ctx.send(message)

# Used to valiDATE a date (haha I'm sure you've never heard that pun before -d)
def validDate(_date):
    __date = _date.content
    if len(__date) != 8:
      return False
    month, day, year = __date.split('/') # Splits the date into three variables
    # Very basic input validation
    if int(year) != 21 or int(day) <= 0 or int(day) >= 32 or int(month) <= 0 or int(month) >= 13:
        return False

    # How to determine if it's a vaild date using datetime with a try except
    try:
        datetime.datetime(int(year), int(month), int(day))
    except ValueError:
        return False
    return True

# Used to add an assignment, quiz, or exam to the schedule
# Prompted with a message and reacts to select which type of work they would like to add
# Afterwards, prompted again to check if the item they want to add has already been added
#  to the schedule
@bot.command(name='add',
             help="choose an assignment, quiz, or exam with a reaction and input the name and date in separate commands",
             brief="input a new item")
async def _add(ctx):
    msg = await ctx.send("What type of work would you like to add? (exam/quiz/assignment)")
    _type = await reactEQA(ctx, msg) # Reacts to above message
    msg2 = await show_list(ctx, _type) # Shows only the type of workload they want
    msg3 = await ctx.send("Is the " + _type + " you want to add already on the schedule? (Y/N)")
    _continue = await reactYN(ctx, msg3)
    # Don't add duplicates
    if _continue == "yes": 
        msg4 = await ctx.send("Thank you for trying to contribute!")
        await asyncio.sleep(5)
        await msg.delete()
        await msg2.delete()
        await msg3.delete()
        await msg4.delete()
        return
    # Otherwise, get the assignment's name and due date
    else: 
        msg4 = await ctx.send("Please enter the " + _type + "\'s name:\n")
        name = await bot.wait_for('message', check=lambda message: message.author == ctx.author, timeout=60)

        msg5 = await ctx.send("Please enter the " + _type + "\'s due date as mm/dd/yy:\n")
        goodDate = False
        while not goodDate:
          dueDate = await bot.wait_for('message', check=lambda message: message.author == ctx.author, timeout=25)
          # Check if the date is valid
          if validDate(dueDate):
              goodDate = True
              await insert(_type, name.content, dueDate.content)
              msg6 = await ctx.send(name.content + " was successfully added!")
          else:
              await msg5.delete()
              msg5 = await ctx.send("Please try again with a valid date! (mm/dd/yy)")
      

# Used with the above add function
# Actual add functionality to the schedule.csv
# Inserts the type of work ordered by dates, earliest to latest
async def insert(_type, name, date):
    i = 0
    month1, day1, year1 = date.split('/') # Splits the date that was passed in and makes it a datetime object
    d1 = datetime.datetime(int(year1), int(month1), int(day1))
    fileName = "schedule.csv"
    _row = [name, date, _type] # _row is used as the row that will be inserted
    with open(fileName) as fileRead:
        reader = csv.reader(fileRead, delimiter=',')
        # Iterates through schedule.csv until a row is found with a date that is later than the current one's
        for row in reader:
            tempDate = row[1]
            month2, day2, year2 = tempDate.split('/')
            d2 = datetime.datetime(int(year2), int(month2), int(day2))
            if (d1 < d2):
                break
            i += 1
        # Resets the reader to the top of the file, (important for the list)
        fileRead.seek(0, 0)
        lines = list(reader) # Creates a list from the reader 
        lines.insert(i, _row) # Inserts the row into the list
    with open(fileName, 'w', newline='') as fileWrite:
        writer = csv.writer(fileWrite)
        writer.writerows(lines) # Rewrites the lines object into schedule.csv

# Used to delete an assignment, quiz, or exam from the schedule
# Prompted with a message and reacts to select which type of work they would like to add
# Afterwards, shown a list of the type of work that they want to delete
# Afterwards, prompted to enter the exact name of the work they want to delete from the schedule
@bot.command(name='delete',
             help="choose an assignment, quiz, or exam with a reaction and input the name and date in separate commands",
             brief="input a new item")
async def _delete(ctx):
    msg = await ctx.send("What type of work would you like to delete?")
    _type = await reactEQA(ctx, msg)
    await show_list(ctx, _type)
    await ctx.send("Please enter the " + _type + "\'s name:\n")
    name = await bot.wait_for('message', check=lambda message: message.author == ctx.author, timeout=60) # Name of the assignment to be deleted
    if await remove(name.content): # Calls remove function which returns true on successful deletion
        await ctx.send("Deletion successful!")
    else:
        await ctx.send("An error has occurred")

# Used in tandem with the above delete function
# Actual removing capabilities from the schedule.csv
# Iterates through the schedule.csv, checking for the name of the item to be deleted
#  When a match is found, removes the line (WILL DELETE DUPLICATE ENTRIES UNTIL END OF FILE)
async def remove(name):
    i = 0
    var = False
    fileName = "schedule.csv"
    with open(fileName) as fileRead:
        reader = csv.reader(fileRead, delimiter=',')
        lines = list() # Create an empty list
        for row in reader:
            lines.append(row) # Append the row
            if row[0] == name: # If the row contains the work being deleted, remove the row from the lines object
                var = True
                lines.remove(row) 
    with open(fileName, 'w', newline='') as fileWrite:
        writer = csv.writer(fileWrite)
        writer.writerows(lines)
        return var

# Input context and a message to react to
# Add E, Q, A possible reactions, and await a reaction from the user
# Return a string representation either 'exam', 'quiz', or 'assignment'
async def reactEQA(ctx, msg):
  await msg.add_reaction(u"\U0001F1EA")
  await msg.add_reaction(u"\U0001F1F6")
  await msg.add_reaction(u"\U0001F1E6")

  def check(reaction, user):
    return user == ctx.message.author
  reaction, user = await bot.wait_for('reaction_add', check=check, timeout=60)

  if str(reaction.emoji) == str(u"\U0001F1EA"):
    return 'exam'
  if str(reaction.emoji) == u"\U0001F1F6":
    return 'quiz'
  if str(reaction.emoji) == u"\U0001F1E6":
    return 'assignment'
    
# Input context and a message to react to
# Return a string representation either 'exam', 'quiz', 'assignment', or 'all'
async def reactEQAAll(ctx, msg):
    await msg.add_reaction(u"\U0001F1EA")
    await msg.add_reaction(u"\U0001F1F6")
    await msg.add_reaction(u"\U0001F1E6")
    await msg.add_reaction(u"\U0001F4AF")

    def check(reaction, user):
        return user == ctx.message.author

    reaction, user = await bot.wait_for('reaction_add', check=check, timeout=60)

    if str(reaction.emoji) == str(u"\U0001F1EA"):
        return 'exam'
    if str(reaction.emoji) == u"\U0001F1F6":
        return 'quiz'
    if str(reaction.emoji) == u"\U0001F1E6":
        return 'assignment'
    if str(reaction.emoji) == u"\U0001F4AF":
        return 'all'

# Input context and a message to react to
# Add Y and N reactions to the message, await reaction from the user
# Return a string 'yes' or 'no' depending on the user's response
async def reactYN(ctx, msg):
  await msg.add_reaction(u"\U0001F1FE")
  await msg.add_reaction(u"\U0001F1F3")

  def check(reaction, user):
    return user == ctx.message.author
  reaction, user = await bot.wait_for('reaction_add', check=check, timeout=30)

  if str(reaction.emoji) == u"\U0001F1FE":
    return 'yes'
  if str(reaction.emoji) == u"\U0001F1F3":
    return 'no'

async def react_close(ctx, msg):
  await msg.add_reaction(u"\u274C")

  def check(reaction, user):
    return user == ctx.message.author

  reaction, user = await bot.wait_for('reaction_add', check=check)

  if str(reaction.emoji) == u"\u274C":
    await ctx.message.delete()
    await msg.delete()

#subscribe to roles
@bot.command(name ='subscribe', help = 'react to the \'E\', \'Q\', or \'A\' to be notified of upcoming deadlines. react with a \'y\' to continue adding roles, or a \'n\' to stop.', brief = 'react to get notified for upcoming assignment deadlines, quizzes, or exams')
async def _subscribe(ctx):
  msg = await ctx.send("react to this message with an emoji")
  # Get a string to represent the type of role to add
  _type = await reactEQA(ctx, msg)

  # Define the user to assign a role to
  user = ctx.message.author

  if _type == 'exam':
    msg2 = await ctx.send("Exam role assigned")
    role = discord.utils.get(ctx.guild.roles, name='exam')
  if _type == 'quiz':
    msg2 = await ctx.send("Quiz role assigned")
    role = discord.utils.get(ctx.guild.roles, name='quiz')
  if _type == 'assignment':
    msg2 = await ctx.send("Assignment rold assigned")
    role = discord.utils.get(ctx.guild.roles, name='assignment')

  # Add the role specified 
  await user.add_roles(role)

  # Determine whether to add another role (loop)
  msg3 = await ctx.send("Would you like to continue? (Y/N)")
  YN = await reactYN(ctx, msg3)
  if YN == 'yes':
    await _subscribe(ctx)

  await ctx.message.delete()
  await msg.delete()
  await msg2.delete()
  await msg3.delete()
    
 
#unsubscribe from roles
@bot.command(name ='unsubscribe')
async def _unsubscribe(ctx):
    msg = await ctx.send("react to this message with an emoji")
    # Get a string to represent the type of role to add
    _type = await reactEQA(ctx, msg)

    # Define the user to assign a role to
    user = ctx.message.author

    if _type == 'exam':
        msg2 = await ctx.send("Exam role removed")
        role = discord.utils.get(ctx.guild.roles, name='exam')
    if _type == 'quiz':
        msg2 = await ctx.send("Quiz role removed")
        role = discord.utils.get(ctx.guild.roles, name='quiz')
    if _type == 'assignment':
        msg2 = await ctx.send("Assignment role removed")
        role = discord.utils.get(ctx.guild.roles, name='assignment')

    # Add the role specified
    await user.remove_roles(role)

    # Determine whether to remove another role (loop)
    msg3 = await ctx.send("Would you like to continue? (Y/N)")
    YN = await reactYN(ctx, msg3)
    if YN == 'yes':
      await _unsubscribe(ctx)

    await ctx.message.delete()
    await msg.delete()
    await msg2.delete()
    await msg3.delete()


@bot.command(name ='set')
async def _set(ctx):
  await ctx.send("timer set for 2 mins")
  guild = ctx.guild
  rol = get(guild.roles, name = 'exam')
  await asyncio.sleep(3)
  await ctx.send("Hey " + rol.mention + " you have Biology Exam today at 4 PM")


bot.timer_manager = timers.TimerManager(bot)


@bot.command(name="remind")
async def remind(ctx, time, _type, text):
    """Remind to do something on a date.

    The date must be in ``Y/M/D`` format."""
    date = datetime.datetime(*map(int, time.split('/')))

    bot.timer_manager.create_timer("reminder", date, args=(ctx, ctx.channel.id, ctx.author.id, _type, text))
    await ctx.send("Reminder created for {} for {}".format(text, date))
    # or without the manager
    #timers.Timer(bot, "reminder", date, args=(ctx.channel.id, ctx.author.id, text)).start()

@bot.event
async def on_reminder(ctx, channel_id, author_id, _type, text):
    channel = bot.get_channel(channel_id)

    await channel.send("Hey, {0}, you have an upcoming {1}: {2}".format(discord.utils.get(ctx.guild.roles, name=_type).mention, _type, text))

@bot.event
async def on_reminderExam(channel_id, author_id, role, text):
    channel = bot.get_channel(channel_id)

    await channel.send("Hey @exam, you have #insert exam here exam in 12 hours")

@bot.event
async def on_reminderQuiz(channel_id, author_id,  text):
    channel = bot.get_channel(channel_id)

    await channel.send("Hey, <@{0}>, remember to: {1}".format(author_id, text))

@bot.event
async def on_reminderAssignment(channel_id, author_id,  text):
    channel = bot.get_channel(channel_id)

    await channel.send("Hey, <@{0}>, remember to: {1}".format(author_id, text))


bot.run(os.getenv('TOKEN'))
