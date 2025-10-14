from flask import Flask, render_template, request, redirect, url_for, flash
import subprocess
import functions

app = Flask(__name__)
app.config["SECRET_KEY"] = "key"

config_gen_script = "/home/student/CSCI5840-Advanced-Network-Automation/Ansible/main.py"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/grafana")
def grafana():
    return redirect("http://localhost:3000")

@app.route("/chronograf")
def chronograf():
    return redirect("http://localhost:8888")

@app.route('/get_golden_configs')
def get_golden_configs():
    saved_files, timestamp = functions.get_golden_configs()
    return render_template('golden_configs.html', files=saved_files, timestamp=timestamp)

@app.route("/configure", methods=["GET", "POST"])
def configure():
    if request.method == "POST":
        form_data = functions.clean_form_data(request.form)
        operation = form_data.get("operation", "update")
        functions.write_to_csv(form_data, operation)
        try:
            subprocess.run(["python3", config_gen_script])
            flash("Configuration saved and templates generated", "success")
        except:
            flash("Something went wrong", "danger")
    return render_template("configure.html")


@app.route("/run_test", methods=["GET", "POST"])
def run_test():
    if request.method == "POST":
        device_name = request.form["device"]
        test_type = request.form["test_type"]
        param = request.form.get("param", "")
        device = functions.get_device_ip(device_name)

        if test_type == "connectivity":
            output = functions.connectivity_check(device_name, device, param)
        elif test_type == "bgp":
            output = functions.bgp_neighbors(device_name, device)
        elif test_type == "route":
            output = functions.route_finder(device_name, device, param)
        else:
            output = "Unknown test selected."

        return render_template("test_results.html", output=output)

    # Get form info for device selection
    devices = ["R1", "R2", "R3", "R4", "S1", "S2", "S3", "S4"]
    return render_template("test_form.html", devices=devices)



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80, debug=True)


