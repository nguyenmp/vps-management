import subprocess
import json
from datetime import datetime, timedelta
import re
from collections import defaultdict

def get_max_arg_length():
    output = subprocess.check_output(['sysctl', 'kern.argmax'])
    return int(output.decode('utf-8').split(': ')[1])

def list_files(bucket, prefix):
    print('Loading files')
    output = subprocess.check_output(['aws', 's3api', 'list-object-versions', '--bucket', bucket, '--prefix', prefix, '--output', 'json'])
    return json.loads(output.decode('utf-8'))

def delete_delete_marker(listing):
    if ('DeleteMarkers' not in listing) or len(listing['DeleteMarkers']) == 0:
        print('No delete markers to delete')
        return

    batch_delete(listing['DeleteMarkers'])


def batch_delete(items, batch_size=500):
    '''
    Batch by 500 because any more and the command will fail sometimes -shrug-
    '''
    payload = {
        "Objects": [],
        "Quiet": False,
    }
    num_processed = 0
    for index, item in enumerate(items):
        payload['Objects'].append(
            {
                "Key": item['Key'],
                "VersionId": item['VersionId'],
            }
        )

        if index % batch_size == 0 or index == len(items) - 1:
            print('Deleting batch with {} items and {} bytes'.format(len(payload['Objects']), len(json.dumps(payload))))
            with open('tmp.txt', 'w') as f:
                f.write(json.dumps(payload))
            subprocess.run(['aws', 's3api', 'delete-objects', '--bucket', 'aggressivelyparaphrasing.me.backups', '--delete', 'file://tmp.txt'], stdout=subprocess.DEVNULL)
            num_processed += len(payload['Objects'])
            print('Processed {} of {} items'.format(num_processed, len(items)))
            payload = {
                "Objects": [],
                "Quiet": False,
            }

def bin_backups_by_date(file_list):
    '''
    Given a list of files, bin them by date
    '''
    bins = {} # Map of date to list of keys
    for item in file_list['Versions']:
        key = item['Key']
        'aggressivelyparaphrasingme_backups/backup_2024-07-01-0445_Aggressively_Paraphrasing_Me_f4ed50d01137-uploads40.zip'
        match = re.search(r'backup_(\d{4}-\d{2}-\d{2}-\d{4})_', key)
        if not match:
            print('Could not match date in key: {}'.format(key))
            continue
        date_string = match.group(1)
        date_format = "%Y-%m-%d-%H%M"
        date_object = datetime.strptime(date_string, date_format)
        date = date_object.strftime("%Y-%m-%d")
        if date not in bins:
            bins[date] = []
        bins[date].append(key)

    for date, keys in bins.items():
        print('Date: {} has {} keys: {}'.format(date, len(keys), keys))
    return bins

def main():
    file_list = list_files(bucket='aggressivelyparaphrasing.me.backups', prefix='aggressivelyparaphrasingme_backups/')
    delete_delete_marker(file_list)
    backups_by_date = bin_backups_by_date(file_list)
    file_by_key = {
        item['Key']: item
        for item in file_list['Versions']
    }

    # Keep daily if it's within the last 30 days
    # Keep weekly for the last year
    # Keep monthly beyond that
    daily_backups = defaultdict(list) # year_month_day -> [dates]
    weekly_backups = defaultdict(list) # year_week -> [dates]
    monthly_backups = defaultdict(list) # year_mo -> [dates]
    today = datetime.now()
    thirty_days_ago = today - timedelta(days=30)
    one_year_ago = today - timedelta(days=365)
    for date, keys in backups_by_date.items():
        date_object = datetime.strptime(date, "%Y-%m-%d")
        if date_object < one_year_ago:
            print('Group monthly for items > 1 year old {}'.format(date))
            monthly_backups[date_object.strftime("%Y-%m")].append(date)
        elif date_object < thirty_days_ago:
            print('Group weekly for items > 30 days old {}'.format(date))
            weekly_backups[date_object.strftime("%Y-%W")].append(date)
        else:
            print('Keep daily for items < 30 days old {}'.format(date))
            daily_backups[date_object.strftime("%Y-%m-%d")].append(date)

    # Pick the first of each date group to keep
    to_keep = set()

    # Delete any that weren't picked
    to_delete = set()

    for week, dates in weekly_backups.items():
        to_keep.add(sorted(dates)[0])
    for month, dates in monthly_backups.items():
        to_keep.add(sorted(dates)[0])
    for day, dates in daily_backups.items():
        to_keep.add(sorted(dates)[0])

    for date, keys in backups_by_date.items():
        if date not in to_keep:
            to_delete.add(date)

    print('Deleting {} dates'.format(len(to_delete)))
    print('Keeping {} dates'.format(len(to_keep)))

    to_delete_files = []
    for date in to_delete:
        keys = backups_by_date[date]
        files = map(lambda key: file_by_key[key], keys)
        to_delete_files.extend(files)

    import pdb; pdb.set_trace()
    
    print('Deleting {} keys'.format(len(to_delete_files)))
    batch_delete(to_delete_files)

if __name__ == '__main__':
    main()
