# XIQ Device Count Per Location
##### XIQ_Device_Count_Per_Loc.py
### <span style="color:purple">Purpose</span>
This script will collect the devices from XIQ using API, then build a CSV listing out each building and how many of each product type are there. 

## <span style="color:purple">Setting up the script</span>
##### Variables
At the top of the script there are some variables that need to be added.
1. <span style="color:purple">XIQ_API_token</span> - Update this with a valid token. The token will need the device_list or device:r permission
2. <span style="color:purple">pageSize</span> - This is set to 100 which is the max number of devices that can be returned per API call. This can be lowered if needed.
3. <span style="color:purple">csv_file_name</span> - this is the name of the file that will be saved.
4. <span style="color:purple">proxyDict</span> - if a proxy is used you can fill out the http and https to be used.
```
proxyDict = {
            "http": "",
            "https": ""
        }
```

## Running the script
open the terminal to the location of the script and run this command.

```
python XIQ_Device_Count_Per_Loc.py
```

## requirements
There are additional modules that need to be installed in order for this script to function. They are listed in the requirements.txt file and can be installed with the command 'pip install -r requirements.txt' if using pip.