#!/usr/bin/env python3

import pyshark

def trap_monitor():
    interface = "eth1"
    pcap_file = "/root/packet_capture.pcap"
    capture = pyshark.LiveCapture(interface=interface, bpf_filter="udp port 162", output_file=pcap_file)
    try:
        capture.sniff(timeout=None)
    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        capture.close()
        print(f"Capture saved to {pcap_file}")


if __name__ == "__main__":
    trap_monitor()
