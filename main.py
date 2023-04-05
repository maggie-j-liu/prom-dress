from machine import Pin
from time import sleep
import neopixel
import random
from wheel import wheel
import rp2

mode = 0
modes = [None, "purple_border", "sparkle_slow", "sparkle", "rb_static", "rb_slow", "rb_fast", "rainbow"]

led = Pin("LED", Pin.OUT)
led.on()
sleep(1)
led.off()

# neopixels

NUM_PIXELS = 200

SPARKLE_COLOR = (10, 80, 190)

pixels = neopixel.NeoPixel(Pin(28), NUM_PIXELS)

# min_step = 15
# max_step = 20
# frequency = 8
# new_sparkles = 5
raw_rotation = 0

class Pixel:
    def __init__(self, idx):
        self.idx = idx
        self.done = True
    def set_color(self, color, min_step, max_step):
        pixels[self.idx] = color
        # print('min, max', min_step, max_step)
        try:
          self.steps = random.randint(min_step, max_step)
        except:
          self.steps = 5
        self.step = tuple(rgb / self.steps for rgb in color)
        self.done = False
    def next_color(self):
        curr = pixels[self.idx]
        pixels[self.idx] = tuple(max(int(curr[idx] - self.step[idx]), 0) for idx in range(3))
        # print(pixels[self.idx])
        if pixels[self.idx] == (0, 0, 0):
            self.done = True


def adjust_color(color):
    # return (color[0], max(min(round(color[1] + raw_rotation), 255), 0), color[2])
    return tuple(min(max(color[idx] + random.randint(-100, 100), 0), 255) for idx in range(3))

def speed(speed):
    global min_step, max_step, frequency, new_sparkles
    # speed is from 0 to 5?
    min_step = max(round(27 - 5 * speed), 1)
    max_step = round(min_step + 5)
    new_sparkles = min(25, round(4 + speed))
    frequency = round(max(15 - speed, 5))

pixels.fill((0, 0, 0))
pixels.write()

def check():
    global mode
    if rp2.bootsel_button(): # type: ignore
        while True:
            if not rp2.bootsel_button(): # type: ignore
                pixels.fill((0, 0, 0))
                pixels.write()
                mode += 1
                mode %= len(modes)
                return True
    return False

def rainbow_border(wait=None):
    STEP = 256 / 22
    offset = 0
    while True:
        idx = 0
        for i in range(22):
            real_i = (i + offset) % 22
            pix_idx = NUM_PIXELS - real_i - 1 
            pixels[pix_idx] = wheel(int(idx) % 256)
            idx += STEP
        pixels.write()

        offset += 1
        offset %= 22

        if wait is None:
            while True:
                if check():
                    return
                sleep(0.1)
        if check():
            return

        sleep(wait)

def sparkle(frequency, min_step, max_step, new_sparkles):
    sparkles = [Pixel(i) for i in range(NUM_PIXELS)]
    loop = 1
    while True:
        for sparkle in sparkles:
            if not sparkle.done:
                sparkle.next_color()
        pixels.write()

        if loop == 0:
            done = [pixel for pixel in sparkles if pixel.done]
            if len(done) > 0:
                done_pixels = [random.randint(0, len(done) - 1) for _ in range(new_sparkles)]
                for idx in done_pixels:
                    done[idx].set_color(adjust_color(SPARKLE_COLOR), min_step, max_step)
                pixels.write()
        
        if check():
            break
        sleep(0.02)
        loop += 1
        loop %= frequency

while True:
    # print(modes[mode])
    if modes[mode] == "sparkle":
        sparkle(8, 15, 20, 5) 
    elif modes[mode] == "sparkle_slow":
        sparkle(15, 35, 40, 4)
    elif modes[mode] == "rainbow":
        idx = 0
        STEP = 16
        pix = NUM_PIXELS - 1

        done = False
        for i in range(NUM_PIXELS - 1, -1, -1):
            # shift all pixels to the right
            for j in range(NUM_PIXELS - 1):
                pixels[j] = pixels[j + 1]
            
            # blenddd
            if pix > 0:
                pixels[pix - 1] = tuple(grb // 20 for grb in pixels[pix])
            
            if pix > 1:
                pixels[pix - 2] = tuple(grb // 40 for grb in pixels[pix])

            # set the first pixel to the next color
            pixels[NUM_PIXELS - 1] = wheel(idx % 256)

            idx += STEP
            pix -= 1
            pixels.write()

            if check():
                done = True 
                break

            sleep(0.01)

        if done:
            continue

        pix = 1
        # go backwards :D
        for i in range(NUM_PIXELS):
            # shift all pixels to the right
            for j in range(NUM_PIXELS - 1, 0, -1):
                pixels[j] = pixels[j - 1]
            
            # blenddd
            if pix > 0 and pix < NUM_PIXELS:
                pixels[pix - 1] = tuple(grb // 20 for grb in pixels[pix])
            
            if pix > 1 and pix < NUM_PIXELS:
                pixels[pix - 2] = tuple(grb // 40 for grb in pixels[pix])

            # clear the first pixel 
            pixels[0] = (0, 0, 0) 

            idx -= STEP
            pix += 1
            pixels.write()
            
            if check():
                break 

            sleep(0.01)
    elif modes[mode] == "rb_static":
        rainbow_border()
    elif modes[mode] == "rb_slow":
        rainbow_border(0.05)
    elif modes[mode] == "rb_fast":
        rainbow_border(0.02)
    elif modes[mode] == "purple_border":
        for i in range(22):
            pix_idx = NUM_PIXELS - i - 1 
            pixels[pix_idx] = adjust_color(SPARKLE_COLOR)
        pixels.write()
        while not check():
            sleep(0.1)
    else:
        check() 
        sleep(0.1)

