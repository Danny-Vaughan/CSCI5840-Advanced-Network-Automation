#!/usr/bin/env python3

import os
import mk_new_play
from netmiko import ConnectHandler
import concurrent.futures as cf
import subprocess

site_yml_location = "/home/student/CSCI5840-Advanced-Network-Automation/Ansible/site.yml"
router_tasks_yml_location = "/home/student/CSCI5840-Advanced-Network-Automation/Ansible/roles/router/tasks/main.yml"
switch_tasks_yml_location = "/home/student/CSCI5840-Advanced-Network-Automation/Ansible/roles/switch/tasks/main.yml"
edge_router_tasks_yml_location = "/home/student/CSCI5840-Advanced-Network-Automation/Ansible/roles/edge_router/tasks/main.yml"
requirements = "/home/student/CSCI5840-Advanced-Network-Automation/Ansible/requirements.csv"
inventory = "/home/student/CSCI5840-Advanced-Network-Automation/Ansible/inventory.yml"

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
    dest: "/home/student/CSCI5840-Advanced-Network-Automation/Ansible/configs/{{item.hostname}}.txt"
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
    dest: "/home/student/CSCI5840-Advanced-Network-Automation/Ansible/configs/{{item.hostname}}.txt"
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
    dest: "/home/student/CSCI5840-Advanced-Network-Automation/Ansible/configs/{{item.hostname}}.txt"
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
def Config(man_ip, config_file): 
    try:

        login = {
                "device_type": "arista_eos",
                "host": f"{man_ip}",
                "username": f"admin",
                "password": f"admin"
        }

        with ConnectHandler(**login) as net_connect:
            print(f"Logged in to {man_ip}")
            net_connect.enable()
            output = net_connect.send_config_from_file(config_file)
            print(f"{man_ip} configured")
    except KeyboardInterrupt:
        print("Exiting")


# uses the config function and concurrency to run the function for each router at the same time   
def topology_config():
    config_ip_list = ["172.20.20.2", "172.20.20.10", "172.20.20.15", "172.20.20.5", "172.20.20.9", "172.20.20.6", "172.20.20.4", "172.20.20.16"]
    config_file_list = ["/home/student/CSCI5840-Advanced-Network-Automation/Ansible/configs/R1.txt", "/home/student/CSCI5840-Advanced-Network-Automation/Ansible/configs/R2.txt", "/home/student/CSCI5840-Advanced-Network-Automation/Ansible/configs/R3.txt", "/home/student/CSCI5840-Advanced-Network-Automation/Ansible/configs/R4.txt", "/home/student/CSCI5840-Advanced-Network-Automation/Ansible/configs/S1.txt", "/home/student/CSCI5840-Advanced-Network-Automation/Ansible/configs/S2.txt", "/home/student/CSCI5840-Advanced-Network-Automation/Ansible/configs/S3.txt", "/home/student/CSCI5840-Advanced-Network-Automation/Ansible/configs/S4.txt"]
    with cf.ThreadPoolExecutor(max_workers=4) as executor:
        futures = []
        for ip, config_file in zip(config_ip_list, config_file_list):
            futures.append(executor.submit(Config, man_ip=str(ip), config_file=config_file))


# main function 
def main():
    mk_playbook_files()
    mk_play_run()


if __name__ == "__main__":
    main()
