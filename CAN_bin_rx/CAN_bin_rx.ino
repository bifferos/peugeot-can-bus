// Copyright (c) Sandeep Mistry. All rights reserved.
// Licensed under the MIT license. See LICENSE file in the project root for full license information.

// This is just a hack of the standard example from Sandeep for investigative purposes.  I've changed the frequency 
// to 125kbits which seems to match what I measured on the scope for the peugeot.  Pulses were a little under 10uS, which would equate to 
// slightly faster than 100Kbps.  125kbps.  You do need to view the hex, because all codes are binary.

#include <CAN.h>

void setup() {
  Serial.begin(9600);
  while (!Serial);

  // start the CAN bus at 125 kbps
  if (!CAN.begin(125E3)) {
    Serial.println("Starting CAN failed!");
    while (1);
  }
}

void loop() {
  // try to parse packet
  int packetSize = CAN.parsePacket();

  if (packetSize) {
    Serial.print(CAN.packetId(), HEX);
    Serial.print(" ");

    if (CAN.packetRtr()) {
    } else {
      Serial.print(packetSize);

      // only print packet data for non-RTR packets
      while (CAN.available()) {
        Serial.print(" ");
        Serial.print((uint8_t)CAN.read(), HEX);
      }
    }

    Serial.println();
  }
}

