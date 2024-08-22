#!/usr/bin/env python3
import json
import os
import inspect
import getpass
import argparse
import pandas as pd
import numpy as np
import requests
from pprint import pprint as pp
from requests.exceptions import HTTPError
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))

## Variables 
XIQ_API_token = ''

# count of devices returned per page
pageSize = 100

csv_file_name = 'Device_Count.csv'
PATH = current_dir

parser = argparse.ArgumentParser()
parser.add_argument('--csv', type=str, help="Optional - Overrides the name of the CSV output file") 
args = parser.parse_args()

URL = "https://api.extremecloudiq.com"

HEADERS = {"Accept": "application/json", "Content-Type": "application/json"}

proxyDict = {
            "http": "",
            "https": ""
        }

def get_api_call(url):
  try:
    response = requests.get(url, headers= HEADERS, verify=False, proxies=proxyDict)
  except HTTPError as http_err:
    raise ValueError(f'HTTP error occurred: {http_err}') 
  if response is None:
    log_msg = "ERROR: No response received from XIQ!"
    raise ValueError(log_msg)
  if response.status_code != 200:
    log_msg = f"Error - HTTP Status Code: {str(response.status_code)}"
    try:
      data = response.json()
    except json.JSONDecodeError:
      log_msg += (f" - {response.text}")
    else:
        if 'error_message' in data:
            log_msg += (f" - {data['error_message']}")
        elif 'message' in data:
           log_msg += (f" - {data['message']}")

    raise ValueError(log_msg) 
  try:
      data = response.json()
  except json.JSONDecodeError:
      raise ValueError(f"Unable to parse json data - {url} - HTTP Status Code: {str(response.status_code)}")
  return data

def collectDevices():
  page = 1
  pageCount = 1
  firstCall = True
  devices = []
  while page <= pageCount:
    url = f"{URL}/devices?page={str(page)}&limit={str(pageSize)}&fields=id&fields=product_type&fields=locations&deviceTypes=REAL"
    try:
      rawList = get_api_call(url)
    except ValueError as e:
      print(e)
      print("Script is exiting...")
      raise SystemExit
    except:
      print("Unknown Error collecting devices. \nScript is exiting...")
      raise SystemExit
    devices = devices + rawList['data']
    if firstCall == True:
      pageCount = rawList['total_pages']
    print(f"completed page {page} of {rawList['total_pages']} collecting Devices")
    page = rawList['page'] + 1 
  return devices

def getAccessToken(XIQ_username, XIQ_password):
    url = f"{URL}/login"
    payload = json.dumps({"username": XIQ_username, "password": XIQ_password})
    response = requests.post(url, headers=HEADERS, data=payload)
    if response is None:
      print("ERROR: Not able to login into ExtremeCloudIQ - no response!")
      print("Script is exiting...")
      raise SystemExit
    if response.status_code != 200:
        print(f"Error getting access token - HTTP Status Code: {str(response.status_code)}")
        print(f"\t\t{response.text}")
        print("Script is exiting...")
        raise SystemExit
    data = response.json()

    if "access_token" in data:
        #print("Logged in and Got access token: " + data["access_token"])
        HEADERS["Authorization"] = "Bearer " + data["access_token"]
        return 0

    else:
        print("Unknown Error: Unable to gain access token")
        print("Script is exiting...")
        raise SystemExit

# Function to convert floats to ints
def convert_floats(val):
    if isinstance(val, float):
        return int(val)
    return val

# MAIN

## XIQ Authorization
if XIQ_API_token:
    HEADERS["Authorization"] = "Bearer " + XIQ_API_token
else:
    print("Enter your XIQ login credentials")
    username = input("Email: ")
    password = getpass.getpass("Password: ")
    getAccessToken(XIQ_username=username,XIQ_password = password)

# check for csv filename override
if args.csv:
   csv_file_name = args.csv

# Collect devices   
devices = collectDevices()

# build csv data
csv_data = []
if devices:
    for device in devices:
      if device['locations']:
        device['locations'] = device['locations'][-2]['name']
      else:
        device['locations'] = None

    df = pd.DataFrame(devices)
    df = df[df['locations'].notna()]
    for location in df.locations.unique():
        filt = (df['locations'] == location)
        data = {"location" : location}
        loc_df = df.loc[filt]
        for product in loc_df.product_type.unique():
            filt = (loc_df['product_type'] == product)
            device_count = len(loc_df.loc[filt])
            product_count = { product: device_count}
            data.update(product_count)
        csv_data.append(data)

# cleanup csv data
csv_df = pd.DataFrame(csv_data)
csv_df.fillna(0, inplace=True)
csv_df = csv_df.apply(lambda col: col.map(convert_floats) if col.dtype == 'float64' else col)
csv_df['Total'] = csv_df.loc[:, csv_df.columns != 'location'].sum(axis=1)

# save csv data
print(f"Writing CSV File {csv_file_name}")
csv_df.to_csv(f"{PATH}/{csv_file_name}", index=False)