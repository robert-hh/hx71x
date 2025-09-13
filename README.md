# HX71X: Python class for the HX710 and HX711 load cells

This is a very short and simple class. This lib includes three variants of the
module. One is using direct GPIO pin handling, the other uses the PIO
module of the RPI Pico. The third variant uses SPI.
Besides the class instantiation, all variants offer the same methods.
The preferred methods are GPIO and PIO, because they deal properly with the conversion
ready signal resulting in a more precise result.

## Classes

The support for the HX71X sensor is split in two classes, HX71X_IO and
HX71X. Class HX71X_IO provides the communication with the sensor and basic
methods. Class HX71X provides further methods supporting to use the HX71X
sensors e.g. for scales. If just the basic raw reading is needed, the HX71X_IO
class is sufficient.

### hx71x_io = HX71X_IO(clock_pin, data_pin, mode=1)

This is the GPIO constructor. `data_pin` and `clock_pin` are the pin objects
of the GPIO pins used for the communication. `clock_pin` must not be an input-only pin.
`mode` is the setting of the load cell amplifier.
The default value of 1 also selects the external sensor.

### hx71x_io = HX71X_IO(clock_pin, data_pin, mode=1, state_machine=0)

This is the Raspberry Pi PIO constructor. `data_pin` and `clock_pin` are the pin objects
of the GPIO pins used for the communication.
`mode` is the setting of the load cell amplifier.
The default value of 1 also selects the external sensor.
The argument `state_machine` can be set to different values if conflicting with
other uses, like if than one HX71X device is used by an application.

### hx71x_io = HX71X_IO(clock_pin, data_pin, spi, mode=1)

This is the SPI constructor. `data_pin` is the SPI MISO, `clock_pin` the SPI MOSI. These must be
Pin objects, with `data_pin` defined for input, `clock_pin` defined as output.
They must be supplied in addition to the spi object, even if spi uses
the same  pins for miso and mosi.
`spi` is the SPI object. The spi clock signal will not be be used.
`mode` is the of of the load cell amplifier.
The default value of 1 also selects the external sensor.

### hx71x = HX71X(hx71x_io_instance)

Create an instance of the utility class, which takes an instance of the HX71X
class as argument.

## Methods of the HX71X_IO class

### hx71x_io.set_mode(mode)

Sets the mode which is used for the next call of hx71x.read()

mode values of the HX710:

|Mode|Value|
|:-:|:-:|
|1|External Sensor at 10 Hz|
|2|Internal Temperature (HX710A)|
|2|DVDD - AVDD (HB710B)|
|3|External Sensor at 40 Hz|

mode values of the HX711:

|Mode|Gain and Channel|
|:-:|:-:|
|1|Gain = 128, Channel A|
|2|Gain = 32, Channel B|
|3|Gain = 64, Channel A|

### result = hx71x_io.read()
### result = hx71x_io()

Returns the actual raw value of the load cell. Raw means: not scaled, no offset
compensation.

### hx71x_io.power_down()

Set the load cell to sleep mode. power_down() and power_up() are only
working with the hx71x_gpio and hx71x_pio variants of the driver.

### hx71x_io.power_up()

Switch the load cell on again. After power up the device needs about
500ms to recover. Any attempt to read in the time will take longer
than usual to finish.


## Methods of the HX71X class

### result = hx71x.read()
### hx71x_set_mode(mode)
### hx71x.temperature([raw=False])
### hx71x.calibrate(ref_temp [, gain=20.4])
### hx71x.power_down()
### hx71x.power_up()

Aliases for the HX71X_IO class methods.

### result = hx71x.read_average(times=3)

Returns the raw value of the load cell as the average of `times` readings of The
raw value.

### result = hx71x.read_lowpass()

Returns the actual value of the load cell fed through an one stage IIR lowpass
filter. The properties of the filter can be set with set_time_constant().
When starting to use hx71x.read_lowpass() after a large change of the input
quantity or change of the ADC mode, it's advisable to first
call hx71x.setup_lowpass(). That will set the new start value for
hx71x.read_lowpass().

### setup_lowpass()

Restart the lowpass filter with the actual value of the ADC.

### rh = hx71x.set_time_constant(value=None)

Set the time constant used by hx71x.read_lowpass(). The range is 0-1.0. Smaller
values means longer times to settle and better smoothing.
If value is None, the actual value of the time constant is returned.

### value = hx71x.get_value()

Returns the difference of the filtered load cell value and the offset, as set
by hx71x.set_offset() or hx71x.tare()

### units = hx71x.set_scale(value)

Sets the scaling factor between thw raw sensor reading and the units as returned by
hx71x.get_unit().

### units = hx71x.get_units()

Returns the value delivered by hx71x.get_value() divided by the scale set by
hx71x.set_scale().

### hx71x.tare(times=15)

Determine the tare value of the load cell by averaging `times` raw readings.

### temperature = hx71x.temperature[raw=False])

Return the value of the internal temperature sensor. In order to get a °C value,
the sensor has to be calibrated first by calling hx71x_io.calibrate(). When `raw`
is set to True, the raw reading us returned.
The temperature() method returns meaningful values only for the HX710A device.
Besides that, do not expect precision.

### hx71x.calibrate(ref_temp [, gain=20.4, offset=None])

Calibrate the sensor. `ref_temp` is the actual temperature when calling calibrate().
`gain` is the ratio of LSB changes/°C. According to the data sheet, the default
value is 20.4. Offset is the ADC value offset. When omitted, the actual ADC
reading is used as offset. This option can be used, if ref_temp is the actual
temperature of the sensor. The values for gain and offset vary per device.
Especially getting the proper value for gain requires some effort.
At some sample devices the gain values were close to the default of 20.4.

## Examples

```
# Example for Pycom device, gpio mode
# Connections:
# Pin # | HX710/HX711
# ------|-----------
# P9    | data_pin
# P10   | clock_pin
#

from hx71x_gpio import HX71X_IO
from hx71x import HX71X
from machine import Pin

pin_OUT = Pin("P9", Pin.IN, pull=Pin.PULL_DOWN)
pin_SCK = Pin("P10", Pin.OUT)

hxc = HX71X_IO(pin_SCK, pin_OUT)
hx71x = HX71X(hxc)

hx71x.tare()
# for read() both the hxc and hx71x class can be used.
value = hxc.read()
value = hx71x.read()
value = hx71x.get_value()
```

```
# Example for micropython.org device, gpio mode
# Connections:
# Pin # | HX710/HX711
# ------|-----------
# 12    | data_pin
# 13    | clock_pin
#

from hx71x_gpio import HX71X_IO
from hx71x import HX71X
from machine import Pin

pin_OUT = Pin(12, Pin.IN, pull=Pin.PULL_DOWN)
pin_SCK = Pin(13, Pin.OUT)

hxc = HX71X_IO(pin_SCK, pin_OUT)
hx71x = HX71X(hxc)

hx71x.tare()
value = hx71x.read()
value = hx71x.get_value()
```

```
# Example for micropython.org device, RP2040 PIO mode
# Connections:
# Pin # | HX710/HX711
# ------|-----------
# 12    | data_pin
# 13    | clock_pin
#

from hx71x_pio import HX71X_IO
from hx71x import HX71X
from machine import Pin

pin_OUT = Pin(12, Pin.IN, pull=Pin.PULL_DOWN)
pin_SCK = Pin(13, Pin.OUT)

hxc = HX71X_IO(pin_SCK, pin_OUT)
hx71x = HX71X(hxc)

hx71x.tare()
value = hx71x.read()
value = hx71x.get_value()
```

```
# Example for Pycom device, spi mode
# Connections:
# Pin # | HX710/HX711
# ------|-----------
# P9    | data_pin
# P10   | clock_pin
# None  | spi clock
#

from hx71x_spi import HX71X_IO
from hx71x import HX71X
from machine import Pin, SPI

pin_OUT = Pin("P9", Pin.IN, pull=Pin.PULL_DOWN)
pin_SCK = Pin("P10", Pin.OUT)

spi = SPI(0, mode=SPI.MASTER, baudrate=1000000, polarity=0,
             phase=0, pins=(None, pin_SCK, pin_OUT))

hxc = HX71X_IO(pin_OUT, spi)
hx71x = HX71X(hxc)

hx71x.tare()
value = hxc.read()
value = hx71x.get_value()
```

```
# Example for micropython.org device, spi mode
# Connections:
# Pin # | HX710/HX711
# ------|-----------
# 12    | data_pin
# 13    | clock_pin
# 14    | spi clock

from hx71x_spi import HX71X_IO
from hx71x import HX71X
from machine import Pin

pin_OUT = Pin(12, Pin.IN, pull=Pin.PULL_DOWN)
pin_SCK = Pin(13, Pin.OUT)
spi_SCK = Pin(14)

spi = SPI(1, baudrate=1000000, polarity=0,
          phase=0, sck=spi_SCK, mosi=pin_SCK, miso=pin_OUT)

hxc = HX71X_IO(SCK, pin_OUT, spi)
hx71x = HX71X(hxc)

hx71x.tare()
value = hx71x.read()
value = hx71x.get_value()
```
