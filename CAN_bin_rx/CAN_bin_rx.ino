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


static uint8_t shaving_bin1;
static uint8_t shaving_bin2;
static uint8_t shaving_count;


void shave_reset()
{
  shaving_bin1 = 0;
  shaving_bin2 = 0;
  shaving_count = 0;
}


// Feed the data/id bytes in here
void shave_bit_and_send(uint8_t& value)
{
  if (shaving_count < 7)
  {
    shaving_bin1 |= (value & (1 << 7)) ? (1 << shaving_count) : 0;
  }
  else
  {
    shaving_bin2 |= (value & (1 << 7)) ? (1 << (shaving_count - 7)) : 0;
  }

  Serial.write(value & ~(1 << 7));
  shaving_count++;
}

uint8_t get_id_length(long& id_value)
{
  uint8_t *byteArray = (uint8_t *)&id_value;
  if (byteArray[3])
  {
      return 4;
  }
  if (byteArray[2])
  {
      return 3;
  }
  if (byteArray[1])
  {
      return 2;
  }
  return 1;
}


void print_warning()
{
  Serial.println("error");
}


void loop() 
{
  uint8_t framing;
  uint8_t data_size;
  uint8_t id_size;
  long data_id;
  uint8_t data_byte;
  bool extended;

  shave_reset();

  // try to parse packet
  int packetSize = CAN.parsePacket();

  if (packetSize) 
  {
    data_id = CAN.packetId();

    if (CAN.packetRtr()) 
    {

    } 
    else 
    {
      // Deal with sending the data bytes
      while (CAN.available()) 
      {
        data_byte = (uint8_t)CAN.read();
        shave_bit_and_send(data_byte);
      }
    }

    extended = CAN.packetExtended();

    data_size = shaving_count;


    uint8_t *idArray = (uint8_t *)&data_id;

    if (extended)
    {
      shave_bit_and_send(idArray[0]);
      shave_bit_and_send(idArray[1]);
      shave_bit_and_send(idArray[2]);
      shave_bit_and_send(idArray[3]);
      id_size = 3;
    }
    else
    {
      shave_bit_and_send(idArray[0]);
      shave_bit_and_send(idArray[1]);
      id_size = 1;
    }

    Serial.write(shaving_bin1);
    Serial.write(shaving_bin2);

    // MS bit (BIT7) set indicates framing byte.  Receiver waits for this to arrive before attempting to decode the prior buffer values.
    // The framing byte contains the length information.  It verifies that a complete frame has been received.  If not it will be discarded
    // and the receiver will wait for a complete frame.
    framing |= (1 << 7);
    // BIT6 indicates whether an extended ID is being sent 1=yes, 0=no.
    framing |= extended ? (1 << 6) : 0;
    // Regardless of extended or not, a 2-bit field indicates the size of the ID.  This is the length of the ID minus 1.
    // You can have zero-length data, but you cannot have zero-length ID I believe.
    framing |= (id_size << 4);
    framing |= (data_size & 0xf);

    Serial.write(framing);
  }
}

