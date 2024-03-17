from os.path import getsize
from time import sleep


def get_dbytes(file_path: str, delay: float) -> int:
    initial_bytes = getsize(file_path)
    sleep(delay)
    final_bytes = getsize(file_path) - initial_bytes
    return final_bytes


def get_bytes_per_second(file_path: str, delay: float) -> float:
    return float(get_dbytes(file_path, delay)) / delay


def monitor_bytes_per_second(file_path: str, output_file: str, delay: float,
                             duration: float, initial_time: float) -> None:
    time = initial_time
    dump = open(output_file, 'a')
    dump.write(f"{time:.2f}\t0.00\n")
    while not (time <= duration <= time + delay):
        speed = get_bytes_per_second(file_path, delay)
        time += delay
        dump.write(f"{time:.2f}\t{speed:.2f}\n")
        dump.flush()
    dump.close()
