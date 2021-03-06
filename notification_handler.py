import csv
import urllib3
from apns import APNs, Frame, Payload
from datetime import datetime as dt
from datetime import timedelta

import boto.dynamodb2
from boto.dynamodb2.table import Table
from boto.dynamodb2.items import Item

import firebase_admin
import requests
import json

from firebase_admin import messaging

cred = firebase_admin.credentials.Certificate("audl_firebase.json")
firebase_app = firebase_admin.initialize_app(credential=  cred) #, { 'databaseURL' : 'https://www.google.com/url?q=https://audl-6ad83.firebaseio.com' })

token_hex = '0d4a8842d98d949225f1aeba1782604a8ae6fd9397c448c18ee52cf78933e368'
ios_table = "ios_device_tokens"
android_table = "android_device_tokens"


def get_fcm_token( apns_token ):
    
    # setup url and headers
    url = "https://iid.googleapis.com/iid/v1:batchImport"
    
    headers = { "Authorization" : "key=AAAAsFRIxTo:APA91bG2MU9PmCUa3iXk1dHkT1v04qkydHHJ25WU1DVcuF1k_HsZAcSmdYg987Q3NUWgPCC4oS2CeCl0PypTkulkfQXhSIL_1F1eTS0PxGwBNUm_4tM3fs3_NoYoYaRtpYngMIAMpxIn",
                "Content-Type" : "application/json" }

    # insert apns_token into data for request
    data = { "application" : "AUDL",
             "sandbox" : False,
             "apns_tokens": [
                 apns_token,
             ]
         }

    # make request
    response = requests.post(url, json = data, headers = headers)
    
    assert( response.status_code == 200 ) # request should be successful

    # parset the returned json
    content = json.loads(response.text)
    
    assert( len(content['results']) == 1 ) # should only get one response
    assert( content['results'][0].has_key('registration_token') ) # should've gotten a valid key
            
    fcm_token = content['results'][0]['registration_token'] 
            
    return fcm_token


def dynamo_connection():
    #read our aws key values for access to the server
    reader = csv.reader(open("rootkey.csv",'rb'),delimiter = '=')
    access_key = reader.next()[1]
    secret_key = reader.next()[1]
    #establish a connection to the dynamodb server
    return boto.dynamodb2.connect_to_region("us-east-1", aws_access_key_id = access_key, aws_secret_access_key = secret_key)

def ios_token_table():
    conn = dynamo_connection()
    if ios_table not in conn.list_tables()['TableNames']:
        print "ERROR: Could not retrieve the ios device token table."
        return
    return Table(ios_table, connection = conn)

def android_token_table():
    conn = dynamo_connection()
    if android_table not in conn.list_tables()['TableNames']:
        print "ERROR: Could not retrieve the android device token table."
        return
    return Table(android_table, connection = conn)

def register_ios_token(path_entities):
    print("Registering ios token...")
    token = path_entities[-1]
    topic = path_entities[-2]
    #determine what type of notification is being registered
    register_ios_token_for_topic(topic, token)

def register_ios_token_from_path(path_entities):
    register_ios_token(path_entities)
    
def register_android_token(path_entities):
    print("Registering android token...")
    token = path_entities[-1]
    #determine what type of notification is being registered
    if "general" in path_entities:
        register_general_android_token(token)
    else:
        abbreviation = path_entities[-2]
        register_team_android_token(abbreviation,token)

def register_android_token_from_path(path_entities):
    register_android_token(path_entities)

def register_team_token(table_name, abbreviation, token):
  #setup a dynamo db connection                                                                                                                                                    
    conn = dynamo_connection()
    #make sure this table exists                                                                                                                                                     
    if any(table_name is table for table in conn.list_tables()):
        print("Could not find ios table on db server")
        return False
    token_table = Table(table_name,connection=conn)

    #get any abbreviation items with this token and remove them from the table
    items_to_remove = list(token_table.scan(token__eq = token, notification_type__ne = "general"))
    if len(items_to_remove) > 1 : print "Warning: Had to remove more than one previously existing team based entry for this token:" , token
    [token_table.delete_item(notification_type=item['notification_type'],token=item['token']) for item in items_to_remove]
    #if the new favorite team is none, then we can be done
    if abbreviation == "None": return True
    #otherwise add the new team to the table
    if validate_token(token):
        item_data = { "notification_type" : abbreviation, "token" : token }
        token_table.put_item(data=item_data, overwrite = True)
        return True
    else:
        print("Invalid token. Not adding to table.")
        return False

def register_ios_token_for_topic(topic, token):
    fcm_token = get_fcm_token(token)
    topic = topic.upper()
    messaging.subscribe_to_topic([fcm_token,], topic)

def register_team_ios_token(abbrev, token):
    register_team_token(ios_table,abbrev,token)

def register_general_ios_token(token):
    register_general_token(ios_table, token)

def register_team_android_token(abbrev, token):
    register_team_token(android_table,abbrev,token)

def register_general_android_token(token):
    register_general_token(android_table, token)
    

def register_general_token(table_name, token):
    #setup a dynamo db connection
    conn = dynamo_connection()
    #make sure this table exists
    if any(table_name is table for table in conn.list_tables()):
        print("Could not find ios table on db server")
        return False
    token_table = Table(table_name,connection=conn)
    #make sure there is an item for the notification_type in that table
    if validate_token(token):
        register_token(token_table,"general",token) 
        return True
    else:
        print("Invalid token. Not adding to table.")
        return False

def register_token(table, notification_type, token):
    #create data item and put into the table
    item_data = { "notification_type" : notification_type, "token" : token }
    table.put_item(data=item_data, overwrite = True)
    
def validate_token(token):
    try:
        int(token,16)
        return True
    except:
        return False

def send_general_notification(message):
    send_ios_general_notification(message)
    condition = "'GENERAL' in topics"
    send_fcm_notification(condition,message)

def send_game_notification(hometeam_abbrev,awayteam_abbrev,message):
    send_team_notification(hometeam_abbrev,message)
    send_team_notification(awayteam_abbrev,message)
    condition = "\'" + hometeam_abbrev + "\' in topics || \'" + awayteam_abbrev + "\' in topics"
    send_fcm_notification(condition,message)

def send_team_notification(team_abbrev,message):
    send_ios_team_notification(team_abbrev, message)
    
def send_fcm_notification(condition,message):
    return True


def send_ios_general_notification(message):
    ios_device_table = ios_token_table()
    items = list(ios_device_table.query(notification_type__eq = 'general'))
    tokens = [item['token'] for item in items]
    send_ios_notifications(message, tokens)

def send_ios_team_notification(team_abbrev,message):
    ios_device_table = ios_token_table()
    items = list(ios_device_table.query(notification_type__eq = team_abbrev))
    tokens = [item['token'] for item in items]
    send_ios_notifications(message, tokens)

def get_apns_connection(sandbox = False, cert_file = "AUDLDistCert.pem", key_file = "AUDLDistKey.pem"):
    return APNs(use_sandbox=sandbox, cert_file = cert_file, key_file = key_file)

def send_ios_notification(message, token = token_hex):
    return

def send_ios_notifications(message, tokens = [token_hex]):
    for token in tokens:
        send_ios_notification(message, token)
