"""
Name: Victoria Lee, based on work from Amy Fung & Cynthia Wang & Sofia Kobayashi & Helen Mao
Date: 03/09/2025
Description: The main Slack bot logic for the food delivery data collection project
"""

import os
from pathlib import Path
from dotenv import load_dotenv
env_path = Path('..') / '.env'
load_dotenv(dotenv_path=env_path)

import messenger

import json
import requests
import copy
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_bolt.adapter.flask import SlackRequestHandler
from datetime import date, datetime
import random


### ### CONSTANTS ### ###
DB_NAME = os.environ['DB_NAME']

EMOJI_DICT = {0: '🪴', 
                1: '🌺', 
                2: '🍀', 
                3: '✨',
                4: '🐨', 
                5: '🐶',
                6: '🐱',
                7: '🦔',
                8: '🐱',
                9: '🪴', 
}


## ### LOAD IN MESSAGE BLOCKS ### ###
# with open('block_messages/default_btn.json', 'r') as infile:
#     default_btn = json.load(infile)

# with open('block_messages/help_block.json', 'r') as infile:
#     info_page = json.load(infile)

with open('block_messages/sample_task.json', 'r') as infile: # TODO: renew sample task
    sample_task = json.load(infile)

# with open('block_messages/onboarding_block.json', 'r') as infile:
#     onboarding = json.load(infile)

with open('block_messages/headers.json', 'r') as infile:
    block_headers = json.load(infile)

with open('block_messages/task_channel_welcome_message.json', 'r') as infile:
    task_channel_welcome_message = json.load(infile) # TODO: modify task channel welcome message

with open('block_messages/task_channel_created_confirmation.json', 'r') as infile:
    task_channel_created_confirmation = json.load(infile)

with open('block_messages/main_channel_welcome_message.json', 'r') as infile:
    main_channel_welcome_message = json.load(infile) # TODO: modify task channel welcome message

### ### INITIALIZE BOLT APP ### ###
# Initialize app, socket mode handler, & client 
app = App(token= os.environ['TASK_BOT_TOKEN'])
handler = SlackRequestHandler(app)
client = WebClient(token=os.environ['TASK_BOT_TOKEN'])

# Get the bot id
BOT_ID = client.api_call("auth.test")['user_id']



### ### HELPER FUNCTIONS ### ####
def send_messages(user_id, block = None, text = None):
    client.chat_postMessage(channel=f"@{user_id}", blocks = block, text=text)
    return

def send_welcome_message(users_list) -> None:
    '''
    Takes   A list containing all user ids or a dictionary with user ids as its keys. 
            currently using users_store returned by get_all_users_info()
    Sends welcoming message to all users
    '''
    active_users = messenger.get_active_users_list()
    for user_id in users_list:
        if BOT_ID != user_id and user_id in active_users:      
            try:
                print(f'IN Welcome: {user_id}', datetime.now())
                client.chat_postMessage(channel=f"@{user_id}", blocks = main_channel_welcome_message['blocks'], text="Welcome to Snack N Go!")
                print("Welcome!")
            except SlackApiError as e:
                assert e.response["ok"] is False and e.response["error"], f"Got an error: {e.response['error']}"
    # active_users = messenger.get_active_users_list()
    # for user_id in users_list:
    #     if BOT_ID != user_id and user_id in active_users:      
    #         try:
    #             print(f'IN Welcome: {user_id}', datetime.now())
    #             client.chat_postMessage(channel=f"@{user_id}", blocks = onboarding['blocks'], text="Welcome to Snap N Go!")
    #             print("Welcome!")
    #         except SlackApiError as e:
    #             assert e.response["ok"] is False and e.response["error"], f"Got an error: {e.response['error']}"

def create_task_channel(user_id, task_id):
    """
    Helper function for handle_begin_task() in bot.py
    Creates a new private channel for a task (an order submission) and invites the user asked for submitting a new order.
    """
    try:
        # create a new private channel
        channel_name = f"order-upload-{task_id}" # TODO: change to a better name
        response = client.conversations_create(
            name=channel_name, 
            is_private=True
        )
        channel_id = response["channel"]["id"]

        # invite the user to the channel
        client.conversations_invite(channel=channel_id, users=[user_id])

        return channel_id
    except SlackApiError as e:
        print(f"Error creating channel: {e.response['error']}")
        return None

def get_all_users_info() -> dict:
    '''
    Helper function to get all users info from slack
    Takes a users array we get from slack which is a SlackResponse object type
    Returns a dict type containing same info with user id as key
    '''
    # Get users list (requires the users:read scope)
    result = client.users_list()

    # Get all user info in result
    users_array = result["members"]
    users_store = {}

    # Turn the SlackResponse object type into dict type
    for user in users_array:
        if user['deleted'] == False:
            # Key user info on their unique user ID
            user_id = user["id"]
            # Store the entire user object (you may not need all of the info)
            users_store[user_id] = user
    
    return users_store

def create_order_task(user_id):
    """
    Create a new order upload task in the database.
    Return a task_id corresponding to the task_id in the database. 
    # TODO: Implementation when database ready
    """
    task_id = int(datetime.now().timestamp()) # WARNING: This is temproary!! # TODO: revise when database ready
    return task_id

### ### MESSAGE HANDLERS ### ###
@app.message()
def handle_message(payload, say):
    """
    Takes the response from a message sent in any chat in which this Bot has
        access to.
    When on, constantly listens for new messages, the responds as dictated below.
    Returns nothing.
    """
    channel_id = payload.get('channel')
    user_id = payload.get('user')
    text = payload.get('text')

    print("- Message sent", user_id, text, datetime.now())
    # Handle certain responses
    if BOT_ID != user_id:
        if 'files' not in payload:
            """
            User sends a text without any image
            """
            # User needs help
            if text.strip() == "?" or text.strip().lower() == 'help': # TODO: make a help thing later, check original code for reference
                say("im too lazy to help")
            # User want account summary
            elif text.strip().lower() == "account": # TODO: make an account summary, check original code for reference
                say("im too lazy to give any account info")
            elif text.strip().lower() == "report": # TODO: make report avialable, check original code for reference
                say("don't report")
            else:
                say(sample_task)
        else:
            # User attaches more than one image
            print("text+file", datetime.now())
            print(payload)
            if len(payload['files']) > 1: 
                say("*:large_orange_circle: You are attaching more than one file.* Reply `?` for more information.")
                return

            # User attaches a file that is not an image
            file = payload['files'][0]
            if "image" not in file['mimetype']: 
                say("*:large_orange_circle: The file you attached is not an image.*\n Reply `?` for more information.")
                return
            task_id = payload['blocks'][0]['elements'][0]['elements'][0]['text']
            print("TASK ID:", task_id)
            if not task_id.isdigit():
                say(":large_orange_circle: Please include *only the task number* in the text & attach that tasks's image.")
                return
            task_id = int(task_id)
            accepted_tasks = messenger.get_accepted_tasks(user_id)
            pending_tasks = messenger.get_pending_tasks(user_id)
            # The text the user enters isn't any of their assigned task numbers
            if messenger.check_time_window(task_id) == "expired":
                say(f''':large_orange_circle: Task {task_id} has already expired. Please pick another assigned task to finish.''')
            elif messenger.check_time_window(task_id) == "not started":
                say(f''':large_orange_circle: Task {task_id} has not started yet. Please check the start time & time window and finish this task later.''')
            elif task_id not in accepted_tasks: 
                say(f":large_orange_circle: Task {task_id} is not one of your unfinished, accepted tasks. Your unfinished, accepted tasks are {accepted_tasks}")
                if task_id in pending_tasks:
                    say(f'''However, task {task_id} is one of your pending tasks. You can still complete the task by pressing the Accept button for task {task_id} and then submit your picture.''')
                return
            else:
                print("submitted")
                url = file['url_private_download']
                path = get_pic(url, os.environ['TASK_BOT_TOKEN'], user_id, task_id)
                if messenger.submit_task(user_id, task_id, path):
                    messenger.update_reliability(user_id)
                    say(f"We received your submission to task {task_id}. Your compensation will be secured once we checked your submission. Reply `account` for more information on your account and completed tasks.")
            #update database if image is NULL
        return #needs to be changed

### ### INTERACTION HANDLERS ### ###
@app.event("message")
def handle_message_events(body, logger, say):
    '''
    When user only send a picture without text
    '''
    logger.info(body)
    user = body['event']['user']
    say(sample_task)

@app.event("file_shared")
def handle_file_shared_events():
    '''
    Don't need this. Just added it so we don't get warning messages from it.
    '''
    return

@app.event("team_join")
def handle_team_join(body, logger, say):
    logger.info("Team join event received!")
    logger.info(body)  # Log the entire payload for debugging
    user_store = get_all_users_info()
    messenger.add_users(user_store)
    user_id = body["event"]["user"]["id"]
    send_welcome_message([user_id])

@app.action("bugs_form")
def handle_some_action(ack, body, logger):
    ack()
    logger.info(body)

@app.action("start_order_submission")
def handle_start_order_submission(ack, body, say):
    """
    Handles the 'Let me submit my order' button in the main channel Welcome message. 
    Create a new order upload task in the database and a dedicated Slack channel for this order.
    TODO: send everything to the database
    TODO: tell amelia that we need a new db column "channel_id" associated with a task
    """
    # Acknowledge the command
    ack()
    # get this user's info
    user_id = str(body["user"]["id"])
    # create a new task in the database 
    task_id = create_order_task(user_id)
    # create a new channel for this order 
    channel_id = create_task_channel(user_id, task_id)
    # sends a welcome message in the task channel
    client.chat_postMessage(channel=channel_id, blocks=task_channel_welcome_message["blocks"])
    # sends a confirmation message in the main channel
    confirmation_message = task_channel_created_confirmation.copy()
    confirmation_message["blocks"][0]["text"]["text"] = confirmation_message["blocks"][0]["text"]["text"].replace("PLACEHOLDER_CHANNEL_NAME", f"order-upload-{task_id}") # TODO: change the channel name when channel name in create_task_channel() changed
    say(confirmation_message)

@app.action("check_account_status")
def handle_check_account_status(ack, body, say):
    """
    Handles the "Check Account Status" button in the main channel Welcome Message.
    Gives user back with their current info such as total compensation, order submission
    history/status, etc. # TODO: revise
    # TODO: implementation
    """
    # Acknowledge the button click
    ack()
    # get the user's ID
    user_id = body["user"]["id"]
    
    say(f"yay nothing ready yet")

if __name__ == "__main__":
    # TODO? Figure out how 
    user_store = get_all_users_info()
    messenger.add_users(user_store)
    send_welcome_message(user_store.keys())
    # Start bolt socket handler
    SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()

# def send_tasks(assignments_dict) -> None:
#     '''
#     * Message users to give them new tasks *
#     Takes the assignments dictionary generated by getAssignments() in messenger
#     Format the tasks each user get into block messages. Send them to each 
#         user respectively
#     Returns nothing
#     ''' 
#     active_users = messenger.get_active_users_list()
#     for user_id in assignments_dict:
#         print(f'IN SEND TASKS: {user_id}', datetime.now())
#         if BOT_ID != user_id and user_id in active_users:   
#             try:
#                 for task_info in assignments_dict[user_id]:
#                     block = generate_message(task_info, user_id)
#                     #texts = "Here are your newly generated tasks"
#                     client.chat_postMessage(channel=f"@{user_id}", blocks = block,text="Sending tasks!")
#                     print("Send task!")
#             except SlackApiError as e:
#                 assert e.response["ok"] is False and e.response["error"], f"Got an error: {e.response['error']}"


# def generate_message(task_info, user_id):
#     '''
#     Helper function for sendTasks.
#     Get the list of task assigned to a user and format them into a 
#     json block message.
#     Return the block message
#     '''
#     block = []
#     starttime_format = task_info[4].strftime("%A (%m/%d) at %I:%M%p")
#     # text = (f"*Task # {task_info[0]}*,Location: {task_info[2]} \n" + 
#     #         f"Description: {task_info[3]}\nStart Time: {starttime_format} \n" + 
#     #         f"Window: {task_info[5]} minutes \nCompensation: {task_info[6]}")
    

#     text = (f"PLACEHOLDER_EMOJI *Task #PLACEHOLDER_TASKID* PLACEHOLDER_EMOJI \n*Description:* PLACEHOLDER_DESCRIPTION. \n*Start Time:* PLACEHOLDER_STARTTIME \n*Window:* PLACEHOLDER_WINDOW minutes \n*Compensation:* PLACEHOLDER_COMPENSATION")\
#                 .replace('PLACEHOLDER_EMOJI', EMOJI_DICT[int(str(task_info[0])[-1])]) \
#                 .replace('PLACEHOLDER_TASKID', str(task_info[0])) \
#                 .replace('PLACEHOLDER_DESCRIPTION', str(task_info[3])) \
#                 .replace('PLACEHOLDER_STARTTIME', str(starttime_format)) \
#                 .replace('PLACEHOLDER_WINDOW', str(task_info[5])) \
#                 .replace('PLACEHOLDER_COMPENSATION', str(task_info[6])) 

#     description = {
#                 "type": "section",
#                 "text": {
#                     "type": "mrkdwn",
#                     "text": text
#                 }
#     }
#     buttons = button_color(task_info[0], user_id)
#     block.append(description)
#     block.append(buttons)
#     return block


# def compact_task(task_info) -> dict:
#     """
#     Takes a task_info list.
#     Formats that task info into a compact task block (for uses outside 
#         of when a task is first send to a user).
#     Returns a fully formed 'section' Slack block (dict).
#     """
#     starttime_format = task_info[4].strftime("%A (%m/%d) at %I:%M%p")
#     text  = "*Task #PLACEHOLDER_TASKID* (*comp:* PLACEHOLDER_COMPENSATION)\n *Starts:* PLACEHOLDER_STARTTIME, *window*: PLACEHOLDER_WINDOW min \n*Description:* PLACEHOLDER_DESCRIPTION." \
#                 .replace('PLACEHOLDER_TASKID', str(task_info[0])) \
#                 .replace('PLACEHOLDER_DESCRIPTION', str(task_info[3])) \
#                 .replace('PLACEHOLDER_STARTTIME', str(starttime_format)) \
#                 .replace('PLACEHOLDER_WINDOW', str(task_info[5])) \
#                 .replace('PLACEHOLDER_COMPENSATION', str(task_info[6])) 
#     return {
# 			"type": "section",
# 			"text": {
# 				"type": "mrkdwn",
# 				"text": text
# 			}
# 		}
    
# def make_report_block(user_id) -> list:
#     """
#     Takes a user id (int? str?)
#     Formats a report block for the given user using their 
#         active (accepted, unexpired, uncompleted) & 
#         pending (pending, unexpired) tasks.
#     Returns a full formatted Slack block message (dict).
    
#     """
#     # A list of task_list lists for all accepted, unexpired, uncompleted tasks
#     active_ids = messenger.get_accepted_tasks(user_id)
#     all_active = [messenger.get_task_list(user_id, task_id) for task_id in active_ids]
  
#     # A list of task_list lists for all pending & unexpired tasks
#     pending_ids = messenger.get_pending_tasks(user_id)

#     # Add appropriate active task information
#     blocks = []
#     if all_active:
#         if len(blocks) >= 46:
#                 blocks.append(block_headers['too_many_pending_header'])
#         blocks.append(block_headers['active_header'])
#         blocks.append(block_headers['divider'])
        
#         # Sort active tasks by start time
#         sorted_active = sorted(all_active, key=lambda task_list: task_list[4]) 
#         for task_list in sorted_active:
#             active_task = compact_task(task_list)
#             blocks.append(active_task)
#     else:
#         blocks.append(block_headers['no_active_header'])

#     blocks.append(block_headers['divider'])
    
#     # Add appropriate pending task information
#     if pending_ids:
#         blocks.append(block_headers['pending_header'])
#     else:
#         blocks.append(block_headers['no_pending_header'])

#     # # Add 'for more info' ending
#     # blocks.append(block_headers['divider'])
#     # blocks.append(block_headers['ending_block'])

#     return blocks


# def button_color(task_id, user_id):
#     """
#     Takes a task id (int) and user id (str).
#     Determines button formatting based on assignment status 
#     Returns button block.
#     """
#     status = messenger.get_assign_status(task_id, user_id)
#     if status == "rejected": # Reject btn is red
#         block = copy.deepcopy(default_btn)
#         block['elements'][1]['style'] = 'danger'
#         block['block_id'] = str(task_id)
#     elif status == "accepted": # Accept btn is green
#         block = copy.deepcopy(default_btn)
#         block['elements'][0]['style'] = 'primary'
#         block['block_id'] = str(task_id)
#     else: # both buttons grey
#         block = copy.deepcopy(default_btn)
#         block['block_id'] = str(task_id)
#     return block

# def get_pic(url, token, user_id, task_id):
#     '''
#     Takes   url: from payload['event']['files'][0]['url_private_download']
#             token: the bot token
#             user_id: the user who sent the picture
#             task_id: the task they are trying to finish, should be payload['event']['text']
#     Downloads picture with the given download url and saves it in the given path
#     '''
#     r = requests.get(url, headers={'Authorization': 'Bearer %s' % token})
#     datetime = date.today() # change to clock
#     filename = f"../../snapngo_pics/{user_id}_{task_id}_{datetime}.jpeg"
#     open(filename, 'wb').write(r.content)
#     return filename

# def handle_message(payload, say):
#     """
#     Takes the response from a message sent in any chat in which this Bot has
#         access to.
#     When on, constantly listens for new messages, the responds as dictated below.
#     Returns nothing.
#     """
#     channel_id = payload.get('channel')
#     user_id = payload.get('user')
#     text = payload.get('text')

#     print("- Message sent", user_id, text, datetime.now())
#     Handle certain responses
#     if BOT_ID != user_id:
#         if 'files' not in payload:
#             if text.strip() == "?" or text.strip().lower() == 'help':
#                 say(info_page)
#             User only sends text without attaching an image
#             elif text.strip().lower() == "account":
#                 send_messages(user_id, generate_account_summary_block(user_id), "") 
#             elif text.strip().lower() == "report":
#                 active_block = make_report_block(user_id) 
#                 end_block = [block_headers['divider'], block_headers['ending_block']]
#                 client.chat_postMessage(channel=f"@{user_id}", blocks = active_block,text="")

#                  # Sort pending tasks by start time
#                 pending_ids = messenger.get_pending_tasks(user_id)
#                 all_pending = [messenger.get_task_list(user_id, task_id) for task_id in pending_ids]
#                 sorted_pending = sorted(all_pending, key=lambda task_list: task_list[4])
#                 for task_list in sorted_pending:
#                     pending_task = compact_task(task_list) 
#                     buttons = copy.deepcopy(default_btn)
#                     buttons['block_id'] = str(task_list[0])
#                     blocks = [pending_task, buttons]

#                     client.chat_postMessage(channel=f"@{user_id}", blocks = blocks, text="")

#                 client.chat_postMessage(channel=f"@{user_id}", blocks = end_block,text="")
#             elif text.strip().lower() == "opt in":
#                 messenger.update_account_status(user_id, "active")
#                 say("You have opted in for the day.")
#             elif text.strip().lower() == "opt out":
#                 messenger.update_account_status(user_id, "inactive")
#                 say("You have opted out for the day.")
#             else:
#                 say(sample_task)
#         else:
#             # User attaches more than one image
#             print("text+file", datetime.now())
#             print(payload)
#             if len(payload['files']) > 1: 
#                 say("*:large_orange_circle: You are attaching more than one file.* Reply `?` for more information.")
#                 return

#             # User attaches a file that is not an image
#             file = payload['files'][0]
#             if "image" not in file['mimetype']: 
#                 say("*:large_orange_circle: The file you attached is not an image.*\n Reply `?` for more information.")
#                 return
#             task_id = payload['blocks'][0]['elements'][0]['elements'][0]['text']
#             print("TASK ID:", task_id)
#             if not task_id.isdigit():
#                 say(":large_orange_circle: Please include *only the task number* in the text & attach that tasks's image.")
#                 return
#             task_id = int(task_id)
#             accepted_tasks = messenger.get_accepted_tasks(user_id)
#             pending_tasks = messenger.get_pending_tasks(user_id)
#             # The text the user enters isn't any of their assigned task numbers
#             if messenger.check_time_window(task_id) == "expired":
#                 say(f''':large_orange_circle: Task {task_id} has already expired. Please pick another assigned task to finish.''')
#             elif messenger.check_time_window(task_id) == "not started":
#                 say(f''':large_orange_circle: Task {task_id} has not started yet. Please check the start time & time window and finish this task later.''')
#             elif task_id not in accepted_tasks: 
#                 say(f":large_orange_circle: Task {task_id} is not one of your unfinished, accepted tasks. Your unfinished, accepted tasks are {accepted_tasks}")
#                 if task_id in pending_tasks:
#                     say(f'''However, task {task_id} is one of your pending tasks. You can still complete the task by pressing the Accept button for task {task_id} and then submit your picture.''')
#                 return
#             else:
#                 print("submitted")
#                 url = file['url_private_download']
#                 path = get_pic(url, os.environ['TASK_BOT_TOKEN'], user_id, task_id)
#                 if messenger.submit_task(user_id, task_id, path):
#                     messenger.update_reliability(user_id)
#                     say(f"We received your submission to task {task_id}. Your compensation will be secured once we checked your submission. Reply `account` for more information on your account and completed tasks.")
#             #update database if image is NULL
#         return #needs to be changed

# def check_all_assignments():
#     messenger.check_all_assignments()
    
#     for user_id in messenger.get_active_users_list():
#         block = [{
#         "type": "section",
#         "text": {
#             "type": "mrkdwn",
#             "text": "✨*Your Daily Summary*✨"
#         }
#         }]
#         block += generate_account_summary_block(user_id)
#         #send account summary
#         send_messages(user_id, block, "")
#     return
    
# def generate_account_summary_block(user_id):
#     compensation, tasks = messenger.get_account_info(user_id)
#     text = f"All completed tasks: {tasks}\nTotal compensation: {compensation} points"
#     summary = [{
#         "type": "section",
#         "text": {
#             "type": "mrkdwn",
#             "text": text
#         }
#     }]
#     return summary



### ### INTERACTION HANDLERS ### ###
# @app.action("accepted")
# def action_button_click(body, ack, say):
#     '''
#     body['actions'][0]   {'value': 'accepted', 'block_id': '1', 'type': 'button', 'action_id': 'accepted', 'text':...}
#     '''
#     # Acknowledge the action
#     ack()
#     messenger.update_tasks_expired()
#     action = body['actions'][0]
#     new_status = action['value']
#     task = int(action['block_id'])
#     user = str(body['user']['id'])
#     task_list = messenger.get_task_list(user, task)
#     old_status = messenger.get_assign_status(task, user)
#     if messenger.check_time_window(task) == "expired":
#         say(f''':large_orange_circle: Task {task} has already expired. Please pick another assigned task to finish.''')
#         return
#     if old_status == "pending":
#         messenger.update_assign_status(new_status, task, user)
#         # task_list = messenger.get
#         message = generate_message(task_list, user) 
#         client.chat_update(channel=body["channel"]["id"], ts = body["message"]["ts"], blocks = message,text="Accepted!")
#         say(f"You {new_status} task {task}")
#     else:
#         say(f"You already {old_status} task {task}")
#     return
    

# @app.action("rejected")
# def action_button_click(body, ack, say):
#     # Acknowledge the action
#     ack()

#     # Get task info 
#     messenger.update_tasks_expired()
#     action = body['actions'][0]
#     new_status = action['value']
#     task = int(action['block_id'])
#     user = str(body['user']['id'])
#     task_list = messenger.get_task_list(user, task)
#     old_status = messenger.get_assign_status(task, user)
#     if messenger.check_time_window(task) == "expired":
#         say(f''':large_orange_circle: Task {task} has already expired.''')
#         return
#     # Change 
#     if old_status == "pending":
#         messenger.update_assign_status(new_status, task, user)
#         # task_list = messenger.get
#         message = generate_message(task_list, user)
#         client.chat_update(channel=body["channel"]["id"], ts = body["message"]["ts"], blocks = message,text="Rejected!")
#         compensation = round(random.randint(10, 30)/100, 2)
#         messenger.add_account_compensation(user, compensation)
#         say(f"You {new_status} task {task}.\nA compensation of {compensation} points is added to your account. Reply `account` to see your account status.")
#     else:
#         say(f"You already {old_status} task {task}")
#     return