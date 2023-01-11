import os
import sqlite3
from numpy import full, sin
import pandas as pd
from datetime import datetime


# Function to create a query string based on chat room ids
def getQueryString(chat_name):
    # Get chat ids based on chat name
    # Could be multiple!
    room_names = pd.read_sql_query('select chat_identifier from chat where display_name = ?', conn, params=(chat_name,))['chat_identifier']
    message_list = []
    for room_name in room_names:
        message = pd.read_sql_query('select ROWID, text from message where cache_roomnames = ? limit 1', conn, params=(room_name,))['ROWID']
        if (not message.empty):
            message = message[0]
            message_list.append(message)

    list_of_chat_ids = []
    for message in message_list:
        chat_id = pd.read_sql_query('select chat_id from chat_message_join where message_id = ?', conn, params=(str(message),))    
        list_of_chat_ids.append(chat_id['chat_id'][0])

    chat_id_query_string = 'chat_id=='
    for id in list_of_chat_ids:
        chat_id_query_string = chat_id_query_string + str(id) + ' | chat_id=='
    chat_id_query_string = chat_id_query_string[:len(chat_id_query_string)-12]
    return chat_id_query_string

home_path = os.path.expanduser('~')
conn = sqlite3.connect(home_path + '/Library/Messages/chat.db')
cur = conn.cursor()
cur.execute(" select name from sqlite_master where type = 'table' ")

##################################################################################################################################
############ https://github.com/yortos/imessage-analysis/blob/master/imessages-data-extract-and-prep.ipynb #######################
messages = pd.read_sql_query('''select *, datetime(date/1000000000 + strftime("%s", "2001-01-01") ,"unixepoch","localtime")  as date_utc from message''', conn) 

handles = pd.read_sql_query("select * from handle", conn)
chat_message_joins = pd.read_sql_query("select * from chat_message_join", conn)

# these fields are only for ease of datetime analysis (e.g., number of messages per month or year)
messages['message_date'] = messages['date']
messages['timestamp'] = messages['date_utc'].apply(lambda x: pd.Timestamp(x))
messages['date'] = messages['timestamp'].apply(lambda x: x.date())
messages['month'] = messages['timestamp'].apply(lambda x: int(x.month))
messages['year'] = messages['timestamp'].apply(lambda x: int(x.year))


# rename the ROWID into message_id, because that's what it is
messages.rename(columns={'ROWID' : 'message_id'}, inplace = True)

# rename appropriately the handle and apple_id/phone_number as well
handles.rename(columns={'id' : 'phone_number', 'ROWID': 'handle_id'}, inplace = True)

# merge the messages with the handles
merge_level_1 = pd.merge(messages[['text', 'handle_id', 'date','message_date' ,'timestamp', 'month','year','is_sent', 'message_id', 'guid', 'associated_message_guid', "is_from_me"]],  handles[['handle_id', 'phone_number']], on ='handle_id', how='left')

# and then that table with the chats
df_messages_all = pd.merge(merge_level_1, chat_message_joins[['chat_id', 'message_id']], on = 'message_id', how='left')
##################################################################################################################################

# Get chat name from user from console
# Easiest way to avoid mispelling, errors, etc. is to list chats 
# by most used to least, allowing user to pick one based on a #

# Get list of groupchats
group_chats = pd.read_sql_query('select distinct display_name from chat', conn)['display_name']
group_chat_list = group_chats.tolist()
group_chat_list.pop(0)
# How many messages in each groupchat
num_mes_dict = {}
for chat in group_chat_list:
    chat_id_query_string = getQueryString(chat)
    if (len(chat_id_query_string) > 9):
        temp_df = df_messages_all.query(chat_id_query_string)
        num_mes_dict[chat] = len(temp_df)

sorted_chats = sorted(num_mes_dict.items(), key=lambda x: x[1], reverse=True)

# Get user input for what group chat to analyze
# Use i to maintian what point in list
lower = 0
upper = 5
user_input = ''
while (user_input == ''):
    for i in range(lower, upper):
        if (i < len(sorted_chats) - 1):
            print(str(i + 1) + ". " + sorted_chats[i][0])
    user_input = input("Please type the # of the group chat you would like to analyze. (If you do not see it, please hit enter to see more): ")
    if (not user_input.isnumeric()):
        user_input = ''
        print("Please enter a number!")
    lower += 5
    upper += 5

user_input = int(user_input) - 1
group_chat = sorted_chats[user_input][0]


# Just specific gc
chat_id_query_string = getQueryString(group_chat)
df_messages = df_messages_all.query(chat_id_query_string)

message_attachement_join = pd.read_sql_query("select * from message_attachment_join", conn)

df_messages = pd.merge(df_messages, message_attachement_join[['message_id', 'attachment_id']], on = 'message_id', how='left')

print("Total messages analyzed: " + str(len(df_messages)))



# Get membership of given group message
membership = df_messages['phone_number'].unique().tolist()
# Remove any NaN values
membership = [x for x in membership if x == x]



###### This section creates a list of contacts ########
# find your address book and establish a connection
conn_address = sqlite3.connect(home_path + '/Library/Application Support/AddressBook/Sources/6A3869D0-3BC4-41E2-B14B-303DDD547254/AddressBook-v22.abcddb')
cur_address = conn_address.cursor()

# # query the database to get all the table names
cur_address.execute(" select name from sqlite_master where type = 'table' ")

# Query to find first and last name, phone number, and email address, 
contacts = pd.read_sql_query('SELECT ZABCDRECORD.ZFIRSTNAME, ZABCDRECORD.ZLASTNAME, ZABCDPHONENUMBER.ZFULLNUMBER, ZABCDEMAILADDRESS.ZADDRESS FROM ZABCDRECORD LEFT JOIN ZABCDPOSTALADDRESS ON ZABCDPOSTALADDRESS.ZOWNER = ZABCDRECORD.Z_PK LEFT JOIN ZABCDEMAILADDRESS ON ZABCDEMAILADDRESS.ZOWNER = ZABCDRECORD.Z_PK LEFT JOIN ZABCDPHONENUMBER ON ZABCDPHONENUMBER.ZOWNER = ZABCDRECORD.Z_PK; ', conn_address) 
# set up easy to use dict. for all contacts in correct format
first_names = contacts['ZFIRSTNAME']
last_names = contacts['ZLASTNAME']
phone_numbers = contacts['ZFULLNUMBER']
contact_dict = {}

for first_name, last_name, phone_number in zip(first_names, last_names, phone_numbers):
    # Skip empty numbers
    if (phone_number):
        first_name_clean = ''
        last_name_clean = ''
        if (first_name):
            first_name_clean = first_name
        if (last_name):
            last_name_clean = last_name
        full_name = first_name_clean + ' ' + last_name_clean
        clean_number = phone_number.replace(' ','')
        clean_number = clean_number.replace('(','')
        clean_number = clean_number.replace(')','')
        clean_number = clean_number.replace('-','')
        # This line is for USA, if your contacts reside outside USA 
        # you can change this to the country code of your choice
        if (clean_number[0] != '+'):
            clean_number = '+1' + clean_number
        contact_dict[clean_number] = full_name


# Get the user's name and number #
my_number = '+xxxxxxxx'

# Set up necessary data structures dynamically
tapbacks_sent = {}
tapbacks_recieved = {}

total_tapbacks = {
    "Loved" : 0,
    "Liked" : 0,
    "Disliked" : 0,
    "Laughed" : 0,
    "Emphasized" : 0,
    "Questioned" : 0
}

total_messages_sent = {}
for member in membership:
    if (member not in contact_dict):
        contact_dict[member] = member
    tapbacks_sent[contact_dict[member]] = {
                "Loved" : 0,
                "Liked" : 0,
                "Disliked" : 0,
                "Laughed" : 0,
                "Emphasized" : 0,
                "Questioned" : 0
            }
    tapbacks_recieved[contact_dict[member]] = {
                "Loved" : 0,
                "Liked" : 0,
                "Disliked" : 0,
                "Laughed" : 0,
                "Emphasized" : 0,
                "Questioned" : 0
            }
    total_messages_sent[contact_dict[member]] = 0

# Trace and store all tapbacks sent and recieved
i = 0 
for index, row in df_messages.iterrows():
    message = row['text']
    if (row['phone_number'] in membership):
        total_messages_sent[contact_dict[row['phone_number']]] = total_messages_sent[contact_dict[row['phone_number']]] + 1
    elif (row['is_from_me'] == 1):
        total_messages_sent[contact_dict[my_number]] = total_messages_sent[contact_dict[my_number]] + 1
    
    if message and row['associated_message_guid']:
        # Associated message guid refers to the message that was 'liked' or 'loved' etc.
        # Must trace this back in order to see who recieved said tapback
        tmp = row['associated_message_guid']
        # string manipulation
        if (tmp[0] == 'p'):
            final = tmp[4:]
        else:
            final = tmp[3:]

        # Check if there is an associated message. If not, can skip
        exists = True
        if (pd.read_sql_query("select * from message where guid = ?", conn, params=(final,)).empty):
            exists = False

        if ('Loved ' in message):
            total_tapbacks['Loved'] = total_tapbacks['Loved'] + 1
            sender = row['phone_number']
            if (row["is_from_me"] == 1):
                sender = my_number

            
           
            if (exists):
                handle_id = pd.read_sql_query("select handle_id from message where guid = ?", conn, params=(final,))
                
                handle_id = handle_id.iat[0,0]
                
                reciever = pd.read_sql_query("select id from handle where ROWID = ?", conn, params=(int(handle_id),))
                # If you sent the tapback, reciever will be empty
                if (reciever.empty):
                    reciever = my_number
                else:
                    reciever = reciever.iat[0,0]
                # Update data
                tapbacks_sent[contact_dict[sender]]['Loved'] = tapbacks_sent[contact_dict[sender]]['Loved'] + 1
                tapbacks_recieved[contact_dict[reciever]]['Loved'] = tapbacks_recieved[contact_dict[reciever]]['Loved'] + 1
        # Continue for the rest of the tapbacks

        if ("Liked " in message):
            total_tapbacks['Liked'] = total_tapbacks['Liked'] + 1
            sender = row['phone_number']
            if (row["is_from_me"] == 1):
                sender = my_number

            
            
            if (exists):
                handle_id = pd.read_sql_query("select handle_id from message where guid = ?", conn, params=(final,))
                
                handle_id = handle_id.iat[0,0]

                reciever = pd.read_sql_query("select id from handle where ROWID = ?", conn, params=(int(handle_id),))
                if (reciever.empty):
                    reciever = my_number
                else:
                    reciever = reciever.iat[0,0]
                
                tapbacks_sent[contact_dict[sender]]['Liked'] = tapbacks_sent[contact_dict[sender]]['Liked'] + 1
                tapbacks_recieved[contact_dict[reciever]]['Liked'] = tapbacks_recieved[contact_dict[reciever]]['Liked'] + 1
        if ("Disliked " in message):
            total_tapbacks['Disliked'] = total_tapbacks['Disliked'] + 1
            sender = row['phone_number']
            if (row["is_from_me"] == 1):
                sender = my_number

            
           
            if (exists):
                handle_id = pd.read_sql_query("select handle_id from message where guid = ?", conn, params=(final,))
                
                handle_id = handle_id.iat[0,0]

                reciever = pd.read_sql_query("select id from handle where ROWID = ?", conn, params=(int(handle_id),))
                if (reciever.empty):
                    reciever = my_number
                else:
                    reciever = reciever.iat[0,0]
                
                tapbacks_sent[contact_dict[sender]]['Disliked'] = tapbacks_sent[contact_dict[sender]]['Disliked'] + 1
                tapbacks_recieved[contact_dict[reciever]]['Disliked'] = tapbacks_recieved[contact_dict[reciever]]['Disliked'] + 1
        if ("Laughed at " in message):
            total_tapbacks['Laughed'] = total_tapbacks['Laughed'] + 1
            sender = row['phone_number']
            if (row["is_from_me"] == 1):
                sender = my_number

            
            
            if (exists):
                handle_id = pd.read_sql_query("select handle_id from message where guid = ?", conn, params=(final,))
                
                handle_id = handle_id.iat[0,0]

                reciever = pd.read_sql_query("select id from handle where ROWID = ?", conn, params=(int(handle_id),))
                if (reciever.empty):
                    reciever = my_number
                else:
                    reciever = reciever.iat[0,0]
                
                tapbacks_sent[contact_dict[sender]]['Laughed'] = tapbacks_sent[contact_dict[sender]]['Laughed'] + 1
                tapbacks_recieved[contact_dict[reciever]]['Laughed'] = tapbacks_recieved[contact_dict[reciever]]['Laughed'] + 1
        if ("Emphasized " in message):
            total_tapbacks['Emphasized'] = total_tapbacks['Emphasized'] + 1
            sender = row['phone_number']
            if (row["is_from_me"] == 1):
                sender = my_number

            
            
            if (exists):
                handle_id = pd.read_sql_query("select handle_id from message where guid = ?", conn, params=(final,))
                
                handle_id = handle_id.iat[0,0]

                reciever = pd.read_sql_query("select id from handle where ROWID = ?", conn, params=(int(handle_id),))
                if (reciever.empty):
                    reciever = my_number
                else:
                    reciever = reciever.iat[0,0]
                    
                
                tapbacks_sent[contact_dict[sender]]['Emphasized'] = tapbacks_sent[contact_dict[sender]]['Emphasized'] + 1
                tapbacks_recieved[contact_dict[reciever]]['Emphasized'] = tapbacks_recieved[contact_dict[reciever]]['Emphasized'] + 1
        if ("Questioned " in message):
            total_tapbacks['Questioned'] = total_tapbacks['Questioned'] + 1
            sender = row['phone_number']
            if (row["is_from_me"] == 1):
                sender = my_number

            
            if (exists):
                handle_id = pd.read_sql_query("select handle_id from message where guid = ?", conn, params=(final,))
                
                handle_id = handle_id.iat[0,0]

                reciever = pd.read_sql_query("select id from handle where ROWID = ?", conn, params=(int(handle_id),))
                if (reciever.empty):
                    reciever = my_number
                else:
                    reciever = reciever.iat[0,0]
                
                tapbacks_sent[contact_dict[sender]]['Questioned'] = tapbacks_sent[contact_dict[sender]]['Questioned'] + 1
                tapbacks_recieved[contact_dict[reciever]]['Questioned'] = tapbacks_recieved[contact_dict[reciever]]['Questioned'] + 1


# Print results to the console
print("TOTAL TAPBACKS")
totalsum = 0
for one in total_tapbacks:
    print(one + ": " + str(total_tapbacks[one]))   
    totalsum = totalsum + total_tapbacks[one]

print("\nTAPBACKS RECIEVED BY PERSON:")
recievedsum = 0 
for i in tapbacks_recieved:
    print(i + ": ")
    singlesum = 0
    for j, k in tapbacks_recieved[i].items():
        print("\t",j,"->", k)
        recievedsum = recievedsum + tapbacks_recieved[i][j]
        singlesum = singlesum + k
    print("SUM: " , singlesum)

print("\nTAPBACKS SENT BY PERSON:")
sentSum = 0 
for i in tapbacks_sent:
    print(i + ": ")
    singlesum = 0
    for j, k in tapbacks_sent[i].items():
        print("\t",j,"->", k)
        sentSum = sentSum + tapbacks_sent[i][j]
        singlesum = singlesum + k
    print("\t SUM: " , singlesum)

print("\nTotal Texts Sent by Person:")
for user in total_messages_sent:
    print("\t ", user, " --> ", total_messages_sent[user])


print('\nLaughed at ratios:')
for user in tapbacks_recieved:
    if (total_messages_sent[user] == 0):
        print("\t", user, " Ratio: ", tapbacks_recieved[user]['Laughed'] / 1, " --- no texts sent")
    else:
        print("\t", user, " Ratio: ", tapbacks_recieved[user]['Laughed'] / total_messages_sent[user])