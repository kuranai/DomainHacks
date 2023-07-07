import subprocess
import random

"""
Python/subprocesses based Mullvad VPN CLI Package
Used to rotate IP connections via python
"""

__version__ = 1.0


def refresh_connections_list():
    """Get the list of connections and parse"""
    try:
        output = subprocess.check_output("mullvad relay list", shell=True)
    except subprocess.CalledProcessError:
        exit("Mullvad Client isn't installed on your device!")
    connection_lines: list = [
        line.strip("\t\t")
        for line in output.decode().split("\n")
        # if line.strip("\t\t").startswith("at")
    ]
    us_connection_relays: list = []
    for connection_line in connection_lines:
        # if connection_line.startswith("at"):
        us_connection_relays.append(connection_line.split(" ")[0])
    return us_connection_relays


avalible_connections: list = refresh_connections_list()


def refresh_connection():
    """Use CLI to connect to vpn"""
    try:
        output = subprocess.check_output(
            f"mullvad relay set hostname {random.choice(list(refresh_connections_list()))}",
            shell=True,
        )
    except Exception as e:
        print(e)
    try:
        output = subprocess.check_output("mullvad connect", shell=True)
    except Exception as e:
        print(e)


def disconnect():
    """Use CLI to disconnect to vpn"""
    try:
        output = subprocess.check_output("mullvad disconnect", shell=True)
    except Exception as e:
        print(e)
