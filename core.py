from time import sleep
from subprocess import check_output


def get_file_bits(path: str) -> int:
    raw = check_output(['du', '-b', path], encoding='utf8')
    return int(raw.split('\t')[0])

def record(monitor_path, dump_path, delay_seconds, lifetime):
    time = 0
    bits_i = get_file_bits(monitor_path)
    with open(dump_path, 'a') as dump:
        while True:
            bits_f = get_file_bits(monitor_path)
            bps = round((bits_f - bits_i) / delay_seconds, 2)
            bits_i = bits_f
            dump.write(str(round(time, 2)) + '\t' + str(bps) + '\n')
            dump.flush()
            time += delay_seconds
            sleep(delay_seconds)
            if (lifetime > 0 and lifetime - delay_seconds < 0):
                break
            lifetime -= delay_seconds
