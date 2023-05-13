// Fast packet sender.  This is designed to saturate the bus to test if the receiver can keep up, sending a range of packet types
// in predictable sequence.

#include <CAN.h>

static uint16_t packetId = 0;
static uint8_t packetData = 0;
static uint8_t dataLength = 0;


void setup() 
{
  Serial.begin(115200);
  while (!Serial);

  Serial.println("CAN Sender");

  // start the CAN bus at 500 kbps
  if (!CAN.begin(125E3)) {
    Serial.println("Starting CAN failed!");
    while (1);
  }
}


void send_packet(uint16_t packetId, uint8_t data_size)
{
  CAN.beginPacket(packetId);
  for (uint8_t i=0; i<data_size; i++)
  {
    CAN.write(0xAA);
  }
  CAN.endPacket();
}


void send_ex_packet(long packetId)
{
  CAN.beginExtendedPacket(packetId);
  CAN.write(0xAA);
  CAN.endPacket();
}


void loop() 
{
  for (packetId = 0; packetId <= 0x7ff; packetId++)
  {
    send_packet(packetId, dataLength);
    dataLength++;
    if (dataLength>8)
    {
      dataLength = 0;
    }
  }

  // Extended packet, just below the max ID.
  send_ex_packet(536870910);
}

