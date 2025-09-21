from flask import Flask, render_template, request, redirect, url_for, flash
import csv
import subprocess
import os

app = Flask(__name__)

# CSV file path
csv_file = "/home/student/CSCI5840-Advanced-Network-Automation/Ansible/requirements.csv"
config_gen_script = "/home/student/CSCI5840-Advanced-Network-Automation/Ansible/main.py"

# Home
@app.route("/")
def index():
    return render_template("index.html")

# Dashboards
@app.route("/grafana")
def grafana():
    return redirect("http://localhost:3000")

@app.route("/chronograf")
def chronograf():
    return redirect("http://localhost:8888")

# Device configuration
@app.route("/configure/<device_type>", methods=["GET", "POST"])
def configure(device_type):
    if request.method == "POST":
        form_data = request.form.to_dict()

        # Convert checkboxes (on → TRUE / blank → FALSE)
        for key in ["rip_enabled"]:
            if key in form_data:
                form_data[key] = "TRUE"
            else:
                form_data[key] = "FALSE"

        # Normalize comma-separated fields
        for key in ["vlan_list", "rip_networks", "bgp_networks_ipv4", "bgp_networks_ipv6", "bgp_neighbors", "bgp_neighbors_ipv6", "ospf_networks"]:
            if form_data.get(key):
                form_data[key] = form_data[key].replace(" ", "")

        # Write to CSV
        write_to_csv(form_data)

        # Run Ansible pipeline
        try:
            subprocess.run(["python3", config_gen_script], check=True)
            flash("Configuration saved and templates generated!", "success")
        except subprocess.CalledProcessError as e:
            flash(f"Error running main.py: {e}", "danger")

        return redirect(url_for("index"))

    return render_template("configure.html", device_type=device_type)

def write_to_csv(data):
    # Ensure consistent column order (based on your CSV header)
    headers = [
        "device_type","hostname","username","password","vlan_list",
        "intf_name","intf_desc","intf_switchport_mode","intf_access_vlan","intf_no_switchport","intf_encapsulation",
        "intf_ipv4","intf_ipv6","ospf_process","intf_ospf_area","bgp_asn","router_id","bgp_neighbors_ipv4",
        "bgp_networks_ipv4","bgp_neighbors_ipv6","bgp_networks_ipv6","bgp_redistribute_ospf","bgp_redistribute_ospfv3",
        "ospf_default_info","ospf_redistribute_bgp","ospf_networks",
        "static_ipv4_network","static_ipv4_nexthop","static_ipv6_network","static_ipv6_nexthop",
        "rip_networks","rip_enabled"
    ]

    # Append to CSV
    file_exists = os.path.isfile(csv_file)
    with open(csv_file, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        if not file_exists:
            writer.writeheader()
        writer.writerow(data)

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=80, debug=True)
