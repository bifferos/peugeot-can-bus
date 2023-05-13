//
// CAN bus sender.
// This sketch tries to keep up with the message rate from a 125Kbps CAN bus, while shifting the data onto a 115200 baud uart.
// All data is transferred with bit7 set low, while the framing bit has bit7 set high.
// Bit 7 on every sent data byte is 'shaved' off and transferred to two 'bin' bytes'
// The final byte in each frame is the 'framing' byte, it's the only byte that has bit7 set.

#include <CAN.h>


void setup() {
  Serial.begin(115200);
  while (!Serial);

  // start the CAN bus at 125 kbps
  if (!CAN.begin(125E3)) {
    Serial.println("Starting CAN failed!");
    while (1);
  }
}


// Total packet count
static uint8_t sending_count;
static uint8_t extended_count;


// Send the ID in 7-bit packets, ensuring the upper bit is always unset
// For the largest extended packet this will be 29 bits.  Don't send a 
// byte consisting of just one bit, we'll stuff that elsewhere.
// This will mean non-extended IDs take up 2 bytes max
void send_id(long ident, bool extended)
{
  // First byte is always sent.
  uint8_t extended_indicator = extended ? (1 << 6) : 0;
  Serial.write((uint8_t)((ident & 0x3f) | extended_indicator));
  sending_count++;
  ident >>= 6;

  // 2nd byte is always sent
  Serial.write((uint8_t)(ident & 0x7f));
  sending_count++;
  ident >>= 7;

  // Worst case is three more bytes for the rest of the extended bits.
  // Total bits: 29.   6 + 7 = 13 bits already sent, 16 remaining
  while (ident)
  {
    Serial.write((uint8_t)(ident & 0x7f));
    sending_count++;
    extended_count++;
    ident >>= 7;
  }
}


uint8_t send_data(uint8_t value)
{
  uint8_t carry = value & (1 << 7);
  Serial.write(value & ~(1 << 7));
  sending_count++;
  return carry;
}


void print_warning()
{
  Serial.println("error");
}


void loop() 
{
  sending_count = 0;
  extended_count = 0;

  // try to parse packet
  int packetSize = CAN.parsePacket();
  long data_id = CAN.packetId();

  if (packetSize || data_id != -1) 
  {
    send_id(data_id, CAN.packetExtended());

    uint8_t carry_byte = 0;
    if (CAN.packetRtr()) 
    {

    } 
    else 
    {
      // Deal with sending the data bytes
      while (CAN.available()) 
      {
        carry_byte >>= 1;
        carry_byte |= send_data((uint8_t)CAN.read());
      }
    }

    carry_byte = send_data(carry_byte);
  
    // MS bit (BIT7) set indicates framing byte.  Receiver waits for this to arrive before attempting to decode the prior buffer values.
    // The framing byte contains the length information.  It verifies that a complete frame has been received.  If not it will be discarded
    // and the receiver will wait for a complete frame.
    uint8_t framing = (1 << 7);

    framing |= (carry_byte >> 1);

    framing |= (extended_count << 4);

    // BITS 3,2,1,0 Indicate the number of bytes preceding, for run packet detection.  This can never be more than 15.
    framing |= (sending_count & 0xf);

    Serial.write(framing);
  }
}

