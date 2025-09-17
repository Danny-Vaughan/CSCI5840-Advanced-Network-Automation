#!/usr/bin/env python3

import argparse
import re
import sys

def ArgParse_Helper():
    parser = argparse.ArgumentParser(description="This is a program that will help you make sure you have a valid IP address")
    parser.add_argument("address",action='store', help="IP address")
    parser.add_argument("--version",action='version',version='Version1.0')
    args=parser.parse_args()
    return(args)

def check(address):
    octet_list = address.split(".")
    is_valid = 1
    if len(octet_list) != 4:
        is_valid = 0
        print("An IP address that doesn't have four octets was found")
    
    try:
        for octet in octet_list:
            if int(octet) > 255 or int(octet) < 0:
                is_valid = 0
                print("An IP address with one or more octets that is not a number between 0 and 255 was found")
    except: 
        is_valid = 0
        print("An IP address with an octet that either is not a number or doesn't exist was found")
        sys.exit()
    if int(octet_list[0]) >= 224 and int(octet_list[0]) <= 239:
        is_valid = 0
        print("A multicast address was found")
    if int(octet_list[0]) == 127:
        is_valid = 0
        print("A loopback address was found")
    if int(octet_list[0]) == 169 and int(octet_list[1]) == 254:
        is_valid = 0
        print("A link local address was found")
    if int(octet_list[0]) == 255 and int(octet_list[1]) == 255 and int(octet_list[2]) == 255 and int(octet_list[3]) == 255:
        is_valid = 0
        print("The broadcast address was found")
    if int(octet_list[0]) >= 240 and int(octet_list[0]) <= 255:
        is_valid = 0
        print("An IP address in the experimental range was found")
    if is_valid == 1:
        return("Good")
    

def main():
    args = ArgParse_Helper()
    address = args.address
    check(address)

if __name__ == "__main__":
    main()
