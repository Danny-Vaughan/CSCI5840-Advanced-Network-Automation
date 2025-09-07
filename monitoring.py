#!/usr/bin/env python3

import pyshark
import os
import re
import subprocess

devices = {"R1": "10.10.4.1","R2": "10.10.4.2","R3": "10.10.4.3","R4": "10.10.4.4","S1": "10.10.40.3","S2": "10.10.40.4","S3": "10.10.4.7","S4": "10.10.4.8"}

def cpu_monitor():
    for device in devices.items():
        hostname = device[0]
        ip = device[1]
        cpu_oid = "iso.3.6.1.2.1.25.3.3.1.2.1"
        cpu = subprocess.run(["snmpget", "-v2c", "-c", "public", ip, cpu_oid], capture_output=True, text=True)
        cpu_output = cpu.stdout.strip()
        match = re.search(r'INTEGER: (\d+)', cpu_output)
        value = match.group(1)
        print(hostname+" CPU Utilization: "+value)

cpu_monitor()
