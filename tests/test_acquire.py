import alazar.alazar as alz
import numpy as np

def do_acquire():

	b = alz.Alazar(1,1)

	b.setup_capture_clock("internal", "1 GS/s")

	b.setup_input_channels("1 V")

	b.setup_one_trigger()
	return b.acquire(10240,65536,128,timeout=1000)