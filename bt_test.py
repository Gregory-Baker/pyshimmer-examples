import time
import argparse
import atexit

from serial import Serial

from pyshimmer import ShimmerBluetooth, DEFAULT_BAUDRATE, DataPacket, EChannelType

def exit_handler():
    print('Stopping Shimmer logging!')
    print(f'Number of packets received: {num_packets}')
    shim_dev.stop_logging()
    shim_dev.shutdown()


def handler(pkt: DataPacket) -> None:
    ppg_raw = pkt[EChannelType.INTERNAL_ADC_13]
    #
    ppg_mv = ppg_raw * (3000.0/4095.0)

    gsr_raw = pkt[EChannelType.GSR_RAW]

    timestamp = pkt[EChannelType.TIMESTAMP]

    global num_packets, timestamp_start, osc_frequency

    if(num_packets == 0):
        timestamp_start = timestamp
    
    timestamp_session = timestamp - timestamp_start
    time_session = timestamp_session/osc_frequency


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

    if (num_packets%1000 == 0):
        print("1000 more packets received!")

    num_packets = num_packets + 1


    try: 
        with open(output_file, 'a') as writer:
            writer.write(str(time_session))
            writer.write(',')
            writer.write(str(gsr_muS))
            writer.write(',')
            writer.write(str(ppg_mv))
            writer.write('\n')
            #print(f'PPG value: {ppg_mv}')
            #print(f'GSR value: {gsr_muS:.3f}')
    except:
        print('Write to file failed')
        print(f'PPG value: {ppg_mv}')
        print(f'GSR value: {gsr_muS:.3f}')


if __name__ == '__main__':

    atexit.register(exit_handler)

        # Create our Argument parser and set its description
    parser = argparse.ArgumentParser(
        description="Extract GSR and PPG data from Shimmer and Log it",
    )

    # parser.add_argument(
    #     'shimmer_port',
    #     type=str,
    #     help='The bluetooth port of the Shimmer, e.g. /dev/rfcomm1'
    # )

    parser.add_argument(
        'output_file',
        help='Location of dest file (default: source_file appended with `_unix`',
    )

    # Parse the args (argparse automatically grabs the values from
    # sys.argv)
    args = parser.parse_args()

    # shimmer_port = args.shimmer_port

    global timestamp_start, num_packets, output_file, osc_frequency
    output_file = args.output_file

    num_packets = 0
    timestamp_start = 0
    osc_frequency = 32768

    serial = Serial('/dev/rfcomm1', DEFAULT_BAUDRATE)
    shim_dev = ShimmerBluetooth(serial)

    shim_dev.initialize()

    dev_name = shim_dev.get_device_name()
    print(f'My name is: {dev_name}')

    shim_dev.add_stream_callback(handler)

    shim_dev.start_streaming()

    try:
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        print('interrupted!')