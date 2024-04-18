import discord
from discord.ui import *
import os
from discord.ext import commands
from discord import app_commands
import requests
import json
import asyncio
from random import randint

bot = commands.Bot(command_prefix='!!', intents=discord.Intents.all())

TOKEN = '


# ON BOT READY
@bot.event
async def on_ready():
  print('Logged in as ' + bot.user.name)
  try:
    synced = await bot.tree.sync()
    print(f"Synced {len(synced)} command(s)")

  except Exception as e:
    print(e)


# LOAD JSON FILES
with open(r"roles.json", 'r') as f:
  roles = json.load(f)

with open(r"user_inventory.json", 'r') as f:
  inventory = json.load(f)

with open(r"user_profile.json", 'r') as f:
  profile = json.load(f)


# SAVE JSON FILES
async def save_profile():
  with open(r"user_profile.json", 'w') as f:
    json.dump(profile, f, indent=4)


async def save_roles():
  with open(r"roles.json", 'w') as f:
    json.dump(roles, f, indent=4)


async def save_inventory():
  with open(r"user_inventory.json", 'w') as f:
    json.dump(inventory, f, indent=4)


# ON MESSAGE
@bot.event
async def on_message(message):

  author_id = str(message.author.id)

  if message.author == bot.user:
    return

  # REGISTER USER IF NOT IN SYSTEM
  if not author_id in inventory and message.author.id != bot.user.id:
    await register_user(author_id)

  # EXP AND LEVEL UP
  profile[author_id]['exp'] += 1

  if lvl_up(author_id):

    await message.channel.send(
      f"{message.author.mention} has leveled up to lvl.{profile[author_id]['level']}" + " [+100<:gold_coin:957561865603543040>]"
    )

  await save_profile()


# LEVEL UP
def lvl_up(author_id):

  current_lvl = profile[author_id]['level']
  current_exp = profile[author_id]['exp']

  if current_exp >= round((4 * (current_lvl**3)) / 5):

    profile[author_id]['level'] += 1
    profile[author_id]['gold'] += 100
    return True

  else:

    return False


# REGISTER NEW USER
async def register_user(id):
  inventory[id] = {}
  inventory[id]['owned_roles'] = {}
  inventory[id]['equipped_role'] = ""
  inventory[id]['desired_role'] = 0

  await save_inventory()

  profile[id] = {}
  profile[id]['level'] = 1
  profile[id]['gold'] = 0
  profile[id]['exp'] = 0
  profile[id]['description'] = "[default description]"

  await save_profile()


# WATCH GENERAL
@bot.tree.command(name="watchgeneral", description="watch general")
async def watchgeneral(interaction: discord.Interaction):

  generalEmbed = discord.Embed(
    title=":white_check_mark: Anti-Cringe Verification",
    description=
    "Scan the QR Code on your Discord Moderator Interface to continue",
    colour=0x76ed66)

  generalEmbed.set_image(
    url=
    "https://cdn.discordapp.com/attachments/939342608260530226/1064552889990778961/watchgeneral.jpg"
  )

  generalEmbed.set_footer(text="This code will expire when you do.")

  await interaction.response.send_message(embed=generalEmbed)


# PROFILE
@bot.tree.command(name="profile", description="show your user profile")
async def get_profile(interaction: discord.Interaction,
                      member: discord.Member = None):

  member = interaction.user if not member else member

  author_id = str(member.id)

  # GET USER INFO
  level = profile[author_id]['level']
  gold = profile[author_id]['gold']
  exp = profile[author_id]['exp']
  desc = profile[author_id]['description']

  # CREATE EMBED

  profile_embed = discord.Embed(title=f"Profile - {member}",
                                description=desc,
                                color=member.color,
                                timestamp=interaction.created_at)

  profile_embed.set_thumbnail(url=member.avatar)

  profile_embed.add_field(name="Level", value=level, inline=True)

  profile_embed.add_field(name="Exp to lvl up",
                          value=(round((4 * (level**3)) / 5) - exp),
                          inline=True)

  profile_embed.add_field(name="Total Messages", value=exp, inline=True)

  profile_embed.add_field(name="Gold",
                          value=f"{gold}<:gold_coin:957561865603543040>",
                          inline=False)

  await interaction.response.send_message(embed=profile_embed)


# SET DESCRIPTION
@bot.tree.command(name="setdesc",
                  description="change the message displayed on your profile")
async def set_desc(interaction: discord.Interaction, message: str):

  author_id = str(interaction.user.id)

  profile[author_id]['description'] = message

  await save_profile()

  # CREATE EMBED

  desc_embed = discord.Embed(
    description=f"Description updated! New message: **{message}**",
    color=interaction.user.color,
    timestamp=interaction.created_at)

  desc_embed.set_author(name=f"Profile - {interaction.user}",
                        icon_url=interaction.user.avatar)

  await interaction.response.send_message(embed=desc_embed)


# CREATE ROLE
@bot.tree.command(name="createrole", description="create a new role")
async def create_role(interaction: discord.Interaction, name: str, colour: str,
                      cost: str):

  author_id = str(interaction.user.id)

  # TEST IF USER IS AUTHORISED (ME)

  if author_id != "312466843803582466":
    await interaction.response.send_message("Bzzzzt~! Unauthorized User!")
    return

  # MAKE ROLE

  hexcolour = int("0x" + colour, 16)

  lower_name = name.lower()

  roles['roles'][lower_name] = {}
  roles['roles'][lower_name]['cost'] = cost
  roles['roles'][lower_name]['colour'] = hexcolour

  guild = interaction.guild

  all_roles = await guild.fetch_roles()
  num_roles = len(all_roles)

  new_role = await guild.create_role(name=name, color=hexcolour, hoist=True)

  await new_role.edit(position=num_roles - 1)

  print(new_role.id)

  roles['roles'][lower_name]['id'] = new_role.id

  await save_roles()

  # EMBED

  role_embed = discord.Embed(title="New role created!",
                             color=hexcolour,
                             timestamp=interaction.created_at)

  role_embed.set_author(name=f"Role Creation - {interaction.user}",
                        icon_url=interaction.user.avatar)

  role_embed.add_field(name="Name", value=name)
  role_embed.add_field(name="Cost",
                       value=f"{cost}<:gold_coin:957561865603543040>")

  await interaction.response.send_message(embed=role_embed)


# LIST ROLES
@bot.tree.command(name="listroles",
                  description="list all available roles on this server")
async def list_roles(interaction: discord.Interaction):

  guild = interaction.guild

  role_list = []

  # GET ROLES FROM JSON FILE AND ADD TO LIST
  for role in roles['roles']:
    temp_role = discord.utils.get(interaction.guild.roles,
                                  id=roles['roles'][role]['id'])
    print(temp_role)
    role_list.append(
      f"- {temp_role.mention} {roles['roles'][role]['cost']} <:gold_coin:957561865603543040>\n"
    )

  # EMBED
  list_embed = discord.Embed(title="Role List",
                             color=interaction.user.color,
                             timestamp=interaction.created_at)

  list_embed.set_author(name=f"Role List - {interaction.user}",
                        icon_url=interaction.user.avatar)


  i = 0

  temp1 = ""
  temp2 = ""
 
  while i < len(role_list) - 1:
      if len(role_list) <= 24:
          if i <= 12:
              temp1 += role_list[i]
          else:
              temp2 += role_list[i]
      i += 1

  list_embed.add_field(name="Roles 1", value=temp1)

  if len(role_list) > 12: list_embed.add_field(name="Roles 2", value=temp2)

  await interaction.response.send_message(embed=list_embed)


class ask_view(discord.ui.View):

  @discord.ui.button(label="Buy", style=discord.ButtonStyle.success)
  async def ask_callback(self, interaction: discord.Interaction,
                         button: discord.ui.Button):
    button.disabled = True

    author_id = str(interaction.user.id)

    # TEST IF BUTTON PRESS DONE BY COMMAND ISSUER
    if interaction.message.interaction.user != interaction.user:

      wrong_embed = discord.Embed(
        title="Incorrect User!",
        description=
        "You are not the user that issued this command, please run the command yourself if you wish to purchase a role!",
        color=0xd64836)
      await interaction.response.send_message(embed=wrong_embed,
                                              ephemeral=True)

    else:

      # GET REQUESTED ROLE INFO
      desired_role = discord.utils.get(interaction.guild.roles,
                                       id=inventory[author_id]['desired_role'])
      role_name = desired_role.name
      role_lower = role_name.lower()

      # GET GOLD INFO
      user_gold = profile[author_id]['gold']
      role_cost = roles['roles'][role_lower]['cost']

      print(f"User gold: {user_gold} | Role cost: {role_cost}")

      # TEST IF USER HAS ENOUGH GOLD
      if not user_gold >= int(role_cost):

        gold_embed = discord.Embed(
          title="Not Enough Gold!",
          description=
          f"You do not have enough gold to purchase the role: **{role_name}**",
          color=0xd64836,
          timestamp=interaction.created_at)

        gold_embed.set_author(name=f"Role Shop - {interaction.user}",
                              icon_url=interaction.user.avatar)

        gold_embed.add_field(
          name="Your Gold",
          value=f"{user_gold} <:gold_coin:957561865603543040>")
        gold_embed.add_field(
          name="Required Gold",
          value=f"{role_cost} <:gold_coin:957561865603543040>")

        await interaction.response.edit_message(embed=gold_embed, view=None)

      else:

        # SUCCESSFULLY PURCHASE ROLE
        inventory[author_id]['owned_roles'][role_lower] = True
        inventory[author_id]['desired_role'] = 0

        profile[author_id]['gold'] = user_gold - int(role_cost)

        success_embed = discord.Embed(
          title="Role Purchase Successfull",
          description=
          f"You have successfully purchased the role: **{role_name}**",
          color=desired_role.color,
          timestamp=interaction.created_at)

        success_embed.set_author(name=f"Role Shop - {interaction.user}",
                                 icon_url=interaction.user.avatar)

        await interaction.response.edit_message(embed=success_embed, view=None)

        await save_inventory()
        await save_profile()


# BUY ROLE
@bot.tree.command(name="buyrole",
                  description="buy one of the available roles using gold")
async def buy_role(interaction: discord.Interaction, role: str):

  author_id = str(interaction.user.id)
  gold = profile[author_id]['gold']
  role_lower = role.lower()

  # ROLE DOESNT EXIST
  if not role_lower in roles['roles']:

    exist_embed = discord.Embed(
      title="Role Doesn't Exist!",
      description=
      "The role you are trying to purchase does not exist! Try checking the spelling and try again later!",
      color=0xd64836,
      timestamp=interaction.created_at)

    exist_embed.set_author(name=f"Role Shop - {interaction.user}",
                           icon_url=interaction.user.avatar)

    await interaction.response.send_message(embed=exist_embed, ephemeral=True)
    return

  # ROLE ALREADY OWNED
  if role_lower in inventory[author_id]['owned_roles']:
    owned_embed = discord.Embed(title="Role Already Owned!",
                                description="You already own this role!",
                                color=0xd64836,
                                timestamp=interaction.created_at)

    owned_embed.set_author(name=f"Role Shop - {interaction.user}",
                           icon_url=interaction.user.avatar)

    await interaction.response.send_message(embed=owned_embed, ephemeral=True)
    return

  # GET ROLE
  role_id = roles['roles'][role_lower]['id']

  desired_role = discord.utils.get(interaction.guild.roles, id=role_id)

  inventory[author_id]['desired_role'] = desired_role.id
  await save_inventory()

  # ASK EMBED
  ask_embed = discord.Embed(
    title="Do you want to buy this role?",
    description=f"Would you like to buy the role: **{desired_role}?**",
    color=desired_role.color,
    timestamp=interaction.created_at)

  ask_embed.add_field(
    name="Cost",
    value=f"{roles['roles'][role_lower]['cost']}<:gold_coin:957561865603543040>"
  )

  ask_embed.set_author(name=f"Role Shop - {interaction.user}",
                       icon_url=interaction.user.avatar)

  message = await interaction.response.send_message(embed=ask_embed,
                                                    view=ask_view())


# LIST ROLES
@bot.tree.command(name="roleinv",
                  description="view the roles that you currently own")
async def role_inv(interaction: discord.Interaction):

  guild = interaction.guild
  author_id = str(interaction.user.id)

  role_list = []

  # GET ROLES FROM JSON FILE AND ADD TO LIST
  for role in inventory[author_id]['owned_roles']:
    temp_role = discord.utils.get(interaction.guild.roles,
                                  id=roles['roles'][role]['id'])
    role_list.append(f"- {temp_role.mention}\n")

  # EMBED
  list_embed = discord.Embed(title="Role Inventory",
                             color=interaction.user.color,
                             timestamp=interaction.created_at)

  list_embed.set_author(name=f"Role Inventory - {interaction.user}",
                        icon_url=interaction.user.avatar)

  if len(role_list) <= 24:
      tempList1 = []
      tempList2 = []

      i = 0

      while i < len(role_list):
          if i <= 12:
            tempList1.append(role_list[i])
          else:
              tempList2.append(role_list[i])
          i += 1

      list_embed.add_field(name="Roles", value ="".join(tempList1))
      
      if len(role_list) >= 13:
          list_embed.add_field(name="Roles", value = "".join(tempList2))


  await interaction.response.send_message(embed=list_embed)

# EQUIP ROLE
@bot.tree.command(name="equiprole", description="equip a role that you own.")
async def equip_role(interaction: discord.Interaction, role: str):

  author_id = str(interaction.user.id)
  role_lower = role.lower()

  guild = interaction.guild

  # CHECK IF ROLE EXISTS
  if not role_lower in roles['roles']:

    exist_embed = discord.Embed(
      title="Role Doesn't Exist!",
      description=
      "The role you are trying to equip does not exist! Checking the spelling and try again later!",
      color=0xd64836,
      timestamp=interaction.created_at)

    exist_embed.set_author(name=f"Role Inventory - {interaction.user}",
                           icon_url=interaction.user.avatar)

    await interaction.response.send_message(embed=exist_embed)
    return

  # CHECK IF USER OWNS THE ROLE
  if not role_lower in inventory[author_id]['owned_roles']:

    owned_embed = discord.Embed(
      title="You do not own this role!",
      description=
      "The role you are to equip is not in your collection! Purchase the role and try again",
      color=0xd64836,
      timestamp=interaction.created_at)

    owned_embed.set_author(name=f"Role Inventory - {interaction.user}",
                           icon_url=interaction.user.avatar)

    await interaction.response.send_message(embed=owned_embed)
    return

  # GET DESIRED ROLE
  desired_role = discord.utils.get(guild.roles,
                                   id=roles['roles'][role_lower]['id'])

  # CHECK IF USER HAS A ROLE EQUIPPED --> EQUIPS ROLE
  if inventory[author_id]['equipped_role'] != "":

    equipped_role = inventory[author_id]['equipped_role']
    old_role_id = roles['roles'][equipped_role]['id']
    old_role = discord.utils.get(guild.roles, id=old_role_id)

    inventory[author_id]['equipped_role'] = role_lower
    await save_inventory()

    await interaction.user.remove_roles(old_role)
    await interaction.user.add_roles(desired_role)

    equip_embed = discord.Embed(
      title="Role Equipped!",
      description=f"You have equipped the role: **{desired_role.name}**",
      color=desired_role.color,
      timestamp=interaction.created_at)

    equip_embed.set_author(name=f"Role Inventory - {interaction.user}",
                           icon_url=interaction.user.avatar)

    await interaction.response.send_message(embed=equip_embed)

  else:

    inventory[author_id]['equipped_role'] = role_lower
    await save_inventory()

    await interaction.user.add_roles(desired_role)

    equip_embed = discord.Embed(
      title="Role Equipped!",
      description=f"You have equipped the role: **{desired_role.name}**",
      color=desired_role.color,
      timestamp=interaction.created_at)

    equip_embed.set_author(name=f"Role Inventory - {interaction.user}",
                           icon_url=interaction.user.avatar)

    await interaction.response.send_message(embed=equip_embed)


# DAILY
@bot.tree.command(name="daily", description="get some daily gold")
@app_commands.checks.cooldown(1, 86400, key=lambda i: (i.user.id))
async def daily(interaction: discord.Interaction):

  author_id = str(interaction.user.id)
  gold = profile[author_id]['gold']

  profile[author_id]['gold'] = gold + 50

  daily_embed = discord.Embed(
    title="Daily Gold Claimed!",
    description="You have claimed your free gold for the day!",
    color=interaction.user.color,
    timestamp=interaction.created_at)

  daily_embed.set_author(name=f"Daily Gold - {interaction.user}",
                         icon_url=interaction.user.avatar)

  daily_embed.add_field(
    name="New Balance",
    value=f"{profile[author_id]['gold']} <:gold_coin:957561865603543040>")

  daily_embed.set_footer(text="This command will now enter a 24 hour cooldown")

  await interaction.response.send_message(embed=daily_embed)
  await save_profile()


@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction,
                               error: app_commands.AppCommandError):
  if isinstance(error, app_commands.CommandOnCooldown):

    seconds = error.retry_after
    minutes = round(seconds / 60)
    hours = round(minutes / 60)
    print(error)

    message = ""

    if hours >= 1:
      message = f"This command is on cooldown! Please wait **{hours} hours**!"
    else:
      if hours < 1:
        message = f"This command is on cooldown! Please wait **{minutes} minutes**!"
      else:
        if minutes < 1:
          message = f"This command is on cooldown! Please wait **{seconds} seconds**!"

    return await interaction.response.send_message(message, ephemeral=True)


# COINFLIP
@bot.tree.command(name="coinflip",
                  description="flip a coin to try and double your bet.")
@app_commands.checks.cooldown(1, 300, key=lambda i: (i.user.id))
async def coin_flip(interaction: discord.Interaction, bet: int = None):

  author_id = str(interaction.user.id)
  gold = profile[author_id]['gold']

  # CHECK IF BET AMOUNT IS VALID
  if bet == None or bet <= 0 or bet > 250:

    invalid_embed = discord.Embed(
      title="Invalid Bet Amount",
      description=
      "The bet amount provide is invalid. Please make sure your bet is between 1 and 250 gold.",
      color=0xd6483,
      timestamp=interaction.created_at)

    invalid_embed.set_author(name=f"Coin Flip - {interaction.user}",
                             icon_url=interaction.user. display_avatar)

    return await interaction.response.send_message(embed=invalid_embed,
                                                   ephemeral=True)

  # CHECK IF USER HAS ENOUGH GOLD TO MAKE THE BET
  if not bet <= gold:

    poor_embed = discord.Embed(
      title="Not Enough Gold",
      description="You do not have enough gold to make a bet this high!",
      color=0xd6483,
      timestamp=interaction.created_at)

    poor_embed.set_author(name=f"Coin Flip - {interaction.user}",
                          icon_url=interaction.user.avatar)

    poor_embed.add_field(name="Your Gold",
                         value=f"{gold} <:gold_coin:957561865603543040>")

    await interaction.response.send_message(embed=poor_embed, ephemeral=True)
    return

  # FLIP COIN
  coin = randint(1, 2)

  # WIN
  if coin == 1:

    win_embed = discord.Embed(
      title="You Won the Coin Flip!",
      description="You have won the coin flip and have doubled your bet!",
      color=0x60de54,
      timestamp=interaction.created_at)

    win_embed.set_author(name=f"Coin Flip - {interaction.user}",
                         icon_url=interaction.user.avatar)

    win_embed.add_field(name="Winnings",
                        value=f"+{bet * 2} <:gold_coin:957561865603543040>")

    win_embed.add_field(name="New Balance",
                        value=f"{gold + bet} <:gold_coin:957561865603543040>")

    win_embed.set_footer(
      text="This command will now go on cooldown for 5 minutes.")

    await interaction.response.send_message(embed=win_embed)

    profile[author_id]['gold'] = gold + bet

    await save_profile()

  # LOSE
  else:

    lose_embed = discord.Embed(
      title="You Lost the Coin Flip!",
      description="You have lost the coin flip and have lost your bet!",
      color=0xd64836,
      timestamp=interaction.created_at)

    lose_embed.set_author(name=f"Coin Flip - {interaction.user}",
                          icon_url=interaction.user.avatar)

    lose_embed.add_field(name="Winnings",
                         value=f"-{bet} <:gold_coin:957561865603543040>")

    lose_embed.add_field(name="New Balance",
                         value=f"{gold - bet} <:gold_coin:957561865603543040>")

    lose_embed.set_footer(
      text="This command will now go on cooldown for 5 minutes.")

    await interaction.response.send_message(embed=lose_embed)

    profile[author_id]['gold'] = gold - bet

    await save_profile()

# LIMBUS COIN

@bot.tree.command(name="limbuscoin", description="-45 sanity")
@app_commands.checks.cooldown(1, 300, key=lambda i: (i.user.id))
async def limbuscoin(interaction: discord.Interaction, bet: int = None):

  author_id = str(interaction.user.id)
  gold = profile[author_id]['gold']

  # CHECK IF BET AMOUNT IS VALID
  if bet <= 0 or bet > 250 or bet == None:

    invalid_embed = discord.Embed(
      title="Invalid Bet Amount",
      description=
      "The bet amount provide is invalid. Please make sure your bet is between 1 and 250 gold.",
      color=0xd6483,
      timestamp=interaction.created_at)

    invalid_embed.set_author(name=f"LIMBUS COMPANYYYYY - {interaction.user}",
                             icon_url=interaction.avatar)

    return await interaction.response.send_message(embed=invalid_embed,
                                                   ephemeral=True)

  # CHECK IF USER HAS ENOUGH GOLD TO MAKE THE BET
  if not bet <= gold:

    poor_embed = discord.Embed(
      title="Not Enough Gold",
      description="You do not have enough gold to make a bet this high!",
      color=0xd6483,
      timestamp=interaction.created_at)

    poor_embed.set_author(name=f"LIMBUS COMPANYYYYY - {interaction.user}",
                          icon_url=interaction.user.avatar)

    poor_embed.add_field(name="Your Gold",
                         value=f"{gold} <:gold_coin:957561865603543040>")

    await interaction.response.send_message(embed=poor_embed, ephemeral=True)
    return

  # FLIP COIN
  coin = randint(1, 100)

  # WIN
  if coin <= 5:

    win_embed = discord.Embed(title="Ding!",
                              color=0x60de54,
                              timestamp=interaction.created_at)

    win_embed.set_author(name=f"LIMBUS COMPANYYYYY - {interaction.user}",
                         icon_url=interaction.user.avatar)

    win_embed.add_field(name="Winnings",
                        value=f"+{bet * 10} <:gold_coin:957561865603543040>")

    win_embed.add_field(
      name="New Balance",
      value=f"{gold + (bet * 10)} <:gold_coin:957561865603543040>")

    win_embed.set_footer(
      text="This command will now go on cooldown for 5 minutes.")

    await interaction.response.send_message(embed=win_embed)

    profile[author_id]['gold'] = gold + (bet * 10)

    await save_profile()

  # LOSE
  else:

    lose_embed = discord.Embed(title="*Glass breaking.mp3*",
                               color=0xd64836,
                               timestamp=interaction.created_at)

    lose_embed.set_author(name=f"LIMBUS COMPANYYYYY - {interaction.user}",
                          icon_url=interaction.user.avatar)

    lose_embed.add_field(name="Winnings",
                         value=f"-{bet} <:gold_coin:957561865603543040>")

    lose_embed.add_field(name="New Balance",
                         value=f"{gold - bet} <:gold_coin:957561865603543040>")

    lose_embed.set_footer(
      text="This command will now go on cooldown for 5 minutes.")

    await interaction.response.send_message(embed=lose_embed)

    profile[author_id]['gold'] = gold - bet

    await save_profile()


# LEADERBOARD
@bot.tree.command(name="leaderboard",
                  description="Shows the top 5 richest users")
async def leaderboard(interaction: discord.Interaction):

  author_id = str(interaction.user.id)

  users = {}
  leaderboard = []
  temp = [None] * 2 

  # GET ALL REGISTERED USERS AND THEIR GOLD AMOUNT
  for user in profile:
    temp = [None] * 2       
    id = int(user)
    gold = profile[user]['gold']
    users[gold] = {}
    users[gold][id] = ""
    temp[0] = id
    temp[1] = gold
    leaderboard.append(temp)
    print(temp)

  leaderboard.sort(key=lambda x: x[1], reverse = True)
  print(leaderboard)

  msg = []
  index = 1

  # GET TOP 5 AND ADD TO MSG ARRAY
  while index <= 5:
      user = bot.get_user(leaderboard[index - 1][0])
      msg.append(f"{index}. {user.mention} - [ {leaderboard[index-1][1]}<:gold_coin:957561865603543040> ]\n")



      index += 1


  # EMBED
  leaderboard_embed = discord.Embed(
    title="Gold Leaderboard",
    description="The top 5 richest users in the server are...",
    color=interaction.user.color,
    timestamp=interaction.created_at)

  leaderboard_embed.set_author(name=f"Gold Leaderboard - {interaction.user}",
                               icon_url=interaction.user.avatar)

  leaderboard_embed.add_field(name="Current Leaders", value="".join(msg))

  await interaction.response.send_message(embed=leaderboard_embed)


bot.run(TOKEN)

