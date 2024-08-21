#!/usr/bin/env python3
import json
import os
import inspect
import pandas as pd
import numpy as np
import requests
from pprint import pprint as pp
from requests.exceptions import HTTPError
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))

## Variables 
XIQ_API_token = '***'

# count of devices returned per page
pageSize = 100

csv_file_name = 'Name-of-File.csv'
PATH = current_dir

URL = "https://api.extremecloudiq.com"

HEADERS = {"Accept": "application/json", "Content-Type": "application/json", 'Authorization':"Bearer " + XIQ_API_token}

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

# Function to convert floats to ints
def convert_floats(val):
    if isinstance(val, float):
        return int(val)
    return val

# MAIN
devices = collectDevices()
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

csv_df = pd.DataFrame(csv_data)
csv_df.fillna(0, inplace=True)
csv_df = csv_df.apply(lambda col: col.map(convert_floats) if col.dtype == 'float64' else col)

print(f"Writing CSV File {csv_file_name}")
csv_df.to_csv(f"{PATH}/{csv_file_name}", index=False)