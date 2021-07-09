from netmiko import ConnectHandler
import os
import time
import datetime
import json
import logging

logging.basicConfig(filename="test.log", level=logging.DEBUG)
logger = logging.getLogger("netmiko")

device_list = '/home/aramideo/Documents/containerlab/ssh-copy-net/Backup_Scripts/router.json'

with open(device_list, "r") as json_file:
    data = json.load(json_file)
    # Change data['router_list'] to data['switch_list'] if you are using switch.json
    # print(data['router_list'])
# backup_filename = 'RTR-Config-Backup.cfg'
    for router in data['router_list']:
        device = {
            'device_type': router['device_type'],
            'host':   router['ip'],
            'username': router['username'],    # Provide SSH username
            'password': router['password'],    # Provide SSH password
        }
        # if device['device_type'] == 'cisco_ios' or device['device_type'] == 'cisco_xr':

        config_file = f"/home/aramideo/Documents/containerlab/ssh-copy-net/Network_Device_Backups/Router/{router['hostname']}/RTR-Config-Backup.cfg"

        with ConnectHandler(**device) as net_connect:
            if device['device_type'] == 'cisco_ios':
                output = net_connect.send_config_from_file(config_file)
                print()
                print(output)
                print()
            else:
            # elif device['device_type'] == 'cisco_xr' or device['device_type'] == 'juniper_junos':
                output = net_connect.send_config_from_file(config_file, exit_config_mode=False)
                output = net_connect.commit()
                print()
                print(output)
                print()
            # elif device['device_type'] == 'juniper_junos':
            #     output = net_connect.send_config_from_file(config_file, exit_config_mode=False)
            #     output = net_connect.commit()
            #     print()
            #     print(output)
            #     print()