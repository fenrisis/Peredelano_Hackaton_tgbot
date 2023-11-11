# Peredelano Hackaton tgbot
Peredelano Hackaton bot a telegram bot designed to manage hackathon participants, teams, projects, ideas and their interactions.

## File structure:
 -profile_handlers.py     # Contains classes for creating a member profile, a team profile and FSM states for making dynamic changes and handlers.
 
 -bot.py                  # Contains classes for inviting  members in team and for remove,and FSM states for making dynamic changes and handlers.
 
 -db.py                   # Contains mysql connector & functions for inserting, updating, deleating and more.

 -mysqlqwery.txt          # Shows mysql database schema.

 -.env                    # Contains Telegram bot token.
 
 -config.py               # Contains a link to send updates using a webhook.
 
 -requirements.txt        # Contains a description of all the necessary libraries and their versions.

## Usage
 -start - start work
 -documentation - Documentation.
 -profile - Interaction with profile.
 -findteam - View existing teams.
 -team - Create a team for a hackathon.
 -editteam - Make changes to the team.
 -hireforteam - View member profiles.
 -invitetoteam - Invite a member to the team.
 -removefromteam -Remove a member from the team.
 -myteam - View current team composition.
 -leaveteam - Leave the team.
 -deleteteam - Disband a team.
        

