#!/usr/bin/python
import sys, struct, serial
import argparse

def wait_for_ack():
   ddata = ""
   ack = struct.pack('B', 0xff)
   while ddata != ack:
      ddata = ser.read(1)
      print "0x%02x" % ord(ddata[0])
	  
   return

def main(shimmer_port, output_file):
   global ser
   ser = serial.Serial(shimmer_port, 115200)
   ser.flushInput()
   print "port opening, done."

# send the set sensors command
   ser.write(struct.pack('BBBB', 0x08 , 0x04, 0x01, 0x00))  #GSR and PPG
   wait_for_ack()   
   print "sensor setting, done."

# Enable the internal expansion board power
   ser.write(struct.pack('BB', 0x5E, 0x01))
   wait_for_ack()
   print "enable internal expansion board power, done."

# send the set sampling rate command

   '''
    sampling_freq = 32768 / clock_wait = X Hz
   '''
   sampling_freq = 200
   clock_wait = (2 << 14) / sampling_freq

   ser.write(struct.pack('<BH', 0x05, clock_wait))
   wait_for_ack()

# send start streaming command
   ser.write(struct.pack('B', 0x07))
   wait_for_ack()
   print "start command sending, done."

# read incoming data
   ddata = ""
   numbytes = 0
   framesize = 8 # 1byte packet type + 3byte timestamp + 2 byte GSR + 2 byte PPG(Int A13)

   timestamp_start = None

   print "Packet Type\tTimestamp\tGSR\tPPG"
   try:
      while True:
         while numbytes < framesize:
            ddata += ser.read(framesize)
            numbytes = len(ddata)
         
         data = ddata[0:framesize]
         ddata = ddata[framesize:]
         numbytes = len(ddata)

         # read basic packet information
         (packettype) = struct.unpack('B', data[0:1])
         (timestamp0, timestamp1, timestamp2) = struct.unpack('BBB', data[1:4])

         # read packet payload
         (PPG_raw, GSR_raw) = struct.unpack('HH', data[4:framesize])

         # get current GSR range resistor value
         Range = ((GSR_raw >> 14) & 0xff)  # upper two bits
         if(Range == 0):
            Rf = 40.2   # kohm
         elif(Range == 1):
            Rf = 287.0  # kohm
         elif(Range == 2):
            Rf = 1000.0 # kohm
         elif(Range == 3):
            Rf = 3300.0 # kohm

         # convert GSR to kohm value
         gsr_to_volts = (GSR_raw & 0x3fff) * (3.0/4095.0)
         GSR_ohm = Rf/( (gsr_to_volts /0.5) - 1.0)
         GSR_muS = 1000000/GSR_ohm

         # convert PPG to milliVolt value
         PPG_mv = PPG_raw * (3000.0/4095.0)

         timestamp = timestamp0 + timestamp1*256 + timestamp2*65536

         if (timestamp_start is None):
            timestamp_start = timestamp

         timestamp_session = timestamp - timestamp_start

         if(output_file is None):
            print "0x%02x\t\t%5d,\t%4f,\t%4d" % (packettype[0], timestamp_session, GSR_muS, PPG_mv)
         else:
            with open(output_file, 'a') as writer:
               writer.write(str(timestamp_session))
               writer.write(',')
               writer.write(str(GSR_muS))
               writer.write(',')
               writer.write(str(PPG_mv))
               writer.write('\n')


   except KeyboardInterrupt:
#send stop streaming command
      ser.write(struct.pack('B', 0x20))
      print
      print "stop command sent, waiting for ACK_COMMAND"
      wait_for_ack()
      print "ACK_COMMAND received."
#close serial port
      ser.close()
      print "All done"


if __name__ == "__main__":
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
      default=None
   )

   # Parse the args (argparse automatically grabs the values from
   # sys.argv)
   args = parser.parse_args()

   shimmer_port = args.shimmer_port
   output_file = args.output_file
   main(shimmer_port, output_file)
   


