import json

import httplib2
import apiclient
from pprint import pprint
from oauth2client.service_account import ServiceAccountCredentials

credentials_file = 'creds.json'
users_table = '1ECOc7GmSV1CbDX3_T1mmLPNI96mWh5x4jpbYYXNiXa8'
appointments_table = '1Cwre4Xr4TitHTLguZX8oBCIzqctZvBzFxoEue0wz7GQ'

credentials = ServiceAccountCredentials.from_json_keyfile_name(credentials_file,
                                                               ['https://www.googleapis.com/auth/spreadsheets',
                                                                'https://www.googleapis.com/auth/drive'])
httpauth = credentials.authorize(httplib2.Http())
service = apiclient.discovery.build('sheets', 'v4', http=httpauth)

def getValues():
    values = service.spreadsheets().values().get(
        spreadsheetId=users_table,
        range='A1:D10',
        majorDimension='ROWS'
    ).execute()
    pprint(values)
def inputUsers(values, num):
    range = 'A2:H'+str(num+1)
    service.spreadsheets().values().batchUpdate(
        spreadsheetId=users_table,
        body={
            "valueInputOption": "USER_ENTERED",
            "data": [
                {"range": range,
                 "majorDimension": "ROWS",
                 "values": values}
            ]
        }
    ).execute()
def inputAppointments(values, num):
    range = 'A2:F'+str(num+10)
    values = json.dumps(values, default=str)
    values = json.loads(values)
    service.spreadsheets().values().batchUpdate(
        spreadsheetId=appointments_table,
        body={
            "valueInputOption": "USER_ENTERED",
            "data": [
                {"range": range,
                 "majorDimension": "ROWS",
                 "values": values}
            ]
        }
    ).execute()

