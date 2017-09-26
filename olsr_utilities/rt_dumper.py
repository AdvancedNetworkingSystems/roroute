#!/usr/bin/env python

from pyroute2 import IPDB
import time
import argparse
from subprocess import check_output


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--starttime', dest='start_time', type=int,
                        help='Dumping start time')
    parser.add_argument('--stoptime', dest='stop_time', type=int,
                        help='Dumping stop time')
    parser.add_argument('--interval', dest='interval', type=int,
                        help='Interval in ms')
    parser.add_argument('--version', dest='version', type=int,
                        choices=[1, 2],
                        help='Interval in ms')
    parser.add_argument('--outid', dest='outid', type=str,
                        help='Output prefix')
    args = parser.parse_args()

    start_time = args.start_time
    stop_time = args.stop_time
    interval = float(args.interval) / 1000.0
    outid = args.outid
    version = args.version

    olsr_pname = ''
    if version == 1:
        olsr_pname = 'olsrd'
    elif version == 2:
        olsr_pname = 'olsrd2_dynamic'

    ipdb = IPDB()
    next_time = start_time

    idx = 0
    now = 0
    last_rt = None
    while True:
        now = time.time()
        wait_time = next_time - now
        if wait_time > 0:
            time.sleep(wait_time)
        else:
            next_time = now

        try:
            check_output(["pgrep", olsr_pname])
            rt_json_str = '{"routes":['
            for r in ipdb.routes:
                dst = r['dst']
                gw = r['gateway']
                if dst is None or gw is None:
                    continue
                if dst == 'default':
                    continue
                dst = dst.split('/')[0]
                rt_json_str += '{"destination":"' + dst +\
                    '","gateway":"' + gw + '"},'

            rt_json_str = rt_json_str.rstrip(',')
            rt_json_str += ']}'
        except:
            rt_json_str = ''

        if last_rt is None or rt_json_str != last_rt:
            now = time.time()
            epoch_s, epoch_ms = ('%.9f' % now).split('.')
            outfile_name = '%s_%06d_%09d_%09d.pyroute' %\
                (outid, idx, int(epoch_s), int(epoch_ms))
            with open(outfile_name, 'w') as df:
                df.write(rt_json_str)

        last_rt = rt_json_str
        idx += 1
        next_time += interval
        stop_diff = stop_time - next_time

        if stop_diff < 0:
            break
