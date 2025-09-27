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



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80, debug=True)


