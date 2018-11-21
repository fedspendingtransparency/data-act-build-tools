import boto3
import argparse
import time
import os


# Set arguments
parser = argparse.ArgumentParser()
parser.add_argument('--env', nargs='?', const='staging', default='staging', type=str)
args = parser.parse_args()

# Requires a cf-invalidation profile with the right access to our distros
session = boto3.Session(profile_name='cf-invalidation')

client = session.client('cloudfront')

# Get distribution Id
response = client.list_distributions()
distributions = response['DistributionList']['Items']
dist_id = [x for x in distributions if x['Comment'] == ('broker - ' + args.env)][0]['Id']

# Create invalidation
timestart = time.time()
inval = client.create_invalidation(DistributionId=dist_id, InvalidationBatch={'Paths': {'Quantity': 1,'Items': ['/*',]},'CallerReference': str(timestart)})
status = client.get_invalidation(DistributionId=dist_id,Id=inval['Invalidation']['Id'])['Invalidation']['Status']
print('Invalidating... ')

# Check status until invalidation is complete.
while (status != 'Completed'):
	print('Still invalidating... ' + "{:.2f}".format(time.time()-timestart) + ' sec elapsed' )
	time.sleep(10)
	status = client.get_invalidation(DistributionId=dist_id,Id=inval['Invalidation']['Id'])['Invalidation']['Status']

# Display completion
print('Invalidation ' + inval['Invalidation']['Id'] + ' on Distribution ' + dist_id + ' completed in ' + "{:.2f}".format(time.time()-timestart) + ' seconds.' )
