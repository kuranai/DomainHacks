import subprocess
import random

"""
Python/subprocesses based Mullvad VPN CLI Package
Used to rotate IP connections via python
"""

__version__ = 1.0


def is_european_country_code(s):
    # This is the list of European Alpha-2 country codes
    european_country_codes = [
        "AL",
        "AD",
        "AT",
        "BY",
        "BE",
        "BA",
        "BG",
        "HR",
        "CY",
        "CZ",
        "DK",
        "EE",
        "FO",
        "FI",
        "FR",
        "DE",
        "GI",
        "GR",
        "GG",
        "VA",
        "HU",
        "IS",
        "IE",
        "IM",
        "IT",
        "JE",
        "XK",
        "LV",
        "LI",
        "LT",
        "LU",
        "MT",
        "MD",
        "MC",
        "ME",
        "NL",
        "MK",
        "NO",
        "PL",
        "PT",
        "RO",
        "RU",
        "SM",
        "RS",
        "SK",
        "SI",
        "ES",
        "SJ",
        "SE",
        "CH",
        "UA",
        "GB",
        "AX",
    ]

    # Extract the first two characters of the string
    code = s[:2].upper()

    # Check if the code is in the list
    if code in european_country_codes:
        return True
    else:
        return False


def refresh_connections_list():
    """Get the list of connections and parse"""
    try:
        output = subprocess.check_output("mullvad relay list", shell=True)
    except subprocess.CalledProcessError:
        exit("Mullvad Client isn't installed on your device!")
    connection_lines: list = [
        line.strip("\t\t")
        for line in output.decode().split("\n")
        if is_european_country_code(line.strip("\t\t"))
    ]
    us_connection_relays: list = []
    for connection_line in connection_lines:
        if is_european_country_code(connection_line):
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
