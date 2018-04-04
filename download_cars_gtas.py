import boto3
import datetime
import os
import re
import argparse
import pandas as pd

# if the contents of the row aren't empty and "null" is in it, delete the contents of the row
def replace_null(row, column_name):
    if row[column_name] and 'null' in row[column_name]:
        return None
    return row[column_name]


def main():
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
    except Exception as e:
        print('No CARS file posted in the last 24 hours')
        no_cars = True
        pass

    if not no_cars:
        current_dir = os.getcwd()
        cars_file_name = os.path.join(current_dir, 'files', 'cars_tas.csv')
        os.makedirs('files', exist_ok=True)
        print('Downloading ' + todays_cars['Key'] + ' as cars_tas.csv')
        s3.download_file('gtas-sf133-frb', todays_cars['Key'], cars_file_name)
        print('Download successful, beginning file cleanup.')

        # read CGAC values from csv
        data = pd.read_csv(cars_file_name, dtype=str, keep_default_na=False)

        data['End Date'] = data.apply(lambda x: replace_null(x, 'End Date'), axis=1)
        data['Financial Indicator Type 2'] = data.apply(lambda x: replace_null(x, 'Financial Indicator Type 2'), axis=1)
        data.rename(columns={'FR Entity Type Code': 'FR Entity Type',
                             'Financial Indicator Type 2': 'financial_indicator_type2',
                             'Date/Time Established': 'DT_TM_ESTAB',
                             'End Date': 'DT_END'},
                    inplace=True)
        data.to_csv(cars_file_name)

    try:
        todays_gtas = [x for x in todays_files if re.search('GTAS', x['Key'])][0]
        no_gtas = False
    except:
        print('No GTAS file posted in the last 24 hours')
        no_gtas = True
        pass

    if not no_gtas:
        gtas_year = todays_gtas['Key'].split('GTAS')[1][4:8]
        gtas_period = todays_gtas['Key'].split('GTAS')[1][8:10]
        gtas_filename = '_'.join(('sf','133',gtas_year,gtas_period))+'.csv'
        os.makedirs('files', exist_ok=True)
        print('Downloading '+todays_gtas['Key']+' as '+gtas_filename)
        s3.download_file(args.bucket,todays_gtas['Key'],os.path.join(os.getcwd(),'files',gtas_filename))
        print('Download successful')

    if no_cars and no_gtas:
        print('No files to test/copy for today ({}).'.format(datetime.datetime.now().strftime("%y-%m-%d")))

if __name__ == '__main__':
    main()