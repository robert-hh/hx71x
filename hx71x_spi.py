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

from machine import idle
import time


class HX71X_IO:
    def __init__(self, data, spi, mode=1):
        self.data = data
        self.spi = spi

        self.clock_25 = b'\xaa\xaa\xaa\xaa\xaa\xaa\x80'
        self.clock_26 = b'\xaa\xaa\xaa\xaa\xaa\xaa\xa0'
        self.clock_27 = b'\xaa\xaa\xaa\xaa\xaa\xaa\xa8'
        self.clock_table = [None, self.clock_25, self.clock_26, self.clock_27]
        self.lookup = (b'\x00\x01\x00\x00\x02\x03\x00\x00\x00\x00\x00\x00'
                       b'\x00\x00\x00\x00\x04\x05\x00\x00\x06\x07\x00\x00'
                       b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
                       b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
                       b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
                       b'\x00\x00\x00\x00\x08\x09\x00\x00\x0a\x0b\x00\x00'
                       b'\x00\x00\x00\x00\x00\x00\x00\x00\x0c\x0d\x00\x00'
                       b'\x0e\x0f')
        self.in_data = bytearray(7)

        # determine the number of attempts to find the trigger pulse
        start = time.ticks_us()
        for _ in range(3):
            temp = self.data()
        spent = time.ticks_diff(time.ticks_us(), start)
        self.__wait_loop = 3_000_000 // spent

        self.temp_offset = 0
        self.temp_gain = 20.4
        self.temp_ref = 0.0

        self.set_mode(mode)

    def __call__(self):
        return self.read()

    def set_mode(self, mode):
        if mode in (1, 2, 3):
            self.MODE = mode
        else:
            self.MODE = 1
        self.read()

    def read(self):
        # wait polling for the trigger pulse
        for _ in range(self.__wait_loop):
            if self.data():
                break
        else:
            raise OSError("No trigger pulse found")
        for _ in range(1000):
            if not self.data():
                break
            time.sleep_ms(1)
        else:
            raise OSError("Sensor does not respond")

        # get the data and set channel and gain
        self.spi.write_readinto(self.clock_table[self.MODE], self.in_data)

        # pack the data into a single value
        result = 0
        for _ in range(6):
            result = (result << 4) + self.lookup[self.in_data[_] & 0x55]

        # check sign
        if result > 0x7fffff:
            result -= 0x1000000

        return result

    def temperature(self, raw=False):
        mode = self.MODE
        self.MODE = 2
        self.read()  # switch to temperature mode
        temp = self.read() >> 9 # read the temperature and scale it down
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

    # Emnpty methods of power_down() and power_up().

    def power_down(self):
        pass

    def power_up(self):
        pass
