# peugeot-can-bus
Investigation of peugeot can-bus

At the rear of the Peugeot Partner, behind the left-hand boot panel just above and the rear of the wheel arch can be found a small 10-way 0.1 inch pitch 2x9 connector.
Viewing the female connector from the underside:

```
yel/green ---  10+-----+ 9  --- yel/green
Pink --------  11|     | 8  --- white
               12|     | 7
               13|     | 6
Red ---------  14|     | 5  --- yellow
               15|     | 4
               16|     | 3
               17|     | 2
               18+-----+ 1
```
   
The connector has numbered pins, but they don't correspond to normal IDC pin numbers.
With the key out of the ignition, the red cable on pin 14 carries approx 11.6 volts.
Once the key is in the ignition and turned (without starting) red switches to around 4.6v
It's at this point that the CAN-BUS signal gets activated.

CAN is carried on Red and Yellow cables.   The Red is normally high, the yellow is normally low when not transmitting.

Therefore Red is CANL
Yellow is CANH.

Having figured out the bus lines, An arduino UNO with older v1.1 shield was used to investigate the data packets.  Shield is wired such that 
default settings of Sandeep Mistry CAN-bus library work out-of-the-box.
https://github.com/sandeepmistry/arduino-CAN/tree/master/examples

Examples work great to join two shields together and allow communication.

BUT There's a problem.  To setup CAN-bus monitoring, it's necessary to get all CAN packets to the PC.  CAN-bus signalling for my car is 
at 125kbps.  Maximum speed of Arduino UNO serial port is realistically 115200.
Using a line-based serial protocol with hex printed values is nice and easy to decode on the PC side (just seek to newline and decode),
however it's not fast enough to keep up with the data rate.   115,200 is pretty close to 125kbps.  With protocol overhead it should be
possible to keep up on the PC side IF a more efficient protocol is used.

First tried base64 encoding.  It didn't work.  Could have been the speed of the encoding or the transmission efficiency.

Decided to invent my own encoding, trying to use knowledge of the CAN-bus protocol.


Information that needs to be transmitted to the PC:

ID of packet.  This can be 11 bits for standard CAN.  29 bits for extended.
Data of packet.  This cab be zero to eight bytes.

By observation all packets on my vehicle bus appear to be standard.  Whatever protocol I use should optimise standard ID transmission.
Extended doesn't matter so much.
By observation 95% of packets have bits higher than 0xff set.  Therefore no point in optimising sending of id as single byte.
Very few messages have zero bytes sent.  Probably not worth optimising this case.
Many packets set all 8 bytes.


Next question, Synchronisation:

Need to understand where a packet starts and ends.  It's OK if you only know where it ends, and the ending byte has some kind of checksum.
Then you just discard the packets with failing checksums until you get sync.
If you control the data acquisition with a 'START''STOP' command, then you don't need sync because you are ready for the first byte when it 
comes.  Unless the data gets corrupted you're fine.  However this greatly complicates the Arduino side of the software.

BUT... we have very short packets.  Average packet size (for the raw data) is around 11 bits + 6-8 data bytes.  That's about 10 bytes.
What if we simply dedicate one bit (let's say BIT7) to sync, and never use it in the data stream?  7-bits data has some complexity.  You 
have to either wrap transmitted bitstream into 7-bit chunks.  Or you need to take off the top bits and transmit them separately.
BUT... we have 11-bits ID the majority case.  So 11 bits can go in two 7-bit values.  Two bytes to xmit over serial and then we are done.
There's even 'spare' bits (14 - 11 = 3) for any extra info.  So why not use the first of those bits to indicate if the ID is extended, 
and save even more space.

NOW... we come onto the data bytes.  Maximum 8 of them.  We could have some complicated encoding mechanism with bit rotation, but since
max count is 8 why bother?  Simply take off the MS bit for each, and send them to the UART.  Then send another byte which is all the 
bit7s from the 8 preceding bytes in one go.   But for 8-bytes, that byte in turn has too many bits for our 7-bit channel.  So take that 
one off, and add it to the end-of-frame byte.

In order to understand if we started rx mid-frame, the end-of-frame marker must have some information.  At a minimum the number of bytes of 
preceding data.  Since that number of bytes will never be greater than 15 it can be encoded in 4 bits.  So for the end-of-frame marker we
have:

BIT7: Sync bit, if set high this is EOF.
BIT6: MSB for the byte carrying all the 'bit7s' of the data bytes.
BIT3-0: Total count of preceding bytes so we know if we have complete frame.

BUT... what about extended IDs.  These can be 29 bits.  I don't really have any knowledge of how they are typically used, so I'm not going to
optimise at all.  The bottom 13 bits get sent in the lower 7 bits of the first two transmitted bytes.  Bit6 of the first byte xmitted is
the extended ID indicator.  Remaining bits get rolled into 7-bit chunks in successive 'id' bytes.  So the max bytes to transmit the ID is 5.
However we need to know where the ID stops and the data starts.  So this is done by an 'extra ID bytes' count.  Set to zero for standard
IDs, where the ID is in two bytes, but can be max of 3.

So the marker makeup is:
BIT7: Sync bit, if set high this is EOF.
BIT6: MSB for the byte carrying all the 'bit7s' of the data bytes.
BIT5-4: Count of 'extra' id bytes.   
BIT3-0: Total count of preceding bytes so we know if we have complete frame.

