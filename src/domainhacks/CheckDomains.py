import requests
import whoisdomain as whois
from time import sleep
import socket
import psycopg
import os
from dotenv import load_dotenv
import dns.resolver

load_dotenv()

Connectionstring = os.environ["CONNECTIONSTRING"]


def create_connection():
    conn = None
    try:
        conn = psycopg.connect(conninfo=Connectionstring)
    except psycopg.Error as e:
        print(e)

    return conn


def check_with_api(domain):
    query = "https://domains.revved.com/v1/domainStatus?domains=," + domain
    response = requests.get(query)
    print(response.json())
    sleep(2)
    if response.status_code == 200:
        if "error" in response.json():
            return False
        data = response.json()
        if (
            "status" in data
            and len(data["status"]) > 0
            and "available" in data["status"][0]
        ):
            if data["status"][0]["available"] == True:
                return True
        return False
    else:
        return False


def update_task(conn, status, domainname):
    sql = (
        "update domains set "
        + "status = "
        + status
        + " where domain = '"
        + domainname
        + "'"
    )
    # print(sql)
    cur = conn.cursor()
    cur.execute(sql)
    # conn.commit()


# check if domain has a record
def check_dns(domain):
    # dns lookup
    try:
        socket.gethostbyname(domain)
        return False
    except socket.gaierror:
        return True


def check_mx(domain):
    try:
        # Attempt to retrieve the MX records for the domain
        mx_records = dns.resolver.resolve(domain, "MX")
        # If we find MX records, the domain is likely taken
        return False
    except (
        dns.resolver.NoAnswer,
        dns.resolver.NXDOMAIN,
        dns.resolver.NoNameservers,
        dns.resolver.LifetimeTimeout,
    ):
        # If we don't find MX records, the domain may be available
        return True


def log_exception(domain, e):
    update_task(conn, "False", domain)
    print(f"Domain: {domain} as the following error: {e}")


# check if domain is available with whois
def domain_is_free(domain):
    try:
        w = whois.query(domain)
        if w != None:
            # update db, domain is not free
            update_task(conn, "False", domain)
        else:
            # update db, domain is free
            update_task(conn, "True", domain)
    # catch exception and print error
    except whois.exceptions.WhoisCommandFailed as e:
        log_exception(domain, e)
        sleep(60)
    except whois.exceptions.FailedParsingWhoisOutput as e:
        log_exception(domain, e)
    except whois.exceptions.UnknownDateFormat as e:
        log_exception(domain, e)
    except whois.exceptions.UnknownTld as e:
        log_exception(domain, e)
    except whois.exceptions.WhoisPrivateRegistry as e:
        log_exception(domain, e)


def update_domain(domain):
    if check_dns(domain):
        # if check_mx(domain):
        # domain_is_free(domain)
        if check_with_api(domain):
            update_task(conn, "True", domain)
        else:
            update_task(conn, "False", domain)
    else:
        # update db, domain is not free
        update_task(conn, "False", domain)


conn = create_connection()
with conn:
    counter = 0
    for row in conn.execute("SELECT * FROM domains where status is null"):
        counter += 1
        domain = row[0]
        # check if domain is available
        update_domain(domain)
        conn.commit()
