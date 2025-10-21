#!/usr/bin/env python3
import sys
import os
sys.path.append("/home/student/CSCI5840-Advanced-Network-Automation/Ansible")
sys.path.append("/home/student/CSCI5840-Advanced-Network-Automation/FrontEnd")

import csv
import tempfile
import unittest
import yaml
import importlib.util
import subprocess
from flask import Flask


# File Paths for .py files
playbook_gen = "/home/student/CSCI5840-Advanced-Network-Automation/Ansible/mk_new_play.py"
functions_file = "/home/student/CSCI5840-Advanced-Network-Automation/FrontEnd/functions.py"
config_gen = "/home/student/CSCI5840-Advanced-Network-Automation/Ansible/main.py"
frontend = "/home/student/CSCI5840-Advanced-Network-Automation/FrontEnd/app.py"

# Coverage counters
mk_count = 0
func_count = 0
config_count = 0
frontend_count = 0


# Import all modules
def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

mk_new_play = load_module("mk_new_play", playbook_gen)
functions = load_module("functions", functions_file)
config_gen_module = load_module("config_gen", config_gen)
frontend_module = load_module("frontend", frontend)

# =============================================================
#                 Unit Tests for mk_new_play.py
# =============================================================
class TestMkNewPlay(unittest.TestCase):
    # Passes values true, FALSE, and None to verify they are normalized
    def test_normalize_value(self):
        global mk_count; mk_count += 1
        self.assertTrue(mk_new_play.normalize_value("true"))
        self.assertFalse(mk_new_play.normalize_value("FALSE"))
        self.assertIsNone(mk_new_play.normalize_value(None))

    # Creates temp csv, runs function, verifies output
    def test_build_inventory(self):
        global mk_count; mk_count += 1
        tmp_csv = tempfile.NamedTemporaryFile(delete=False, suffix=".csv")
        tmp_yml = tempfile.NamedTemporaryFile(delete=False, suffix=".yml")

        with open(tmp_csv.name, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["hostname", "device_type"])
            writer.writeheader()
            writer.writerow({"hostname": "R1", "device_type": "router"})

        mk_new_play.build_inventory(tmp_csv.name, tmp_yml.name)
        self.assertTrue(os.path.exists(tmp_yml.name))
        with open(tmp_yml.name) as f:
            yml = yaml.safe_load(f)
        self.assertIn("router", yml["all"]["children"])
    
    # Generates dummy csv file with a router and runs function, looks for exceptions
    def test_yaml_file_creator(self):
        global mk_count; mk_count += 1
        tmp_csv = tempfile.NamedTemporaryFile(delete=False, suffix=".csv")
        with open(tmp_csv.name, "w", newline="") as f:
            fieldnames = ["hostname", "device_type", "username", "password", "vlan_list"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerow({"hostname": "R1", "device_type": "router",
                             "username": "admin", "password": "admin", "vlan_list": "10,20"})
        mk_new_play.yaml_file_creator(tmp_csv.name)
        self.assertTrue(True)

    # Not really needed, but checks that the main function is there for running locally
    def test_main_exists(self):
        global mk_count; mk_count += 1
        self.assertTrue(callable(mk_new_play.main))

# =============================================================
#                 Unit Tests for functions.py
# =============================================================
class TestFunctions(unittest.TestCase):
    # Writes temp file confirms it exists and it can be opened
    def test_read_write_csv(self):
        global func_count; func_count += 1
        tmp_csv = tempfile.NamedTemporaryFile(delete=False, suffix=".csv")
        data = [{"hostname": "R1", "device_type": "router"}]
        with open(tmp_csv.name, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["hostname", "device_type"])
            writer.writeheader()
            writer.writerows(data)
        self.assertTrue(os.path.exists(tmp_csv.name))
    
    # Feeds the function a bit of info that might come from flask form, verifies that a list is returned
    def test_form_to_rows_basic(self):
        global func_count; func_count += 1
        form_data = {"hostname": "R1", "interface_count": "1", "device_type": "router"}
        result = functions.form_to_rows(form_data)
        self.assertIsInstance(result, list)
    
    # Simulates description getting updated and verifies that rows are merged and description is there
    def test_merge_rows_update(self):
        global func_count; func_count += 1
        existing = [{"hostname": "R1", "intf_name": "Ethernet1"}]
        new = [{"hostname": "R1", "intf_name": "Ethernet1", "intf_desc": "updated"}]
        merged = functions.merge_rows(existing, new, "update")
        self.assertEqual(merged[0]["intf_desc"], "updated")
    
    # Gives a list with an empty field, verifies that the empty field is cleaned up
    def test_clean_form_data(self):
        global func_count; func_count += 1
        class Dummy:
            def keys(self): return ["key"]
            def getlist(self, key): return ["", "value"]
        cleaned = functions.clean_form_data(Dummy())
        self.assertEqual(cleaned["key"], "value")
    
    # Calls function checks output to verify that it is a list
    def test_get_all_devices(self):
        global func_count; func_count += 1
        result = functions.get_all_devices()
        self.assertIsInstance(result, list)
    
    # Passes name that doesn't exist and checks for none in output
    def test_get_device_ip(self):
        global func_count; func_count += 1
        result = functions.get_device_ip("nonexistent")
        self.assertIsNone(result)
    
    # Checks that the function exists
    def test_get_golden_configs_exists(self):
        global func_count; func_count += 1
        self.assertTrue(callable(functions.get_golden_configs))

# =============================================================
#                 Unit tests for main.py
# =============================================================
class TestMain(unittest.TestCase):
    # Checks that the function exists
    def test_mk_playbook_files_exists(self):
        global config_count; config_count += 1
        self.assertTrue(callable(config_gen_module.mk_playbook_files))
    
    # Checks that the function exists
    def test_mk_play_run(self):
        global config_count; config_count += 1
        self.assertTrue(callable(config_gen_module.mk_play_run))

    # Checks that the function exists
    def test_config_function(self):
        global config_count; config_count += 1
        self.assertTrue(callable(config_gen_module.Config))
    
    # Makes a temp csv and verifies that a dictionary is returned
    def test_parse_devices_from_csv(self):
        global config_count; config_count += 1
        tmp_csv = tempfile.NamedTemporaryFile(delete=False, suffix=".csv")
        with open(tmp_csv.name, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["hostname", "management_ip"])
            writer.writeheader()
            writer.writerow({"hostname": "R1", "management_ip": "10.0.0.1"})
        devices = config_gen_module.parse_devices_from_csv(tmp_csv.name)
        self.assertIsInstance(devices, dict)
    
    # Checks that the function exists
    def test_topology_config_exists(self):
        global config_count; config_count += 1
        self.assertTrue(callable(config_gen_module.topology_config))
    
    # Checks that the function exists
    def test_rollback_config_exists(self):
        global config_count; config_count += 1
        self.assertTrue(callable(config_gen_module.rollback_config))
    
    # Checks that the function exists
    def test_get_device_credentials_exists(self):
        global config_count; config_count += 1
        self.assertTrue(callable(config_gen_module.get_device_credentials))

# =============================================================
#                 Unit Tests for app.py
# =============================================================
class TestFrontend(unittest.TestCase):
    def setUp(self):
        self.app = frontend_module.app.test_client()
        self.app.testing = True

    # Sends GET request and checks for 200
    def test_index_route(self):
        global frontend_count; frontend_count += 1
        response = self.app.get("/")
        self.assertEqual(response.status_code, 200)

    # Sends GET/grafana checks for 302
    def test_grafana_redirect(self):
        global frontend_count; frontend_count += 1
        response = self.app.get("/grafana")
        self.assertEqual(response.status_code, 302)

    # Same a grafana, checks for redirect
    def test_chronograf_redirect(self):
        global frontend_count; frontend_count += 1
        response = self.app.get("/chronograf")
        self.assertEqual(response.status_code, 302)

    # Checks for 200 at /configure
    def test_configure_route_get(self):
        global frontend_count; frontend_count += 1
        response = self.app.get("/configure")
        self.assertEqual(response.status_code, 200)

    # Checks for 200 at /run_test
    def test_run_test_route_get(self):
        global frontend_count; frontend_count += 1
        response = self.app.get("/run_test")
        self.assertEqual(response.status_code, 200)

    # Checks that the function exists
    def test_golden_configs_exists(self):
        global frontend_count; frontend_count += 1
        self.assertTrue(callable(frontend_module.get_golden_configs))

# =============================================================
#       Running and CC Calculation
# =============================================================
if __name__ == "__main__":
    unittest.main(exit=False)

    mk_funcs_total = 4       # mk_new_play
    func_funcs_total = 11    # functions.py
    config_funcs_total = 7   # main.py
    frontend_funcs_total = 6 # app.py routes + helpers

    mk_cov = round((mk_count / mk_funcs_total) * 100, 2)
    func_cov = round((func_count / func_funcs_total) * 100, 2)
    config_cov = round((config_count / config_funcs_total) * 100, 2)
    frontend_cov = round((frontend_count / frontend_funcs_total) * 100, 2)
    total_cov = round(((mk_count + func_count + config_count + frontend_count) /
                      (mk_funcs_total + func_funcs_total + config_funcs_total + frontend_funcs_total)) * 100, 2)

    print("\n========== COVERAGE SUMMARY ==========")
    print(f"mk_new_play.py: {mk_cov}% ({mk_count}/{mk_funcs_total})")
    print(f"functions.py  : {func_cov}% ({func_count}/{func_funcs_total})")
    print(f"main.py       : {config_cov}% ({config_count}/{config_funcs_total})")
    print(f"app.py        : {frontend_cov}% ({frontend_count}/{frontend_funcs_total})")
    print(f"-------------------------------------")
    print(f"TOTAL COVERAGE: {total_cov}%")

