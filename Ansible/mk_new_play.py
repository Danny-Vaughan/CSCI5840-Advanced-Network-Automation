#!/usr/bin/env python3
import csv
import yaml

# Input/Output
input_csv_file = "/home/student/CSCI5840-Advanced-Network-Automation/Ansible/requirements.csv"
inventory_file = "/home/student/CSCI5840-Advanced-Network-Automation/Ansible/inventory.yml"

def normalize_value(val):
    if val is None:
        return None
    v = val.strip().upper()
    if v == "TRUE":
        return True
    if v == "FALSE":
        return False
    return val.strip() if val.strip() else None

def build_inventory(input_csv_file, inventory_file):
    # Create a minimal inventory with hostnames per device type
    inventory = {"all": {"children": {}}}
    with open(input_csv_file, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            hostname = row["hostname"].strip()
            device_type = row["device_type"].strip().lower()
            if not hostname:
                continue
            if device_type not in inventory["all"]["children"]:
                inventory["all"]["children"][device_type] = {"hosts": {}}
            inventory["all"]["children"][device_type]["hosts"][hostname] = ""
    with open(inventory_file, "w") as outfile:
        yaml.dump(inventory, outfile, sort_keys=False)
    print(f"Converted {input_csv_file} --> {inventory_file}")


def yaml_file_creator(input_csv):
    devices = {"router": [], "edge_router": [], "switch": []}
    with open(input_csv, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            hostname = row["hostname"].strip()
            if not hostname:
                continue
            device_type = row["device_type"].strip().lower()
            if device_type not in devices:
                continue
            # Check if device already exists
            existing = next((d for d in devices[device_type] if d["hostname"] == hostname), None)
            if not existing:
                # Initialize device
                existing = {
                    "device_type": device_type,
                    "hostname": hostname,
                    "username": row.get("username"),
                    "password": row.get("password"),
                    "vlan_list": row["vlan_list"].split(",") if row.get("vlan_list") else [],
                    "interfaces": [],
                    "routing": {}
                }
                # Routing fields
                routing_fields = [
                    "rip_enabled","rip_networks","router_id","ospf_process",
                    "bgp_asn","bgp_router_id","bgp_neighbors_ipv4","bgp_networks_ipv4",
                    "bgp_neighbors_ipv6","bgp_networks_ipv6","bgp_redistribute_ospf",
                    "bgp_redistribute_ospfv3","ospf_router_id",
                    "ospf_default_info","ospf_redistribute_bgp",
                    "static_ipv4_network","static_ipv4_nexthop",
                    "static_ipv6_network","static_ipv6_nexthop"
                ]
                existing["routing"] = {k: normalize_value(row[k]) for k in routing_fields if row.get(k)}
                rip_networks_str = row.get("rip_networks", "")
                bgp_networks_v6 = row.get("bgp_networks_ipv6", "")
                bgp_networks_v4 = row.get("bgp_networks_ipv4", "")
                if rip_networks_str:
                    existing["routing"]["rip_networks"] = rip_networks_str.split(";")
                if bgp_networks_v6:
                    existing["routing"]["bgp_networks_ipv6"] = bgp_networks_v6.split(";")
                if bgp_networks_v4:
                    existing["routing"]["bgp_networks_ipv4"] = bgp_networks_v4.split(";")
                devices[device_type].append(existing)
            # Interfaces
            if row.get("intf_name"):
                iface = {
                    "name": row.get("intf_name"),
                    "description": row.get("intf_desc") or None,
                    "mode": row.get("intf_switchport_mode") or None,
                    "access_vlan": row.get("intf_access_vlan") or None,
                    "no_switchport": True if row.get("intf_no_switchport") == "TRUE" else False,
                    "encapsulation": row.get("intf_encapsulation") or None,
                    "ipv4": row.get("intf_ipv4") or None,
                    "ipv6": row.get("intf_ipv6") or None,
                    "ospf_area": row.get("intf_ospf_area") or None,
                }
                # Remove empty keys
                iface = {k: v for k, v in iface.items() if v not in [None, "", "FALSE"]}
                existing["interfaces"].append(iface)

    # Dump YAML per device type
    for dtype, dlist in devices.items():
        if dlist:
            filename = f"/home/student/CSCI5840-Advanced-Network-Automation/Ansible/roles/{dtype}/vars/{dtype}.yml"
            with open(filename, "w") as yamlfile:
                yaml.dump({"devices": dlist}, yamlfile, sort_keys=False)
            print(f"Converted {input_csv} --> {dtype}.yml")


def main():
    build_inventory(input_csv_file, inventory_file)
    yaml_file_creator(input_csv_file)


if __name__ == "__main__":
    main()

