import boto3
import datetime
import json
import socket
import ssl

ssl_domains = [
    # USASpending API
    'spending-api.us',
    'spending-api-staging.us',
    'spending-api-dev.us',
    'spending-api-sandbox.us',

    # USASpending Website (Publication)
    'spendingdata.us',
    'staging.spendingdata.us',
    'dev.spendingdata.us',
    'sandbox.spendingdata.us',

    # Broker Website
    'broker.usaspending.gov',
    'alpha-broker.usaspending.gov',
    'alpha-broker-staging.usaspending.gov',
    'alpha-broker-dev.usaspending.gov',
    'alpha-broker-sandbox.usaspending.gov',

    # Broker API
    # Missing broker-api.usaspending.gov (coming before 2/22/17)
    'alpha-broker-api.usaspending.gov',
    'alpha-broker-staging-api.usaspending.gov',
    'alpha-broker-dev-api.usaspending.gov',

    ]


def check_cert_valid_expiration(domain, days_to_warn=14):

    # Open connection
    sock = ssl.create_default_context().wrap_socket(
        socket.socket(socket.AF_INET),
        server_hostname=domain,
    )
    sock.settimeout(5.0)
    sock.connect((domain, 443))
    cert = sock.getpeercert()

    # Parse
    date_regex = r'%b %d %H:%M:%S %Y %Z'
    expire_time = datetime.datetime.strptime(cert['notAfter'], date_regex)

    time_remaining = expire_time - datetime.datetime.utcnow()

    try:
        if time_remaining < datetime.timedelta(days=0):
            raise ExpiredCert()
        elif time_remaining < datetime.timedelta(days=days_to_warn):
            return {"domain": domain, "status": "ABOUT TO EXPIRE"}
        else:
            return {"domain": domain, "status": "OK"}
    except ExpiredCert:
        return {"domain": domain, "status": "EXPIRED"}
    except:
        import traceback
        return {"domain": domain, "status": "ERROR"}


class ExpiredCert(Exception):
    pass


def lambda_handler(event, context):

    results = []
    for domain in ssl_domains:
        result = check_cert_valid_expiration(domain, event.get('days_to_warn', 14))
        results.append(result)
        if result['status'] != 'OK' and event.get('topic', False):
            # Send email
            boto3.client('sns').publish(
                TopicArn=event['topic'],
                Message=json.dumps(result)
            )
    return results
