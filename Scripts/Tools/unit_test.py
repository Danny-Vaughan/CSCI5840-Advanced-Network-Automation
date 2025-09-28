#!/usr/bin/env python3

from netmiko import ConnectHandler
import re

class UnitTestError(Exception):
    '''This was made to be raised if a test fails'''
    pass

def check_loopback_ip():
    router = {
        "device_type": "arista_eos",
        "ip": "172.20.20.15",
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

def check_bgp_neighbor():
    router = {
        "device_type": "arista_eos",
        "ip": "172.20.20.5",
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

def check_ping():
    router = {
        "device_type": "arista_eos",
        "ip": "172.20.20.2",
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

def main():
    result1 = check_loopback_ip()
    result2 = check_bgp_neighbor()
    result3 = check_ping()
    if result1 == 1 or result2 == 1 or result3 == 1:
        raise UnitTestError(f"Unit testing failed result1={result1}, result2={result2}, result3={result3}")
    else:
        print("Unit testing passed")
        
if __name__ == "__main__":
    main()
