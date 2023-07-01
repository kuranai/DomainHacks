import whoisdomain as whois
from time import sleep
import socket
import datetime
import psycopg
import os
from dotenv import load_dotenv

load_dotenv()

Connectionstring = os.environ["CONNECTIONSTRING"]


def create_connection():
    conn = None
    try:
        conn = psycopg.connect(conninfo=Connectionstring)
    except psycopg.Error as e:
        print(e)

    return conn


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
    should_sleep = False
    if check_dns(domain):
        domain_is_free(domain)
        should_sleep = True
    else:
        # update db, domain is not free
        update_task(conn, "False", domain)
    if should_sleep:
        sleep(2)


conn = create_connection()
with conn:
    counter = 0
    for row in conn.execute("SELECT * FROM domains where status is null"):
        counter += 1
        domain = row[0]
        # check if domain is available
        update_domain(domain)
        if counter % 10 == 0:
            conn.commit()
