from alazar import Alazar
import alazar.processor as proc
import numpy as np

import matplotlib.pyplot as plt

def do_acquire():

    b = Alazar(1,1)

    board_model = b.get_board_model()

    b.setup_capture_clock("internal", "10 MS/s")

    if board_model == 'ATS9360':
        b.setup_input_channels("400 mV")

        b.setup_one_trigger('ext', ext_range='TTL')
    else:
        b.setup_input_channels("1 V")

        b.setup_one_trigger()

    raw_proc = proc.Raw('test raw')
    ave = proc.Average('test ave')

    procs = b.acquire(1024, 100, 10, processors=[raw_proc, ave])

    return procs

def stats(chan):
    cmin, cmax = chan.min(), chan.max()
    return chan.shape, cmin, cmax, cmax - cmin, np.mean(chan[:])

def main():
    procs = do_acquire()

    chA, chB = procs[0].get_result()

    stat_str = 'shape = {}, min = {}, max = {}, delta = {}, mean = {}'

    plt.plot(range(1024), chA[3,:], 'r-')
    plt.plot(range(1024), chB[3,:], 'g-')
    plt.show()

    print 'acquisition statistics:'
    print 'channel A:'
    print stat_str.format(*stats(chA))
    print 'channel B:'
    print stat_str.format(*stats(chB))

if __name__ == '__main__':
    main()