import datetime as dt
import urllib.request as req
import time
from configparser import ConfigParser, NoOptionError, NoSectionError
import warnings
import traceback
import os, sys
import persistence
import tracemalloc
import logging
import server

now = dt.datetime.now()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='app.log',
    filemode='a'
)

def read_settings(args):
    config = ConfigParser()
    fn_ini_file = 'config.ini'
    config.read(fn_ini_file)
    match args:
        case 'MIKROTIK_IP':
            try:
                MIKROTIK_IP  = config.get('Settings', 'MIKROTIK_IP')
            except (NoSectionError, NoOptionError):
                MIKROTIK_IP   = '192.168.100.8'
                warn_msg = 'Parameter \'Router_IP\' was not found under section \
                            \'Settings\'. The default ip of \'%s\' was used.' %MIKROTIK_IP
                warnings.warn(warn_msg)
            return MIKROTIK_IP
        case 'LOG_INTERVAL':
            try:
                LOG_INTERVAL  = config.getint('Settings', 'LOG_INTERVAL')
            except (NoSectionError, NoOptionError):
                LOG_INTERVAL  = 10
                warn_msg = 'Parameter \'LOG_INTERVAL\' was not provided \
                            under section \'Settings\'. The default log interval of %is was used.' %LOG_INTERVAL
                warnings.warn(warn_msg)
            return LOG_INTERVAL
        case 'AGGREGATE_INTERVAL':
            try:
                AGGREGATE_INTERVAL = config.getint('Settings', 'AGGREGATE_INTERVAL')
            except (NoSectionError, NoOptionError):
                AGGREGATE_INTERVAL = 1800
                warn_msg = 'Parameter \'AGGREGATE_INTERVAL\' was not provided \
                            under section \'Settings\'. The default log interval of %is was used.' %AGGREGATE_INTERVAL
                warnings.warn(warn_msg)
            return AGGREGATE_INTERVAL
        case 'DB_NAME':
            try:
                DB_NAME = config.get('Settings', 'DB_NAME')
            except (NoSectionError, NoOptionError):
                DB_NAME = 'mikrotik'
                warn_msg = 'Parameter \'DB_NAME\' was not provided \
                            under section \'Settings\'. The default db name of %s was used.' %DB_NAME
                warnings.warn(warn_msg)
            return DB_NAME
        case 'DB_USER':
            try:
                DB_USER = config.get('Settings', 'DB_USER')
            except (NoSectionError, NoOptionError):
                DB_USER = 'root'
                warn_msg = 'Parameter \'DB_USER\' was not provided \
                            under section \'Settings\'. The default db user of %s was used.' %DB_USER
                warnings.warn(warn_msg)
            return DB_USER
        case 'DB_PASSWORD':
            try:
                DB_PASSWORD = config.get('Settings', 'DB_PASSWORD')
            except (NoSectionError, NoOptionError):
                DB_PASSWORD = ''
                warn_msg = 'Parameter \'DB_PASSWORD\' was not provided \
                            under section \'Settings\'. The default db password of %s was used.' %DB_PASSWORD
                warnings.warn(warn_msg)
            return DB_PASSWORD
        case 'DB_HOST':
            try:
                DB_HOST = config.get('Settings', 'DB_HOST')
            except (NoSectionError, NoOptionError):
                DB_HOST = 'localhost'
                warn_msg = 'Parameter \'DB_HOST\' was not provided \
                            under section \'Settings\'. The default db host of %s was used.' %DB_HOST
                warnings.warn(warn_msg) 
            return DB_HOST
        case __annotations__:  # If no match is found
            raise ValueError(f'Invalid argument: {args}')
        
        


def roundTime(roundTo, now=None):
    """Round a datetime object to any time laps in seconds
    dt : datetime.datetime object, default now.
    roundTo : Closest number of seconds to round to, default 1 minute.
    Author: Thierry Husson 2012 - Use it as you want but don't blame me.
    """
    if now == None: now = dt.datetime.now()
    seconds = (now.replace(tzinfo=None) - now.min).seconds
    rounding = (seconds+roundTo/2) // roundTo * roundTo
    if now.second > roundTo/2.:
        return now + dt.timedelta(0,rounding-seconds,-now.microsecond) - dt.timedelta(seconds=roundTo)
    else:
        return now + dt.timedelta(0,rounding-seconds,-now.microsecond)

def roundTime_forward(interval=60, now_var=None):
    if now_var == None: now_var = dt.datetime.now().replace(microsecond=0)
    seconds = (now_var.replace(tzinfo=None) - now_var.min).seconds
    rounding = (seconds + interval) // interval * interval
    result = now_var + dt.timedelta(0, rounding-seconds, -now_var.microsecond)
    return result

def wait_to_next_interval(interval):
    """
    Waits for the next interval boundary.

    Args:
        interval: Interval in seconds.
    """
    time_now = dt.datetime.now()
    next_interval = roundTime_forward(interval, now_var=time_now)
    sec_from_last_interval = ((next_interval-time_now).total_seconds())
    logging.info(f'Waiting {sec_from_last_interval:.2f} seconds for the next interval')
    time.sleep(sec_from_last_interval)

def get_data(IP, starttime=time.time(), interval=60):
    data = []
    all_users = []
    total_up = 0.0
    total_dn = 0.0
    try:
        pulled = req.urlopen(req.Request('http://' + IP + '/accounting/ip.cgi')).read()
        pulled = pulled.decode('utf-8').rstrip().split('\n')
    except Exception as E:
        print(E)
        try:
            pulled = req.urlopen(req.Request('http://' + IP + '/accounting/ip.cgi')).read()
            pulled = pulled.decode('utf-8').rstrip().split('\n')
        except Exception as E:
            print(E)
            pulled = ['']
    
    for line in pulled:
        s = line.split(' ')
        if not s == ['']:
            username_up = s[4]
            username_down = s[5]
            user_list_with_id = persistence.read_user_lists()
            user_list = [user['username'] for user in user_list_with_id]
            if not username_up == '*':
                if username_up in user_list:
                    # print(f'{username_up} ada di list up')
                    user_id = persistence.get_user_id_from_username(username_up)
                else:
                    # print(f'{username_up} gak ada di list up')
                    persistence.add_new_user_to_lists(username_up)
                    user_id = persistence.get_user_id_from_username(username_up)
                all_users.append(user_id)
                data.append([(user_id), float(s[2]), 0.0])
            elif not username_down == '*':
                if username_down in user_list:
                    # print(f'{username_down} ada di list down')
                    user_id = persistence.get_user_id_from_username(username_down)
                else:
                    # print(f'{username_down} gak ada di list down')
                    persistence.add_new_user_to_lists(username_down)
                    user_id = persistence.get_user_id_from_username(username_down)
                all_users.append(user_id)
                data.append([(user_id), 0.0, float(s[2])])
            else:
                logging.info(f'username tidak terdeteksi: {s}')

    user_unique = list(set(all_users))
    aggregated = [[0.0] * 3 for _ in range(len(user_unique))] 
    for i_agg in range(len(user_unique)):
        aggregated[i_agg][0] = user_unique[i_agg]
        for i in range(len(data)):
            if data[i][0] == user_unique[i_agg]:
                aggregated[i_agg][1] += data[i][1]
                aggregated[i_agg][2] += data[i][2]
                total_up += data[i][1]
                total_dn += data[i][2]
        persistence.add_raw_data(aggregated[i_agg][0], aggregated[i_agg][1], aggregated[i_agg][2], dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    persistence.add_raw_data(1, total_up, total_dn, dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

def aggregate_data_30_min():
    try:
        user_list_with_id = persistence.read_user_lists()
        user_list = [user['username'] for user in user_list_with_id]
        for user in user_list:
            user_id = persistence.get_user_id_from_username(user)
            count = persistence.query_db('SELECT COUNT(*) as count FROM raw_bandwidth_logs WHERE user_id = %s', [(user_id)])[0]['count']
            if count == 0:
                continue
            result = persistence.query_db('SELECT SUM(tx_bytes) as total_tx_bytes, SUM(rx_bytes) as total_rx_bytes FROM raw_bandwidth_logs WHERE user_id = %s', [(user_id)])
            timestamps = persistence.query_db('SELECT timestamp FROM raw_bandwidth_logs WHERE user_id = %s', [(user_id)])

            timestamp_values = [entry['timestamp'] for entry in timestamps]
            earliest_time = min(timestamp_values)
            latest_time = max(timestamp_values)

            total_tx_bytes = result[0]['total_tx_bytes']
            total_rx_bytes = result[0]['total_rx_bytes']
            
            persistence.aggregate_data(user_id, earliest_time, latest_time, total_tx_bytes, total_rx_bytes)
            
    except Exception as E:
        print("error: ", E)
        print(traceback.format_exc())

if __name__ == '__main__':
    try:
        tracemalloc.start()
        IP_MIKROTIK = read_settings('MIKROTIK_IP')
        LOG_INTERVAL = read_settings('LOG_INTERVAL')
        AGGREGATE_INTERVAL = read_settings('AGGREGATE_INTERVAL')
        start_time = dt.datetime.now().replace(microsecond=0)
        aggregate_time = roundTime_forward(AGGREGATE_INTERVAL, now_var=start_time)
        server.start()

        while True:
            get_data(IP_MIKROTIK)
            logging.info(f'get_data_at: {dt.datetime.now().replace(microsecond=0)}')
            current_time = dt.datetime.now().replace(microsecond=0)

            if ( current_time >= aggregate_time):
                logging.info(f'next_aggregate_time: {aggregate_time}')
                logging.info( f'current_time: {current_time}')
                aggregate_data_30_min()
                aggregate_time = roundTime_forward(AGGREGATE_INTERVAL, now_var=current_time)
                logging.info(f'aggregate_data_at: {dt.datetime.now().replace(microsecond=0)}')
                
                current, peak = tracemalloc.get_traced_memory()
                logging.info(f"Current memory usage: {current / 1024 / 1024:.2f} MiB")
                logging.info(f"Peak memory usage: {peak / 1024 / 1024:.2f} MiB")

            wait_to_next_interval(LOG_INTERVAL)  # Align main function to minute boundary

    except KeyboardInterrupt as E:
        print(traceback.format_exc())
        os._exit(0)
        sys.exit()

            