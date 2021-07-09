from netmiko import ConnectHandler
import os
import time
import datetime
import json
import logging

logging.basicConfig(filename="test.log", level=logging.DEBUG)
logger = logging.getLogger("netmiko")

device_list = '/home/aramideo/Documents/containerlab/ssh-copy-net/Backup_Scripts/router.json'
backup_filename = 'RTR-Config-Backup.cfg'

with open(device_list, "r") as json_file:
    data = json.load(json_file)
    # Change data['router_list'] to data['switch_list'] if you are using switch.json
    # print(data['router_list'])
    for router in data['router_list']:
        device = {
    	    'device_type': router['device_type'],
    	    'host':   router['ip'],
    	    'username': router['username'],    # Provide SSH username
    	    'password': router['password'],    # Provide SSH password
	}

        try:
            net_connect = ConnectHandler(**device)
        except:
            continue

        if device['device_type'] == 'cisco_ios' or device['device_type'] == 'cisco_xr':

            # net_connect.enable()

            output_run_config = net_connect.send_command("show running-config")
        
        else:
            output_run_config = net_connect.send_command("show configuration | display set")

            # net_connect.exit_enable_mode()
        net_connect.disconnect()

            #Create a separate directory for each device if not exists.
        backup_dir = '/home/aramideo/Documents/containerlab/ssh-copy-net/Network_Device_Backups/Router/'+router['hostname']
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)

            #Write the device running-config to a file.
        f0 = open(backup_dir+'/'+backup_filename, 'w')
        f0.write(output_run_config)
        f0.close()