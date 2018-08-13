import boto3
import argparse
import time

# Usage - python invalidate.py --url 'www.example.com'

# REQUIRED - AWS Profile/Key 
PROFILE_VAR = 'cf-invalidation'

parser = argparse.ArgumentParser()
parser.add_argument('--url', required=True, type=str)
args = parser.parse_args()
url = args.url

session = boto3.Session(profile_name=PROFILE_VAR)
client = session.client('cloudfront')

# Get distribution ID
response = client.list_distributions()
distributions = response['DistributionList']['Items']
for distribution in distributions:
    if int(distribution['Aliases']['Quantity'] > 0) and url in distribution['Aliases']['Items']:
        dist_id = distribution['Id']
        break

timestart = time.time()
invalidation = client.create_invalidation(DistributionId=dist_id, 
    InvalidationBatch={'Paths': {'Quantity': 1,'Items': ['/*',]},
    'CallerReference': str(timestart)})
invalidation_id = invalidation['Invalidation']['Id']
print('Creating invalidation for %s (id: %s)...' % (url, invalidation_id))

status = client.get_invalidation(DistributionId=dist_id,Id=invalidation_id)['Invalidation']['Status']

while (status != 'Completed'):
    print('Invalidating...%d sec elapsed' % (time.time()-timestart))
    time.sleep(10)
    status = client.get_invalidation(DistributionId=dist_id,Id=invalidation_id)['Invalidation']['Status']

print('Completed.')
