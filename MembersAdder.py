from telethon.sync import TelegramClient
from telethon.tl.functions.messages import GetDialogsRequest
from telethon.tl.types import InputPeerEmpty, InputPeerChannel, InputPeerUser
from telethon.errors.rpcerrorlist import PeerFloodError, UserPrivacyRestrictedError
from telethon.errors.rpcbaseerrors import BadRequestError
from telethon.tl.functions.channels import InviteToChannelRequest
import sys
import csv
import traceback
import time
import random
import os

api_id = 30812268
api_hash = 'b9c8c066e9bb7b8dc569e2cad0547bd8'
phone = '+51987323020'
client = TelegramClient(phone, api_id, api_hash)

FLOOD_ERROR_SLEEP = 18000  # 5 horas en segundos

client.connect()
if not client.is_user_authorized():
    client.send_code_request(phone)
    client.sign_in(phone, input('Enter the code: '))

users = []
csv_path = input("Enter CSV path (default: members.csv): ").strip() or "members.csv"

if not os.path.isfile(csv_path):
    sys.exit("CSV file not found: {}".format(csv_path))

with open(csv_path, encoding='UTF-8') as f:
    rows = csv.reader(f,delimiter=",",lineterminator="\n")
    next(rows, None)
    for row in rows:
        user = {}
        user['username'] = row[0]
        user['id'] = int(row[1])
        user['access_hash'] = int(row[2])
        user['name'] = row[3]
        users.append(user)

chats = []
last_date = None
chunk_size = 200
targets = []

result = client(GetDialogsRequest(
    offset_date=last_date,
    offset_id=0,
    offset_peer=InputPeerEmpty(),
    limit=chunk_size,
    hash=0
))
chats.extend(result.chats)

for chat in chats:
    try:
        if getattr(chat, 'megagroup', False) or getattr(chat, 'broadcast', False):
            targets.append(chat)
    except:
        continue

print('Choose a group/channel to add members:')
i = 0
for target in targets:
    target_type = 'Group' if getattr(target, 'megagroup', False) else 'Channel'
    print(str(i) + '- [{}] {}'.format(target_type, target.title))
    i += 1

g_index = input("Enter a Number: ")
target_group = targets[int(g_index)]

if getattr(target_group, 'broadcast', False) and not getattr(target_group, 'megagroup', False):
    sys.exit(
        "Selected target is a broadcast channel. Telegram often blocks direct member invites there. "
        "Choose a Group/Megagroup target instead."
    )

target_group_entity = InputPeerChannel(target_group.id, target_group.access_hash)

mode = int(input("Enter 1 to add by username or 2 to add by ID: "))

n = 0

for user in users:
    n += 1
    if n % 80 == 0:
        time.sleep(60)
    try:
        print("Adding {}".format(user['id']))
        if mode == 1:
            if user['username'] == "":
                continue
            user_to_add = client.get_input_entity(user['username'])
        elif mode == 2:
            user_to_add = InputPeerUser(user['id'], user['access_hash'])
        else:
            sys.exit("Invalid Mode Selected. Please Try Again.")
        client(InviteToChannelRequest(target_group_entity, [user_to_add]))
        print("Waiting for 60-180 Seconds...")
        time.sleep(random.randrange(0, 5))
    except PeerFloodError:
        print("Getting Flood Error from telegram. Script is stopping now. Please try again after some time.")
        print("Waiting 24 hours before retrying...")
        print("El script esperará 24 horas y volverá a intentar automáticamente.")
        time.sleep(FLOOD_ERROR_SLEEP)
        print("Reanudando después de 24 horas...")
        continue
    except UserPrivacyRestrictedError:
        print("The user's privacy settings do not allow you to do this. Skipping.")
        print("Waiting for 5 Seconds...")
        time.sleep(random.randrange(0, 5))
    except BadRequestError as e:
        if 'CHANNEL_MONOFORUM_UNSUPPORTED' in str(e):
            print("Target does not support InviteToChannelRequest (CHANNEL_MONOFORUM_UNSUPPORTED).")
            print("Use a Group/Megagroup as target, not this channel type.")
            break
        traceback.print_exc()
        print("BadRequestError")
        continue
    except:
        traceback.print_exc()
        print("Unexpected Error")
        continue
