import requests
import whoisdomain as whois
from time import sleep
import socket
import psycopg
import os
from dotenv import load_dotenv
import dns.resolver
import vpn
from functools import wraps
from time import time
from currency_converter import CurrencyConverter

c = CurrencyConverter()


load_dotenv()

Connectionstring = os.environ["CONNECTIONSTRING"]


def create_connection():
    conn = None
    try:
        conn = psycopg.connect(conninfo=Connectionstring)
    except psycopg.Error as e:
        print(e)
    if conn is None:
        return create_connection()
    return conn


def timed(f):
    @wraps(f)
    def wrapper(*args, **kwds):
        start = time()
        result = f(*args, **kwds)
        elapsed = time() - start
        print(f"{f.__name__} took {elapsed} time to finish")
        return result

    return wrapper


def check_with_api(domain):
    query = "https://domains.revved.com/v1/domainStatus?domains=," + domain
    response = requests.get(query)
    print(response.json())
    # sleep(2)
    if response.status_code == 200:
        data = response.json()
        if "error" in response.json():
            # returnlist = ["Status", "Premium", "Amount", "RetailAmount", "Domain"]
            returnlist = [False, False, None, None, domain]
            return returnlist
        if (
            "status" in data
            and len(data["status"]) > 0
            and "available" in data["status"][0]
        ):
            if data["status"][0]["available"] is True:
                if "premium" in response.json():
                    currency = data["status"][0]["fee"]["currency"]
                    amount = data["status"][0]["fee"]["amount"]
                    retailAmount = data["status"][0]["fee"]["retailAmount"]
                    print(f"{c.convert(amount, currency, 'USD')}")
                    print(f"{c.convert(retailAmount, currency, 'USD')}")
                    returnlist = [True, True, amount, retailAmount, domain]
                    return returnlist
                else:
                    returnlist = [True, False, None, None, domain]
                    return returnlist
        returnlist = [False, False, None, None, domain]
        return returnlist
    elif response.status_code == 429:
        print("change proxy")
        vpn.refresh_connection()
        sleep(5)
        return check_with_api(domain)
    else:
        returnlist = [False, False, None, None, domain]
        return returnlist


def update_task(conn, status, premium, amount, retailAmount, domainname):
    if premium is False:
        sql = (
            "update domains set "
            + "status = "
            + str(status)
            + ", premium = "
            + str(premium)
            + " where domain = '"
            + domainname
            + "'"
        )
    else:
        sql = (
            "update domains set "
            + "status = "
            + str(status)
            + ", premium = "
            + str(premium)
            + ", amount = "
            + str(amount)
            + ", retailAmount = "
            + str(retailAmount)
            + " where domain = '"
            + domainname
            + "'"
        )
    # print(sql)
    cur = conn.cursor()
    cur.execute(sql)
    conn.commit()


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
        if w is not None:
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
    # if check_dns(domain):
    # if check_mx(domain):
    # domain_is_free(domain)
    resultlist = check_with_api(domain)
    conn = create_connection()
    with conn:
        # update_task(conn, status, premium, amount, retailAmount, domainname)
        # returnlist = ["Status", "Premium", "Amount", "RetailAmount", "Domain"]
        update_task(
            conn, resultlist[0], resultlist[1], resultlist[2], resultlist[3], domain
        )
    # else:
    #     # update db, domain is not free
    #     update_task(conn, "False", domain)


# conn = create_connection()
# with conn:
#     counter = 0
#     for row in conn.execute("SELECT * FROM domains where status is null"):
#         counter += 1
#         domain = row[0]
#         # check if domain is available
#         update_domain(domain)
#         conn.commit()


def get_domains_where_status_is_null():
    conn = create_connection()
    with conn:
        domains = [
            row[0]
            for row in conn.execute(
                """select * from domains d 
left join words_sorted ws on ws.word = replace(d."domain",'.','')
where d.status is null 
order by ws.line_number asc"""
            )
        ]
    return domains


for domain in get_domains_where_status_is_null():
    # check if domain is available
    update_domain(domain)
