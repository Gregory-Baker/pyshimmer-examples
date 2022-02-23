import time

from serial import Serial

from pyshimmer import ShimmerBluetooth, DEFAULT_BAUDRATE, DataPacket, EChannelType


def handler(pkt: DataPacket) -> None:
    ppg_value = pkt[EChannelType.INTERNAL_ADC_13]
    print(f'Received new PPG value: {ppg_value}')

    gsr_raw = pkt[EChannelType.GSR_RAW]

    # get current GSR range resistor value
    Range = ((gsr_raw >> 14) & 0xff)  # upper two bits
    if(Range == 0):
        Rf = 40.2   # kohm
    elif(Range == 1):
        Rf = 287.0  # kohm
    elif(Range == 2):
        Rf = 1000.0 # kohm
    elif(Range == 3):
        Rf = 3300.0 # kohm

    gsr_to_volts = (gsr_raw & 0x3fff) * (3.0/4095.0)
    gsr_ohm = Rf/( (gsr_to_volts /0.5) - 1.0)
    gsr_mS = 1000/gsr_ohm

    print(f'Received new GSR value: {gsr_mS:.3f}')



if __name__ == '__main__':
    serial = Serial('/dev/rfcomm1', DEFAULT_BAUDRATE)
    shim_dev = ShimmerBluetooth(serial)

    shim_dev.initialize()

    dev_name = shim_dev.get_device_name()
    print(f'My name is: {dev_name}')

    shim_dev.add_stream_callback(handler)

    shim_dev.start_streaming()
    time.sleep(50.0)
    shim_dev.stop_streaming()

    shim_dev.shutdown()