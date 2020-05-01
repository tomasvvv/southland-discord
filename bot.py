# bot.py 
# http://github.com/tomasvosylius/discord-bot
# using discord.py

import discord
import mysql.connector

general_channel_name = "pagrindinis"
token_file           = "token.txt"
server_name          = "Southland.lt"
samp_server_ip       = "samp.southland.lt:7777"
messages             = {
    # message used for DM when new user joins
    "verification_message" : 
        f"Sveikiname prisijungus prie {server_name}! :partying_face:\n"
        f"Jei negali rašyti žinučių Discord kanaluose, privalai patvirtinti savo telefono numerį."
        f"Norėdamas patvirtinti savo UCP vartotoją, užsiregistruok serveryje `{samp_server_ip}`\n"
        f"Žemiau paraťyk savo __žaidimo Vardą_Pavardę__ ir lauk **patvirtinimo**",
    "welcome_global" : 
        "Labas, __{0}__! :wave: :tada:\nSveikiname prisijungus prie {1} serverio!",
}

if __name__ == "__main__":

    def read_token():
        #  Function reads token from token.txt file in current directory
        with open("token.txt") as file:
            lines = file.readlines()
            return lines[0].strip()

    def get_channel_by_name(name):
        # Function returns channel if found by given name 
        for channel in client.get_all_channels():
            if name in channel.name:
                return channel
        return None


    if __name__ == "__main__":
        print("Starting bot.py!")

        token = read_token()
        print("Token was read succesfully!")

        client = discord.Client()
        print("Running the client now...")

        gen_channel = None # general channel
        bugs_channel = None # bugs-found channel

        @client.event 
        async def on_ready():
            gen_channel = get_channel_by_name(general_channel_name)
            if gen_channel == None:
                print("Error when looking for channel (general)")
            else:
                print("General channel was found")

        @client.event
        async def on_member_join(member):
            print(f"{str(member)} just joined the server.")
        
            if gen_channel != None:
                # send the message to general channel
                await greet_member(gen_channel, message.author)

            # message the user
            dm = await member.create_dm()
            if dm != None:
                await dm.send(messages['verification_message'])


        @client.event
        async def on_connect():
            print("Connected")

        @client.event 
        async def on_message(message):
            """
                Komandos
            """

            if message.author == client.user:
                return # ignore the bot itself

            if message.content.startswith("!greetme"):
                await greet_member(message.channel, message.author)
                # message.channel.send(messages["welcome_global"].format(message.author.display_name, server_name))

            if message.content.startswith("!dmme"):
                dm = await message.author.create_dm()
                await dm.send(messages['verification_message'])

            if message.content.startswith("!myid"):
                await message.channel.send(f"Tavo Discord ID yra {message.author.id}")

            if message.content.startswith("!checkuser"):
                roles = message.author.roles
                admin = False
                for role in roles:
                    if role.name == "Management":
                        admin = True
                        break
                        
                if admin:
                    if len(message.mentions) == 1 and message.mentions is not None:
                        check_user = message.mentions[0].id
                        if check_user is None:
                            await message.channel.send("Neteisingai nurodytas vartotojas")
                        else:
                            await show_user_data(message.channel, message.author, check_user)
                    else:
                        await message.channel.send("Nenurodytas vartotojas")

                else:
                    await message.channel.send(f"<@{message.author.id}>, nesi administratorius :x:")
                

            if message.content.startswith("!verify"):
                args = message.content.split()
                if len(args) != 2:
                    await message.channel.send(f"<@{member.id}>, neteisingai nurodei vartotojo vardą :x:")
                else:
                    await verify_member(message.channel, message.author, args)
                    
        """
            Funkcijos
        """
        async def greet_member(channel, member):
            await channel.send(messages["welcome_global"].format(member.display_name, server_name))

        async def show_user_data(channel, member, check_user):
            db = mysql_connect()
            if db is None:
                print("Error")
                return

            cur = db.cursor()
            sql = f"SELECT `Name`,`id`,`RegisterIp`,`RegisterDate` FROM `users_data` WHERE `DiscordUser`='{check_user}'"
            cur.execute(sql)
            row = cur.fetchone()
            if row is None:
                await channel.send(f"Discord narys <@{check_user}> nėra surišęs savo žaidimo vartotojo.")

            else:
                user_id = row[1]
                lpad =  """Discord narys <@{0}> yra patvirtinęs vartotoją **{1}** (ID: {2})```Registracijos IP: {3}\nRegistracijos data: {4}```""".format(
                    check_user,
                    row[0],
                    user_id,
                    hide_ip(row[2]),
                    row[3]
                )

                await show_game_accounts(lpad, channel, user_id)

            cur.close()
            db.close()

        async def show_game_accounts(lpad, channel, user_id):
            db = mysql_connect()
            if db is None:
                print("Error")
                return

            cur = db.cursor()
            sql = f"SELECT `Name`,`gpci` FROM `players_data` WHERE `UserId`='{user_id}'"
            cur.execute(sql)
            rows = cur.fetchall()
            if rows is None:
                await channel.send(f"Žaidėjas veikėjų neturi.")

            else:
                string = lpad;
                string += "Veikėjai:```"
                
                for row in rows:
                    string += f"{row[0]}, veikėjo GPCI: {row[1]}\n\n"

                string += "```"
                if len(string) > 0:
                    await channel.send(string)


            cur.close()
            db.close()

        async def verify_member(channel, member, args):
            """
                Userio patvirtinimas    
            """

            db = mysql_connect()
            if db is None:
                print("Error")
                return

            cur = db.cursor()
            args[1] = args[1].strip()

            sql = f"SELECT `Name` FROM `users_data` WHERE `DiscordUser`='{member.id}'"
            cur.execute(sql)
            row = cur.fetchone()
            if row is not None:
                await channel.send(f"<@{member.id}>, tavo Discord vartotojas jau surištas su žaidimo vartotoju `{row[0]}`. Šiame projekte gali turėti tik vieną žaidimo vartotoją ant to pačio Discord vartotojo :x:")

            else:
                sql = f"SELECT `id`,`DiscordVerified` FROM `users_data` WHERE `Name`='{args[1]}'" # WHERE `Name` = '%s'"
                cur.execute(sql) # , args[1]
                row = cur.fetchone()

                if row is None:
                    await channel.send(f"<@{member.id}>, vartotojas `{args[1]}` serveryje **neegzistuoja** :x:")
                else:
                    if row[1] >= 1:
                        await channel.send(f"<@{member.id}>, vartotojas `{args[1]}` jau yra **patvirtintas** :x:")
                    else:
                        cur.execute(f"UPDATE `users_data` SET `DiscordVerified`='1',`DiscordUser`='{member.id}' WHERE `id`='{row[0]}'")
                        db.commit()
                        
                        await channel.send(f"<@{member.id}> sėkmingai **patvirtinai** vartotoją `{args[1]}` :white_check_mark:")

            cur.close()
            db.close()

        def hide_ip(ip):
            if(len(ip)) <= 3:
                return ip

            last_dot = ip.rfind(".")
            returnal = ip[0:(last_dot+1)]
            returnal += "*"*(len(ip) - last_dot - 1)

            return returnal

        def mysql_connect():
            try:
                db = mysql.connector.connect(
                    host="localhost",
                    user="root",
                    passwd="",
                    database="southland"
                )
            except mysql.connector.Error as err:
                if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                    print("Something is wrong with your user name or password")
                elif err.errno == errorcode.ER_BAD_DB_ERROR:
                    print("Database does not exist")
                else:
                    print(err)
            else:
                print("Successfully connected to MySQL")
                return db

            return None

        client.run(token)
