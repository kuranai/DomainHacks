import whoisdomain as whois
from time import sleep
import socket
import datetime
import psycopg
import os
from dotenv import load_dotenv

load_dotenv()

Connectionstring = os.environ["Connectionstring"]


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
        + " where name = '"
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
        print(e)
        sleep(60)
    except whois.exceptions.FailedParsingWhoisOutput as e:
        print(e)
    except whois.exceptions.UnknownDateFormat as e:
        print(e)


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
    for row in conn.execute("SELECT * FROM domains where status is null"):
        # get the name of the logo
        name = row[0]
        # check if domain is available
        update_domain(name)
        print(f"{datetime.datetime.now()}: {name}")
        # print time
        # print(datetime.datetime.now())
        conn.commit()
