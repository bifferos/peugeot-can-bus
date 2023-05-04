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

