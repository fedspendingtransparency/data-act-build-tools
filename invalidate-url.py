import boto3
import argparse
import time
import os

# Usage - python invalidate.py --url 'www.example.com'

parser = argparse.ArgumentParser()
parser.add_argument('--url', required=True, type=str)
parser.add_argument('--path', required=False, type=str, default='/*')
args = parser.parse_args()
url = args.url
path = args.path

# Requires AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables available
session = boto3.Session(region_name='us-east-1')

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
    InvalidationBatch={'Paths': {'Quantity': 1,'Items': [path,]},
    'CallerReference': str(timestart)})
invalidation_id = invalidation['Invalidation']['Id']
print('Creating invalidation for %s (id: %s)...' % (url, invalidation_id))

status = client.get_invalidation(DistributionId=dist_id,Id=invalidation_id)['Invalidation']['Status']

while (status != 'Completed'):
    print('Invalidating...%d sec elapsed' % (time.time()-timestart))
    time.sleep(10)
    status = client.get_invalidation(DistributionId=dist_id,Id=invalidation_id)['Invalidation']['Status']

print('Completed.')
