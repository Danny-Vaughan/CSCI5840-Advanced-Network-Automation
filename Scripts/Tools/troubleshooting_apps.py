#!/usr/bin/env python3

from netmiko import ConnectHandler
import re

def check_connectivity(man_ip, target_ip):
    router = {
        "device_type": "arista_eos",
        "ip": f"{man_ip}",
        "username": "admin",
        "password": "admin"
    }
    try:
        with ConnectHandler(**router) as net_connect:
            net_connect.enable()
            output = net_connect.send_command(f"ping {target_ip}")
                return output
    except Exception as e:
        return f"Error: {e}"

def check_bgp_neighbors(man_ip):
    router = {
        "device_type": "arista_eos",
        "ip": f"{man_ip}",
        "username": "admin",
        "password": "admin"
    }
    try:
        with ConnectHandler(**router) as net_connect:
            output = net_connect.send_command("show ip bgp summ")
            if not output:
                return f"no bgp configuration found"
            neighbors = re.findall(r"(\d+\.\d+\.\d+\.\d+)", output)
            return(f"BGP neighbors: {neighbors}")
    except Exception as e:
        return f"Error: {e}"

def ip_route_finder(man_ip, search_term):
    router = {
        "device_type": "arista_eos",
        "ip": f"{man_ip}",
        "username": "admin",
        "password": "admin"
    }
    try:
        with ConnectHandler(**router) as net_connect:        
            output = net_connect.send_command(f"show ip route | inc {search_term}")
                return(output)
    except Exception as e:
        return f"Error: {e}"

def main():
    result1 = check_connectivity()
    result2 = check_bgp_neighbors()
    result3 = ip_route_finder()
        
if __name__ == "__main__":
    main()
