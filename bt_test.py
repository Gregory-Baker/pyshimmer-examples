import time
import argparse
import atexit

from serial import Serial

from pyshimmer import ShimmerBluetooth, DEFAULT_BAUDRATE, DataPacket, EChannelType


def handler(pkt: DataPacket) -> None:
    ppg_raw = pkt[EChannelType.INTERNAL_ADC_13]
    #
    ppg_mv = ppg_raw * (3000.0/4095.0)

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
    gsr_kohm = Rf/( (gsr_to_volts /0.5) - 1.0)
    gsr_muS = 1000/gsr_kohm


    try: 
        with open(output_file, 'a') as writer:
            #writer.write(str(timestamp_session))
            #writer.write(',')
            writer.write(str(gsr_muS))
            writer.write(',')
            writer.write(str(ppg_mv))
            writer.write('\n')
            print(f'PPG value: {ppg_mv}')
            print(f'GSR value: {gsr_muS:.3f}')
    except:
        print('Write to file failed')
        print(f'PPG value: {ppg_mv}')
        print(f'GSR value: {gsr_muS:.3f}')

def exit_handler():
    print('My application is ending!')



if __name__ == '__main__':
        # Create our Argument parser and set its description
    parser = argparse.ArgumentParser(
        description="Extract GSR and PPG data from Shimmer and Log it",
    )

    parser.add_argument(
        'shimmer_port',
        type=str,
        help='The bluetooth port of the Shimmer, e.g. /dev/rfcomm1'
    )

    parser.add_argument(
        'output_file',
        help='Location of dest file (default: source_file appended with `_unix`',
    )

    # Parse the args (argparse automatically grabs the values from
    # sys.argv)
    args = parser.parse_args()

    shimmer_port = args.shimmer_port

    global output_file
    output_file = args.output_file

    serial = Serial('/dev/rfcomm1', DEFAULT_BAUDRATE)
    shim_dev = ShimmerBluetooth(serial)

    shim_dev.initialize()

    dev_name = shim_dev.get_device_name()
    print(f'My name is: {dev_name}')

    shim_dev.add_stream_callback(handler)

    shim_dev.start_streaming()
    time.sleep(20.0)
    shim_dev.stop_streaming()

    shim_dev.shutdown()