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

from machine import Pin, idle, Timer
import time
import rp2

class HX71X_IO:
    def __init__(self, clock, data, mode=1, state_machine=0):
        self.clock = clock
        self.data = data
        self.clock.value(False)

        self.temp_offset = 0
        self.temp_gain = 20.4
        self.temp_ref = 0.0

        # create the state machine
        self.sm = rp2.StateMachine(state_machine, self.hx71x_pio, freq=1_000_000,
                                   sideset_base=self.clock, in_base=self.data,
                                   set_base=self.data, jmp_pin=self.data)
        self.set_mode(mode);


    @rp2.asm_pio(
        sideset_init=rp2.PIO.OUT_LOW,
        in_shiftdir=rp2.PIO.SHIFT_LEFT,
        autopull=False,
        autopush=False,
    )
    def hx71x_pio():
        label("start")
        pull()              .side (0)   # get the number of clock cycles
        mov(x, osr)         .side (0)
        jmp(not_x, "power_down") .side (0)
        set(pindirs, 0)     .side (0)    # Initial set pin direction.
# Wait for a high level = start of the DATA pulse
        wait(1, pin, 0)     .side (0)
# Wait for a low level = DATA signal
        wait(0, pin, 0)     .side (0)
        jmp(x_dec, "bitloop").side(0)   # just decrement

        label("bitloop")
        nop()               .side (1)[1]# active edge
        in_(pins, 1)        .side (0)   # get the pin and shift it in
        jmp(x_dec, "bitloop").side (0)  # test for more bits
        
        push(block)         .side (0)   # no, deliver data and start over
        jmp("start")        .side (0)   # And start over

        label("power_down")
        jmp("power_down")   .side (1)


    def __call__(self):
        return self.read()

    def set_mode(self, mode):
        if mode in (1, 2, 3):
            self.MODE = mode
        else:
            self.MODE = 1
        self.read()

    def read(self):
        # Feed the waiting state machine & get the data
        self.sm.restart()  # Just in case that it is not at the start.
        self.sm.put(self.MODE + 24)     # set pulse count 25-27
        self.sm.active(1)  # start the state machine
        start = time.ticks_ms()
        while time.ticks_diff(time.ticks_ms(), start) < 1000:
            # Wait for the result
            if self.sm.rx_fifo() > 0:
                break
            time.sleep_ms(1)
        else:
            self.sm.active(0)  # stop the state machine
            raise OSError("sensor timeout")

        result = self.sm.get(None, self.MODE)  # get the result & discard MODE bits
        self.sm.active(0)  # stop the state machine
        if result == 0x7fffffff:
            raise OSError("Sensor does not respond")
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
        self.sm.restart()  # Just in case that it is not at the start.
        self.sm.put(0)     # mode power down
        self.sm.active(1)  # start the state machine
        time.sleep_ms(1)
        self.sm.active(0)  # and stop it again

    def power_up(self):
        self.sm.restart()  # Just in case that it is not at the start.
        self.sm.active(1)  # start the state machine to set clock low
        self.sm.active(0)  # and stop it again
