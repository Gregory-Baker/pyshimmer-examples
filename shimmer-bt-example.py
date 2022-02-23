import time
import atexit

from serial import Serial

from pyshimmer import ShimmerBluetooth, DEFAULT_BAUDRATE, DataPacket, EChannelType

def exit_handler():
    print('Stopping Shimmer logging!')
    shim_dev.stop_logging()
    shim_dev.shutdown()


def handler(pkt: DataPacket) -> None:
    cur_value = pkt[EChannelType.INTERNAL_ADC_13]
    print(f'Received new data point: {cur_value}')


if __name__ == '__main__':
    atexit.register(exit_handler)

    serial = Serial('/dev/rfcomm1', DEFAULT_BAUDRATE)
    shim_dev = ShimmerBluetooth(serial)

    shim_dev.initialize()

    dev_name = shim_dev.get_device_name()
    print(f'My name is: {dev_name}')

    print('Starting Shimmer logging!')
    shim_dev.start_logging()

    try:
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        print('interrupted!')