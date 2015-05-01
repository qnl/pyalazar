import alazar.board as alz
import alazar.processor as proc
import numpy as np

def do_acquire():

    b = alz.Alazar(1,1)

    b.setup_capture_clock("internal", "1 GS/s")

    b.setup_input_channels("1 V")

    b.setup_one_trigger()

    raw_proc = proc.Raw()
    ave = proc.Average()

    procs = b.acquire(1024, 128, 128, processors=[raw_proc, ave], timeout=1000)

    return procs