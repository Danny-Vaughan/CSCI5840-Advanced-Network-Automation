#!/usr/bin/env python3

from netmiko import ConnectHandler
import subprocess
from datetime import datetime
import pytz
import re
import csv
import os

requirements = "/home/student/CSCI5840-Advanced-Network-Automation/Ansible/requirements.csv"

devices = {
    "R1": "172.20.20.101",
    "R2": "172.20.20.102",
    "R3": "172.20.20.103",
    "R4": "172.20.20.104",
    "S1": "172.20.20.201",
    "S2": "172.20.20.202",
    "S3": "172.20.20.203",
    "S4": "172.20.20.204"
}

class UnitTestError(Exception):
    '''This was made to be raised if a test fails'''
    pass

# Log into R3 and check that it has a correctly configured Loopback interface
def check_loopback_ip():
    router = {
        "device_type": "arista_eos",
        "ip": "172.20.20.103",
        "username": "admin",
        "password": "admin"
    }
    try:
        with ConnectHandler(**router) as net_connect:
            net_connect.enable()
            output = net_connect.send_command("show run interface loopback0")
            ip_match = re.search(r"ip address (\d+\.\d+\.\d+\.\d+'/32')", output)
            if ip_match:
                if ip_match == "1.0.0.3/32":
                    return 0
                else:
                    return 1
    except Exception as e:
        return f"Error: {e}"

# Log into R4 and verify that it has a BGP peering connection with R5
def check_bgp_neighbor():
    router = {
        "device_type": "arista_eos",
        "ip": "172.20.20.104",
        "username": "admin",
        "password": "admin"
    }
    try:
        with ConnectHandler(**router) as net_connect:
            output = net_connect.send_command("show ip bgp summ")
            if not output:
                return f"no bgp configuration found on r4"
            
            neighbors = re.findall(r"(\d+\.\d+\.\d+\.\d+)", output)
            if '1.0.0.5' in neighbors:
            	return 0
            else:
            	return 1
    except Exception as e:
        return f"Error: {e}"

# Log into R1 and verify that it can ping the web server
def check_ping():
    router = {
        "device_type": "arista_eos",
        "ip": "172.20.20.101",
        "username": "admin",
        "password": "admin"
    }
    try:
        with ConnectHandler(**router) as net_connect:        
            dst_ip = "203.0.113.10"
            ping_output = net_connect.send_command(f"ping {dst_ip}")
            fail_match = re.search(r"100% packet loss", ping_output)
            if fail_match:
                return 1
            else:
                return 0
    except Exception as e:
        return f"Error: {e}"


def get_golden_configs():
    # Pulls 'golden' configs from all managed devices via SSH using Netmiko
    save_path = "/home/student/CSCI5840-Advanced-Network-Automation/Ansible/golden_configs/"
    archive_path = "/home/student/CSCI5840-Advanced-Network-Automation/Ansible/config_archive/"
    creds = get_device_credentials()
    os.makedirs(save_path, exist_ok=True)
    os.makedirs(archive_path, exist_ok=True)
    subprocess.run(f"mv {save_path}* {archive_path}", shell=True)
    
    mountain_tz = pytz.timezone("America/Denver")
    timestamp = datetime.now(mountain_tz).strftime("%Y-%m-%d_%H-%M-%S")

    saved_files = []
    
    for hostname, ip in devices.items():
        device = {
            "device_type": "arista_eos",
            "host": ip,
            "username": creds[hostname]["username"],
            "password": creds[hostname]["password"],
        }

        try:
            print(f"Connecting to {hostname} ({ip})...")
            connection = ConnectHandler(**device)
            connection.enable()
            config_output = connection.send_command("show run")
            connection.disconnect()

            filename = f"{hostname}_golden_config_{timestamp}.txt"
            filepath = os.path.join(save_path, filename)

            with open(filepath, "w") as file:
                file.write(config_output)

            saved_files.append(filename)

        except Exception as e:
            print(f"Failed to get config from {hostname}: {e}")

    return saved_files, timestamp


def get_device_credentials():
    # Reads credentials for each device from requirements.csv
    creds = {}
    try:
        with open(requirements, newline="") as file:
            reader = csv.DictReader(file)
            for row in reader:
                hostname = row.get("hostname", "").strip()
                username = row.get("username", "").strip()
                password = row.get("password", "").strip()
                if hostname and username and password:
                    creds[hostname] = {"username": username, "password": password}
    except Exception as e:
        print(f"Error reading credentials: {e}")
    return creds



def main():
    result1 = check_loopback_ip()
    result2 = check_bgp_neighbor()
    result3 = check_ping()
    if result1 == 1 or result2 == 1 or result3 == 1:
        rollback_config()
        raise UnitTestError(f"Unit testing failed result1={result1}, result2={result2}, result3={result3}")
    else:
        print("Unit testing passed")
        get_golden_configs()

        
if __name__ == "__main__":
    main()
