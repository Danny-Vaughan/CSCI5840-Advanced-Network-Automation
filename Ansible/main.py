#!/usr/bin/env python3

import os
import csv
import sys
import glob
import subprocess
import mk_new_play
from netmiko import ConnectHandler
import concurrent.futures as cf


site_yml_location = "/home/student/CSCI5840-Advanced-Network-Automation/Ansible/site.yml"
router_tasks_yml_location = "/home/student/CSCI5840-Advanced-Network-Automation/Ansible/roles/router/tasks/main.yml"
switch_tasks_yml_location = "/home/student/CSCI5840-Advanced-Network-Automation/Ansible/roles/switch/tasks/main.yml"
edge_router_tasks_yml_location = "/home/student/CSCI5840-Advanced-Network-Automation/Ansible/roles/edge_router/tasks/main.yml"
requirements = "/home/student/CSCI5840-Advanced-Network-Automation/Ansible/requirements.csv"
inventory = "/home/student/CSCI5840-Advanced-Network-Automation/Ansible/inventory.yml"
candidate_dir = "/home/student/CSCI5840-Advanced-Network-Automation/Ansible/candidate_configs"
golden_dir = "/home/student/CSCI5840-Advanced-Network-Automation/Ansible/golden_configs"


site_yml_content = """
---
- name: Configure Routers
  hosts: router
  connection: local
  gather_facts: no
  roles:
    - role: router

- name: Configure Edge Routers
  hosts: edge_router
  connection: local
  gather_facts: no
  roles:
    - role: edge_router

- name: Configure Switches
  hosts: switch
  connection: local
  gather_facts: no
  roles:
    - role: switch
"""

router_tasks_yml_content = """
---
- name: Load Variables
  include_vars:
    file: "/home/student/CSCI5840-Advanced-Network-Automation/Ansible/roles/router/vars/router.yml"

- name: Generate configuration files
  template: 
    src: router.j2 
    dest: "/home/student/CSCI5840-Advanced-Network-Automation/Ansible/candidate_configs/{{item.hostname}}.txt"
  loop: "{{ devices | default([]) }}"
  when: devices is defined
"""
switch_tasks_yml_content = """
---
- name: Load Variables
  include_vars:
    file: "/home/student/CSCI5840-Advanced-Network-Automation/Ansible/roles/switch/vars/switch.yml"

- name: Generate configuration files
  template: 
    src: switch.j2
    dest: "/home/student/CSCI5840-Advanced-Network-Automation/Ansible/candidate_configs/{{item.hostname}}.txt"
  loop: "{{ devices | default([]) }}"
  when: devices is defined
"""
edge_router_tasks_yml_content = """
---
- name: Load Variables
  include_vars:
    file: "/home/student/CSCI5840-Advanced-Network-Automation/Ansible/roles/edge_router/vars/edge_router.yml"

- name: Generate configuration files
  template: 
    src: edge_router.j2 
    dest: "/home/student/CSCI5840-Advanced-Network-Automation/Ansible/candidate_configs/{{item.hostname}}.txt"
  loop: "{{ devices | default([]) }}"
  when: devices is defined
"""


# this function sets up the ansible files needed for template creation. It will create a site.yml and then a main.yml in the tasks folder for each role
def mk_playbook_files():
    with open(site_yml_location, "w") as site_file:
        site_file.write(site_yml_content)
    print("Created site.yml")

    with open(router_tasks_yml_location, "w") as r_task_file:
        r_task_file.write(router_tasks_yml_content)
    print("Created router main.yml in tasks folder")

    with open(switch_tasks_yml_location, "w") as s_task_file:
        s_task_file.write(switch_tasks_yml_content)
    print("Created switch main.yml in tasks folder")

    with open(edge_router_tasks_yml_location, "w") as e_task_file:
        e_task_file.write(edge_router_tasks_yml_content)
    print("Created edge_router main.yml in tasks folder")

    # runs the mk_new_play.py script that creates a yml file with the formatted info from requirements.csv
    mk_new_play.build_inventory(requirements, inventory)
    mk_new_play.yaml_file_creator(requirements)



# runs the ansible playbook
def mk_play_run():
    print("Running ansible-playbook")
    run = subprocess.run(["ansible-playbook", "-i", "/home/student/CSCI5840-Advanced-Network-Automation/Ansible/inventory.yml", "/home/student/CSCI5840-Advanced-Network-Automation/Ansible/site.yml"], stdout=subprocess.PIPE, text=True)
    print(run.stdout)
    if run.returncode == 0:
        print("Playbook completed")



# basic function to use netmiko to configure a device
def Config(man_ip, config_file, username="admin", password="admin"): 
    try:

        login = {
                "device_type": "arista_eos",
                "host": man_ip,
                "username": username,
                "password": password
        }

        with ConnectHandler(**login) as net_connect:
            print(f"Logged in to {man_ip}")
            net_connect.enable()
            output = net_connect.send_config_from_file(config_file)
            print(f"{man_ip} configured")
    except KeyboardInterrupt:
        print("Exiting")


def parse_devices_from_csv(csv_file=requirements):
    # Parse the CSV and return a dictionary {hostname: management_ip}
    devices = {}
    try:
        with open(csv_file, newline="") as file:
            reader = csv.DictReader(file)
            for row in reader:
                hostname = row.get("hostname", "").strip()
                mgmt_ip = row.get("management_ip", "").strip()
                if hostname and mgmt_ip:
                    devices[hostname] = mgmt_ip
        print(f"Parsed {len(devices)} unique devices from {csv_file}")
    except Exception as e:
        print(f"Something went wrong trying to parse {csv_file}: {e}")
    return devices


def topology_config():
    # Configure all devices in parallel using candidate configs.
    devices = parse_devices_from_csv()
    creds = get_device_credentials()
    if not devices:
        print("No devices found to configure.")
        return

    with cf.ThreadPoolExecutor(max_workers=4) as executor:
        futures = []
        for hostname, mgmt_ip in devices.items():
            config_path = os.path.join(candidate_dir, f"{hostname}.txt")
            if not os.path.exists(config_path):
                print(f"No candidate config found for {hostname} ({config_path})")
                continue
            futures.append(executor.submit(Config, man_ip=mgmt_ip, config_file=config_path, username=creds[hostname]["username"], password=creds[hostname]["password"]))

        for future in cf.as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"Thread execution error: {e}")


def rollback_config():
    # Rolls back each device to the most recent golden configuration file.
    devices = parse_devices_from_csv()
    creds = get_device_credentials()
    if not devices:
        print("No devices found for rollback")
        return

    with cf.ThreadPoolExecutor(max_workers=4) as executor:
        futures = []
        for hostname, mgmt_ip in devices.items():
            rollback_matches = glob.glob(os.path.join(golden_dir, f"{hostname}_*.txt"))
            if not rollback_matches:
                print(f"No rollback file found for {hostname}")
                continue

            rollback_file = max(rollback_matches, key=os.path.getmtime)
            futures.append(executor.submit(Config, man_ip=mgmt_ip, config_file=rollback_file, username=creds[hostname]["username"], password=creds[hostname]["password"]))
        for future in cf.as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"Rollback error: {e}")


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



# main function 
def main():
    if "--action" in sys.argv:
        action = sys.argv[sys.argv.index("--action") + 1]
        actions = {"rollback_config": rollback_config, "topology_config": topology_config}
        if action in actions:
            print(f"Running action: {action}")
            actions[action]()
    else:
        mk_playbook_files()
        mk_play_run()
        topology_config()


if __name__ == "__main__":
    main()
