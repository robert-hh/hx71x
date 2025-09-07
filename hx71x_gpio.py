# MIT License

# Copyright (c) 2025

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from machine import enable_irq, disable_irq, Pin
import time

class HX71X_IO:
    def __init__(self, clock, data, mode=1):
        self.clock = clock
        self.data = data
        self.clock.value(False)

        self.temp_offset = 0
        self.temp_gain = 20.4
        self.temp_ref = 0.0

        # determine the number of attempts to find the trigger pulse
        start = time.ticks_us()
        for _ in range(3):
            temp = self.data()
        spent = time.ticks_diff(time.ticks_us(), start)
        self.__wait_loop = 3_000_000 // spent

        self.set_mode(mode)

    def __call__(self):
        return self.read()

    def set_mode(self, mode):
        if mode in (1, 2, 3):
            self.MODE = mode
        else:
            self.MODE = 1
        self.read()

    def conversion_done_cb(self, data):
        self.conversion_done = True
        data.irq(handler=None)

    def read(self):
        if hasattr(self.data, "irq"):
            self.conversion_done = False
            self.data.irq(trigger=Pin.IRQ_FALLING, handler=self.conversion_done_cb)
            # wait for the device being ready
            for _ in range(1000):
                if self.conversion_done == True:
                    break
                time.sleep_ms(1)
            else:
                self.data.irq(handler=None)
                raise OSError("Sensor does not respond")
        else:
            # wait polling for the trigger pulse
            for _ in range(self.__wait_loop):
                if self.data():
                    break
            else:
                raise OSError("No trigger pulse found")
            for _ in range(5000):
                if not self.data():
                    break
                time.sleep_us(100)
            else:
                raise OSError("Sensor does not respond")
 
        # shift in data, and gain & channel info
        result = 0
        for j in range(24 + self.MODE):
            state = disable_irq()
            self.clock(True)
            self.clock(False)
            enable_irq(state)
            result = (result << 1) | self.data()

        # shift back the extra bits
        result >>= self.MODE

        # check sign
        if result > 0x7fffff:
            result -= 0x1000000

        return result

    def temperature(self, raw=False):
        mode = self.MODE
        self.MODE = 2
        self.read()  # switch to temperature mode
        temp = self.read()  # read the temperature
        self.MODE = mode
        self.read()  # switch the mode back
        if raw:
            return temp
        else:
            return (temp - self.temp_offset) / self.temp_gain + self.temp_ref

    def calibrate(self, ref_temp, gain=20.4):
        self.temp_ref = ref_temp
        self.temp_gain = gain
        self.temp_offset = self.temperature(True)

    def power_down(self):
        self.clock.value(False)
        self.clock.value(True)

    def power_up(self):
        self.clock.value(False)
