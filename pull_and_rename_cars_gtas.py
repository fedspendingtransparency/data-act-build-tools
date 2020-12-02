import boto3
import datetime
import os
import re
import argparse
import pandas as pd

'''
Pulls and renames both the most recent CARS file and the most recent GTAS aka SF133 file.
By default, does nothing if there was no S3 files found in the past 24 hours, 
can be forced to pull the most recent.

File naming convention is s3://dti-gtas-sf133-frb-{account}/PE.[CARS or GTAS]_DA-YYYYMM-PP 
where PP = period and MM = fiscal month
'''


# Helper function...if the contents of the row aren't empty and "null" is in it, delete the contents of the row
def replace_null(row, column_name):
    if row[column_name] and 'null' in row[column_name]:
        return None
    return row[column_name]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--force_pull_latest', action='store_true', help='Pulls the most recent CARS ' + 
        'and the most recent GTAS (aka SF133) file, regardless of when it came in.')
    parser.add_argument('--bucket', nargs='?', const='default', default='default', type=str)
    args = parser.parse_args()

    print('\nPulling latest from bucket "{}".'.format(args.bucket))

    if not args.force_pull_latest:
        print('Ignoring files modified before {}'.format(
            (datetime.datetime.now() - datetime.timedelta(hours=24)).strftime("%Y-%m-%d %H:%m:%S"))
        )

    s3 = boto3.resource(service_name='s3', region_name='us-gov-west-1')
    bucket_source = s3.Bucket(args.bucket)

    all_files = bucket_source.objects.all()

    if args.force_pull_latest:
        recent_files = list(all_files)
    else:
        recent_files = [x for x in all_files if (
            datetime.datetime.utcnow() - x.last_modified.replace(tzinfo=None) <
            datetime.timedelta(hours=24))]

    recent_files.sort(key=lambda tup: tup.last_modified, reverse=True)

    try:
        recent_cars = [x for x in recent_files if re.search('PE\.CARS', x.key)][0]
        cars_exists = True
    except Exception as e:
        print('No CARS file posted in the last 24 hours, or no files found.')
        cars_exists = False
        pass

    if cars_exists:
        current_dir = os.getcwd()
        cars_file_name = os.path.join(current_dir, 'files', 'cars_tas.csv')
        os.makedirs('files', exist_ok=True)
        print('Downloading ' + recent_cars.key + ' as cars_tas.csv')
        bucket_source.download_file(recent_cars.key, cars_file_name)
        print('Download successful, beginning file cleanup.')

        # read CGAC values from csv
        data = pd.read_csv(cars_file_name, dtype=str, keep_default_na=False)

        data['End Date'] = data.apply(lambda x: replace_null(x, 'End Date'), axis=1)
        data['Financial Indicator Type 2'] = data.apply(
            lambda x: replace_null(x, 'Financial Indicator Type 2'), 
            axis=1
        )

        data.rename(columns={'FR Entity Type Code': 'FR Entity Type',
                             'Financial Indicator Type 2': 'financial_indicator_type2',
                             'Date/Time Established': 'DT_TM_ESTAB',
                             'End Date': 'DT_END'},
                             inplace=True)
        data.to_csv(cars_file_name)

    try:
        recent_gtas = [x for x in recent_files if re.search('PE\.GTAS', x.key)][0]
        gtas_exists = True
    except:
        print('No GTAS file posted in the last 24 hours, or no files found.')
        gtas_exists = False
        pass

    if gtas_exists:
        gtas_year = recent_gtas.key.split('GTAS')[1][4:8]
        gtas_period = recent_gtas.key.split('GTAS')[1][8:10]
        gtas_filename = '_'.join(('sf', '133', gtas_year,gtas_period)) + '.csv'
        os.makedirs('files', exist_ok=True)
        print('Downloading ' + recent_gtas.key + ' as ' + gtas_filename)
        bucket_source.download_file(recent_gtas.key, os.path.join(os.getcwd(), 'files', gtas_filename))
        print('Download successful')

    if not cars_exists and not gtas_exists:
        print('No files in "{}" modified since {}, or no files found.'.format(
            args.bucket,
            (datetime.datetime.now() - datetime.timedelta(hours=24)).strftime("%Y-%m-%d %H:%m:%S"))
        )

if __name__ == '__main__':
    main()
