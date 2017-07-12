import boto3
import datetime
import os
import re
import argparse


# Set arguments
parser = argparse.ArgumentParser()
parser.add_argument('--bucket', nargs='?', const='default', default='default', type=str)
args = parser.parse_args()


s3 = boto3.client(service_name='s3',region_name='us-gov-west-1')

files = s3.list_objects(Bucket='gtas-sf133-frb')['Contents']

todays_files = [x for x in files if (datetime.datetime.utcnow() - x['LastModified'].replace(tzinfo=None) < datetime.timedelta(hours=24))]
todays_files.sort(key=lambda tup: tup['LastModified'],reverse=True)

try:
    todays_cars = [x for x in todays_files if re.search('CARS', x['Key'])][0]
    no_cars = False
    os.makedirs('files', exist_ok=True)
    s3.download_file('gtas-sf133-frb',todays_cars['Key'],os.path.join(os.getcwd(),'files','cars_tas.csv'))
except:
    print('No CARS file posted in the last 24 hours')
    no_cars = True
    pass

try:
    todays_gtas = [x for x in todays_files if re.search('GTAS', x['Key'])][0]
    no_gtas = False
    gtas_year = todays_gtas['Key'].split('GTAS')[1][4:8]
    gtas_period = todays_gtas['Key'].split('GTAS')[1][8:10]
    gtas_filename = '_'.join(('sf','133',gtas_year,gtas_period))+'.csv'
    os.makedirs('files', exist_ok=True)
    s3.download_file(args.bucket,todays_gtas['Key'],os.path.join(os.getcwd(),'files',gtas_filename))
except:
    print('No GTAS file posted in the last 24 hours')
    no_gtas = True
    pass

if no_cars and no_gtas:
    print('No files to test/copy. Job failed.')
    exit(1)