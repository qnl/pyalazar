import alazar.alazar as alz
import numpy as np

def do_acquire():

	b = alz.Alazar(1,1)

	b.setup_capture_clock("internal", "100 MS/s")

	b.setup_input_channels("1 V")

	b.setup_one_trigger(level=0.2)

	return b.acquire(256,2,1,timeout=1000)