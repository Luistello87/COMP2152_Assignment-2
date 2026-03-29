"""
Author: Luis Tello
Assignment: #2
Description: Port Scanner — A tool that scans a target machine for open network ports
"""

# TODO: Import the required modules (Step ii)
import socket
import threading
import sqlite3
import os
import platform
import datetime


# TODO: Print Python version and OS name (Step iii)
print(f"Python Version: {platform.python_version()}")
print(f"Operating System: {os.name}")


# TODO: Create the common_ports dictionary (Step iv)
# Stores common port numbers and their typical service names
common_ports = {
    20: "FTP Data",
    21: "FTP",
    22: "SSH",
    23: "Telnet",
    25: "SMTP",
    53: "DNS",
    67: "DHCP",
    68: "DHCP",
    69: "TFTP",
    80: "HTTP",
    110: "POP3",
    123: "NTP",
    143: "IMAP",
    161: "SNMP",
    443: "HTTPS",
    3306: "MySQL",
    3389: "RDP",
    8080: "HTTP-Alt"
}


# TODO: Create the NetworkTool parent class (Step v)
# - Constructor: takes target, stores as private self.__target
# - @property getter for target
# - @target.setter with empty string validation
# - Destructor: prints "NetworkTool instance destroyed"
class NetworkTool:
    def __init__(self, target):
        self.__target = target

    # Q3: What is the benefit of using @property and @target.setter?
    # Using @property and @target.setter helps control how the target value is accessed and changed.
    # It lets us hide the internal attribute but still expose a clean interface to other code.
    # In this case, it stops the target from being set to an empty string and makes the class safer to use.
    @property
    def target(self):
        return self.__target

    @target.setter
    def target(self, value):
        if value.strip() == "":
            raise ValueError("Target cannot be empty.")
        self.__target = value

    def __del__(self):
        print("NetworkTool instance destroyed")


# Q1: How does PortScanner reuse code from NetworkTool?
# PortScanner reuses code from NetworkTool by inheriting from it as a child class.
# It does not need to rewrite that code, which reduces duplication and keeps the design cleaner.

# TODO: Create the PortScanner child class that inherits from NetworkTool (Step vi)
# - Constructor: call super().__init__(target), initialize self.scan_results = [], self.lock = threading.Lock()
# - Destructor: print "PortScanner instance destroyed", call super().__del__()
class PortScanner(NetworkTool):
    def __init__(self, target):
        super().__init__(target)
        self.scan_results = []
        self.lock = threading.Lock()

    def __del__(self):
        print("PortScanner instance destroyed")
        super().__del__()
    def scan_port(self, port):
        sock = None

    # Q4: What would happen without try-except here?
    # Without try-except, any socket error during scanning could crash the whole program.
    # For example, a network issue or unreachable host might raise an exception and stop all remaining scans.
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)

            result = sock.connect_ex((self.target, port))

            if result == 0:
                status = "Open"
            else:
                status = "Closed"

            service_name = common_ports.get(port, "Unknown")

            with self.lock:
                self.scan_results.append((port, status, service_name))

        except socket.error as e:
            print(f"Error scanning port {port}: {e}")

        finally:
            if sock:
                sock.close()

    def get_open_ports(self):
        return [result for result in self.scan_results if result[1] == "Open"]

    # Q2: Why do we use threading instead of scanning one port at a time?
    # We use threading so that multiple ports can be scanned in parallel instead of waiting for each one to finish.
    # With threads, each port scan runs in its own thread, which makes the overall scan much faster from the user's perspective.
    # This is especially helpful on slower networks or when scanning larger port ranges.
    def scan_range(self, start_port, end_port):
        threads = []

        for port in range(start_port, end_port + 1):
            thread = threading.Thread(target=self.scan_port, args=(port,))
            threads.append(thread)

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()


# TODO: Create save_results(target, results) function (Step vii)
# - Connect to scan_history.db
# - CREATE TABLE IF NOT EXISTS scans (id, target, port, status, service, scan_date)
# - INSERT each result with datetime.datetime.now()
# - Commit, close
# - Wrap in try-except for sqlite3.Error
def save_results(target, results):
    try:
        conn = sqlite3.connect("scan_history.db")
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                target TEXT,
                port INTEGER,
                status TEXT,
                service TEXT,
                scan_date TEXT
            )
        """)

        for port, status, service in results:
            cursor.execute("""
                INSERT INTO scans (target, port, status, service, scan_date)
                VALUES (?, ?, ?, ?, ?)
            """, (target, port, status, service, datetime.datetime.now()))

        conn.commit()
        conn.close()

    except sqlite3.Error as e:
        print(f"Database error: {e}")


# TODO: Create load_past_scans() function (Step viii)
# - Connect to scan_history.db
# - SELECT all from scans
# - Print each row in readable format
# - Handle missing table/db: print "No past scans found."
# - Close connection
def load_past_scans():
    try:
        conn = sqlite3.connect("scan_history.db")
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM scans")
        rows = cursor.fetchall()

        if rows:
            for row in rows:
                print(
                    f"ID: {row[0]}, Target: {row[1]}, Port: {row[2]}, "
                    f"Status: {row[3]}, Service: {row[4]}, Date: {row[5]}"
                )
        else:
            print("No past scans found.")

        conn.close()

    except sqlite3.Error:
        print("No past scans found.")


# ============================================================
# MAIN PROGRAM
# ============================================================
if __name__ == "__main__":
    # TODO: Get user input with try-except (Step ix)
    # - Target IP (default "127.0.0.1" if empty)
    # - Start port (1-1024)
    # - End port (1-1024, >= start port)
    # - Catch ValueError: "Invalid input. Please enter a valid integer."
    # - Range check: "Port must be between 1 and 1024."
    try:
        target = input("Enter target IP address (default 127.0.0.1): ").strip()
        if target == "":
            target = "127.0.0.1"

        start_port = int(input("Enter start port (1-1024): "))
        end_port = int(input("Enter end port (1-1024): "))

        if start_port < 1 or start_port > 1024 or end_port < 1 or end_port > 1024:
            print("Port must be between 1 and 1024.")
        elif end_port < start_port:
            print("End port must be greater than or equal to start port.")
        else:
            scanner = PortScanner(target)
            print(f"Scanning {target} from port {start_port} to {end_port}...")

            # TODO: After valid input (Step x)
            # - Create PortScanner object
            # - Print "Scanning {target} from port {start} to {end}..."
            # - Call scan_range()
            # - Call get_open_ports() and print results
            # - Print total open ports found
            # - Call save_results()
            # - Ask "Would you like to see past scan history? (yes/no): "
            # - If "yes", call load_past_scans()

            scanner.scan_range(start_port, end_port)

            open_ports = scanner.get_open_ports()

            print("\nOpen Ports:")
            for port, status, service in open_ports:
                print(f"Port {port}: {status} ({service})")

            print(f"\nTotal open ports found: {len(open_ports)}")

            save_results(target, scanner.scan_results)

            choice = input("Would you like to see past scan history? (yes/no): ").strip().lower()
            if choice == "yes":
                load_past_scans()

    except ValueError:
        print("Invalid input. Please enter a valid integer.")


# Q5: New Feature Proposal
# TODO: Your 2-3 sentence description here... (Part 2, Q5)
# I think that a useful new feature would be to add a command-line option to export scan results to a CSV file.
# This would let users open their scan history in Excel or other tools for further analysis and reporting.
# It would also make it easier to share scan output with teammates or include it in documentation.
# Diagram: See diagram_101580076.png in the repo.