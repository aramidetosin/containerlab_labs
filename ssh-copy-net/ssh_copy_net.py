#!/usr/bin/env python3

import os
import getpass
import argparse
from netmiko import ConnectHandler, SCPConn

UNSET = False

def read_file(fn):
   with open(fn) as f:
      result = f.read()
   return result.rstrip()

def cisco_ios(username, public_key):
    public_key = [public_key[i:i+253] for i in range(0, len(public_key), 253)]
    commands_to_set = ['username {} privilege 15'.format(username),
                       'ip ssh pubkey-chain',
                       'username {}'.format(username),
                       'key-string'] + public_key + ['exit']
    commands_to_unset = ['no username {}'.format(username),
                         '\n'
                         'ip ssh pubkey-chain',
                         'no username {}'.format(username)]
    if not UNSET:
        return commands_to_set
    else:
        return commands_to_unset

def arista(username, public_key, admin_secret):
    commands_to_set = ['username {} privilege 15 secret {}'.format(username, admin_secret),
                       'username {} sshkey {}'.format(username, public_key)]
    commands_to_unset = ['no username {}'.format(username)]
    if not UNSET:
        return commands_to_set
    else:
        return commands_to_unset

def junos(username, public_key):
    commands_to_set = ['edit system login',
                       'set user {} class super-user'.format(username),
                       'set user {} authentication ssh-rsa "{}"'.format(username,
                                                                      public_key),
                        'exit']
    commands_to_unset = ['edit system login',
                         'delete user {}'.format(username),
                         'exit']
    if not UNSET:
        return commands_to_set
    else:
        return commands_to_unset

def dell_os9(username):
    commands_to_set = ['username {} privilege 15'.format(username),
                       'ip ssh rsa-authentication enable',
                       'exit',
                       'ip ssh rsa-authentication username {0} \
                       authorized-keys flash:/{0}.pub'.format(username)]
    commands_to_unset = ['no username {}'.format(username)]
    if not UNSET:
        return commands_to_set
    else:
        return commands_to_unset

def comware(username):
    commands_to_set = ['public-key peer {0} import sshkey {0}.pub'.format(username),
                       'ssh user {0} service-type all authentication-type publickey assign publickey {0}'.format(username),
                       'local-user {}'.format(username),
                       'service-type ssh']
    commands_to_unset = ['undo ssh user {}'.format(username),
                         'undo public-key peer {}'.format(username),
                         'undo local-user {}'.format(username)]
    if not UNSET:
        return commands_to_set
    else:
        return commands_to_unset

def sros(username, public_key):
    public_key = public_key.split()[1]
    commands_to_set = ['system security',
                       'user "{}"'.format(username),
                       'access console',
                       'public-keys rsa rsa-key 1 create',
                       'key-value "{}"'.format(public_key), 'exit all']
    commands_to_unset = ['system security',
                         'no user "{}"'.format(username), 'exit all']
    if not UNSET:
        return commands_to_set
    else:
        return commands_to_unset

def mellanox(username, public_key):
    commands_to_set = ['username {} capability admin'.format(username),
                       'ssh client user {} authorized-key sshv2 "{}"'.format(username, public_key)]
    commands_to_unset = ['no username {}'.format(username)]
    if not UNSET:
        return commands_to_set
    else:
        return commands_to_unset

def scp_file(ssh_conn, file_path, target_file):
    scp_conn = SCPConn(ssh_conn)
    scp_conn.scp_transfer_file(args.ssh_key, target_file)
    scp_conn.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("ip", help="Device hostname or IP address")
    parser.add_argument("vendor", help="Device vendor(same as in netmiko)",
                         choices=['cisco_ios', 'arista_eos', 'juniper',
                                  'alcatel_sros', 'dell_force10', 'hp_comware',
                                  'mellanox_ssh'])
    parser.add_argument("--user", default=getpass.getuser(),
                        help="User for which to add SSH key")
    parser.add_argument("-P", "--port", default=22, help="SSH port (Default=22)", type=int)
    parser.add_argument("-i", default=os.path.expanduser("~/.ssh/id_rsa.pub"),
                        help="Path to public SSH key", dest='ssh_key')
    parser.add_argument("-u", help="Device admin username", dest='device_admin')
    parser.add_argument("-p", help="Device admin password", dest='device_pass')
    parser.add_argument("-r", "--remove", help="Remove SSH key", action="store_true")
    parser.add_argument("-v", "--verbose", help="Increase output verbosity", action="store_true")
    args = parser.parse_args()

    if not args.device_admin:
        device_admin = input('Username: ')
    else:
        device_admin = device_admin

    if not args.device_pass:
        device_pass = getpass.getpass('Password: ')
    else:
        device_pass = device_pass

    if args.remove:
        UNSET = True

    net_device = {
        'device_type': args.vendor,
        'ip': args.ip,
        'username': device_admin,
        'password': device_pass,
        'secret': device_pass,
        'port': args.port,
    }

    ssh_conn = ConnectHandler(**net_device)
    if args.vendor == 'cisco_ios':
        commands_set = cisco_ios(args.user, read_file(args.ssh_key))
        output = ssh_conn.send_config_set(commands_set)
        output += ssh_conn.send_command_expect('write memory')
    elif args.vendor == 'juniper':
        commands_set = junos(args.user, read_file(args.ssh_key))
        output = ssh_conn.send_config_set(commands_set, exit_config_mode=False)
        output += ssh_conn.commit()
    elif args.vendor == 'arista_eos':
        ssh_conn.enable()
        commands_set = arista(args.user, read_file(args.ssh_key), device_pass)
        output = ssh_conn.send_config_set(commands_set)
        output += ssh_conn.send_command_expect('write memory')
    elif args.vendor == 'alcatel_sros':
        commands_set = sros(args.user, read_file(args.ssh_key))
        output = ssh_conn.send_config_set(commands_set, exit_config_mode=False)
        output += ssh_conn.send_command('admin save', expect_string='#')
    elif args.vendor == 'dell_force10':
        scp_file(ssh_conn, args.ssh_key, '{}.pub'.format(args.user))
        commands_set = dell_os9(args.user)
        output = ssh_conn.send_config_set(commands_set)
        output += ssh_conn.send_command_expect('write memory')
    elif args.vendor == 'hp_comware':
        scp_file(ssh_conn, args.ssh_key, '{}.pub'.format(args.user))
        commands_set = comware(args.user)
        output = ssh_conn.send_config_set(commands_set)
        output += ssh_conn.send_config_set(['save', 'Y', '', 'Y'])
    elif args.vendor == 'mellanox_ssh':
        ssh_conn.enable()
        commands_set = mellanox(args.user, read_file(args.ssh_key))
        output = ssh_conn.send_config_set(commands_set)
        output += ssh_conn.send_command_expect('write memory')

    if args.verbose:
        print (output)
    print("All Done!")
