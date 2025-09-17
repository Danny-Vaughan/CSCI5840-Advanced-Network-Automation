#!/usr/bin/env python3

import csv
import os

def sshInfo():
    try:
        logins = []
        if os.path.exists('sshInfo.csv'):
            with open ('sshInfo.csv', 'r') as csv_file:
                csv_info = csv.DictReader(csv_file)
                for row in csv_info:
                    login = {
                            "device_type": "cisco_ios",
                            "host": row["ip"],
                            "username": row["username"],
                            "password": row["password"],
                            "secret": "netman",
                    }
                    logins.append(login)
            return(logins)
        else:
            print("Something went wrong opening file sshInfo.csv, ensure that it is named correctly and saved in the current working directory")
    except Exception as mistake:
        print(f"Something went wrong: {mistake}")

def main():
    test = sshInfo()
    print(test)

if __name__ == "__main__":
    main()
