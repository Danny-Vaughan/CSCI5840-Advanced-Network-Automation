import csv
import os
import re
import sys
import pytz
import subprocess
from datetime import datetime
from netmiko import ConnectHandler


requirements = "/home/student/CSCI5840-Advanced-Network-Automation/Ansible/requirements.csv"

# Define headers once so writer knows the correct fields
def get_fieldnames():
    if os.path.exists(requirements):
        with open(requirements, "r", newline="") as file:
            data = csv.DictReader(file)
            fieldnames = data.fieldnames
            return fieldnames

fieldnames = get_fieldnames()

# Read requirements.csv for configuration and template generation functions
def read_csv():
    """Read CSV into list of dictionaries"""
    if not os.path.exists(requirements):
        return []
    with open(requirements, "r", newline="") as file:
        return list(csv.DictReader(file))


def write_csv(rows):
    """Write list of dictionaries back to CSV with proper headers."""
    with open(requirements, "w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def form_to_rows(form_data):
    """
    Convert submitted form data into rows for the CSV.
    Each interface gets its own row.
    """
    hostname = form_data.get("hostname")
    interface_count = int(form_data.get("interface_count", 0))

    # Start with all base (non-interface) fields
    base_fields = {key: form_data.get(key, "") for key in fieldnames if not key.startswith("intf_")}

    # Normalize routing fields
    base_fields["router_id"] = form_data.get("router_id", "")
    base_fields["rip_enabled"] = "TRUE" if form_data.get("rip_enabled") in ("TRUE", "true", "on", "1") else "FALSE"
    base_fields["rip_networks"] = ";".join(
        [n.strip() for n in form_data.get("rip_networks", "").split(";") if n.strip()]
    )
    base_fields["ospf_networks"] = ";".join(
        [n.strip() for n in form_data.get("ospf_networks", "").split(";") if n.strip()]
    )

    rows = []
    for i in range(1, interface_count + 1):
        row = base_fields.copy()
        row["device_type"] = form_data.get("device_type", "")
        row["hostname"] = hostname
        row["intf_name"] = form_data.get(f"intf_name_{i}", "")
        row["intf_desc"] = form_data.get(f"intf_desc_{i}", "")
        row["intf_switchport_mode"] = form_data.get(f"intf_switchport_mode_{i}", "")
        row["intf_access_vlan"] = form_data.get(f"intf_access_vlan_{i}", "")
        row["intf_no_switchport"] = form_data.get(f"intf_no_switchport_{i}", "")
        row["intf_encapsulation"] = form_data.get(f"intf_encapsulation_{i}", "")
        row["intf_ipv4"] = form_data.get(f"intf_ipv4_{i}", "")
        row["intf_ipv6"] = form_data.get(f"intf_ipv6_{i}", "")
        row["intf_ospf_area"] = form_data.get(f"intf_ospf_area_{i}", "")
        rows.append(row)
    return rows

def merge_rows(existing_rows, new_rows, operation="update"):
    """
    Merge new rows into existing rows based on operation type.
    - overwrite: remove old rows for hostname, replace with new
    - update: update rows that match intf_name, add missing ones
    """
    if not new_rows:
        return existing_rows

    hostname = new_rows[0]["hostname"]

    if operation == "overwrite":
        # Remove all existing rows for this hostname
        filtered = [r for r in existing_rows if r["hostname"] != hostname]
        return filtered + new_rows

    elif operation == "update":
        updated = []
        found_interfaces = {row["intf_name"]: row for row in new_rows}

        for row in existing_rows:
            if row["hostname"] == hostname and row["intf_name"] in found_interfaces:
                # Update only changed fields
                updated_row = row.copy()
                for k, v in found_interfaces[row["intf_name"]].items():
                    if v:  # only overwrite if new value is not empty
                        updated_row[k] = v
                updated.append(updated_row)
                del found_interfaces[row["intf_name"]]  # remove from "to add"
            else:
                updated.append(row)

        # Add any new interfaces not in existing_rows
        updated.extend(found_interfaces.values())
        return updated

    else:
        raise ValueError(f"Unknown operation: {operation}")


def write_to_csv(form_data, operation):
    """Main entry: process form data and write to CSV with merge/update logic."""
    existing = read_csv()
    new_rows = form_to_rows(form_data)
    merged = merge_rows(existing, new_rows, operation)
    write_csv(merged)


def clean_form_data(raw_form):
    """
    Clean a Flask request.form ImmutableMultiDict:
    - If multiple values exist for the same key, pick the last non-empty one.
    - If all are empty, fall back to the last value.
    """
    form_data = {}
    for key in raw_form.keys():
        values = raw_form.getlist(key)
        chosen = ""
        for v in reversed(values):
            if v is not None and str(v).strip() != "":
                chosen = v
                break
        if chosen == "" and values:
            chosen = values[-1]
        form_data[key] = chosen
    return form_data


# Health check portal functions
def connectivity_check(hostname, man_ip, target_ip):
    creds = get_device_credentials()
    router = {
        "device_type": "arista_eos",
        "ip": f"{man_ip}",
        "username": creds[hostname]["username"],
        "password": creds[hostname]["password"],
    }
    try:
        with ConnectHandler(**router) as net_connect:
            net_connect.enable()
            output = net_connect.send_command(f"ping {target_ip}")
            return output
    except Exception as e:
        return f"Error: {e}"

def bgp_neighbors(hostname, man_ip):
    creds = get_device_credentials()
    router = {
        "device_type": "arista_eos",
        "ip": f"{man_ip}",
        "username": creds[hostname]["username"],
        "password": creds[hostname]["password"],
    }
    try:
        with ConnectHandler(**router) as net_connect:
            output = net_connect.send_command("show ip bgp summ")
            if not output:
                return f"no bgp configuration found"
            neighbors = re.findall(r"(\d+\.\d+\.\d+\.\d+)", output)
            return(f"BGP neighbors: {neighbors[1:]}")
    except Exception as e:
        return f"Error: {e}"

def route_finder(hostname, man_ip, search_term):
    creds = get_device_credentials()
    router = {
        "device_type": "arista_eos",
        "ip": f"{man_ip}",
        "username": creds[hostname]["username"],
        "password": creds[hostname]["password"],
    }
    try:
        with ConnectHandler(**router) as net_connect:
            if search_term:
                output = net_connect.send_command(f"show ip route | inc {search_term}")
            else:
                output = net_connect.send_command("show ip route")
            return(output)
    except Exception as e:
        return f"Error: {e}"

# Device selection for health check portal
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

def get_all_devices():
    return list(devices.keys())

def get_device_ip(name):
    return devices.get(name)
    

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


# main function 
def main():
    if "--action" in sys.argv:
        action = sys.argv[sys.argv.index("--action") + 1]
        actions = {"get_golden_configs": get_golden_configs}
        if action in actions:
            print(f"Running action: {action}")
            actions[action]()
    else:
        get_golden_configs()


if __name__ == "__main__":
    main()
