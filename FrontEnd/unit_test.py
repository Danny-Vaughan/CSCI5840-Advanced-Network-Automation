#!/usr/bin/env python3

from netmiko import ConnectHandler
from datetime import datetime
import subprocess
import functions
import pytz
import re
import csv
import os
import ast

requirements = "/home/student/CSCI5840-Advanced-Network-Automation/Ansible/requirements.csv"
playbook_gen = "/home/student/CSCI5840-Advanced-Network-Automation/Ansible/mk_new_play.py"
functions_file = "/home/student/CSCI5840-Advanced-Network-Automation/FrontEnd/functions.py"
config_gen = "/home/student/CSCI5840-Advanced-Network-Automation/Ansible/main.py"
frontend = "/home/student/CSCI5840-Advanced-Network-Automation/FrontEnd/app.py"
devices = functions.get_devices()


def count_functions_in_file(filename):

    with open(filename, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=filename)

    # Count functions
    func_count = sum(isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) for node in ast.walk(tree))
    return func_count


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


class UnitTestError(Exception):
    '''This was made to be raised if a test fails'''
    pass


def main():
    result1 = check_loopback_ip()
    result2 = check_bgp_neighbor()
    result3 = check_ping()
    if result1 == 1 or result2 == 1 or result3 == 1:
        rollback_config()
        raise UnitTestError(f"Unit testing failed result1={result1}, result2={result2}, result3={result3}")
    else:
        print("Unit testing passed")
        functions.get_golden_configs()


if __name__ == "__main__":
    main()
