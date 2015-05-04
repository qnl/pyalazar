import alazar.processor as proc
from alazar.processor import ProcessorException
from alazar.board import _AcqParams

from nose.tools import raises

import numpy as np

# some fake but realistic acquisition parameters
def acq_params():

    dtype = np.uint8

    return _AcqParams(samples_per_record=1024,
                      records_per_acquisition=128,
                      records_per_buffer=64,
                      channel_count=2,
                      dtype=dtype)

# make a bunch of test buffers with the same value
def buffers_same_val(params, value):
    bufs = [[np.full((params.records_per_buffer, params.samples_per_record),
                     value,
                     dtype=params.dtype,)
             for _ in range(params.channel_count)]
            for _ in range(params.buffers_per_acquisition)]
    return bufs

def buffers_random(params, min_val, max_val, seed=0):
    # seed the random number generator with a constant value
    np.random.seed(seed)
    bufs = [[(np.random.rand(params.records_per_buffer,
                             params.samples_per_record)*(max_val-min_val)+min_val
             ).astype(params.dtype)
             for _ in range(params.channel_count)]
            for _ in range(params.buffers_per_acquisition)]
    return bufs

# --- Automatic tests for various basic functions of all processors ---

class TestAllProcessors(object):

    def _setup_all_procs(self):
        # make a list of all the types of processors
        processors = []
        processors.append(proc.BufferProcessor())
        processors.append(proc.Average())
        processors.append(proc.Raw())

        return processors

    def test_abort(self):
        for processor in self._setup_all_procs():
            yield (self.check_abort, processor)

    @raises(ProcessorException)
    def check_abort(self, processor):
        processor.abort(Exception())
        processor.get_result()

# --- tests for Average processor

class TestAverage(object):

    def test_process(self):
        ave = proc.Average()
        params = acq_params()
        ave.initialize(params)

        bufs = buffers_same_val(params, 1)

        for (buf, buf_num) in zip(bufs,
                                  range(params.buffers_per_acquisition)):
            ave.process(buf, buf_num)

        ave.post_process()

        dat = ave.get_result()

        for chan in range(params.channel_count):
            assert (bufs[chan][0] == dat[chan]).all()

        # test re-use of same processor with re-initializtion

        ave.initialize(params)

        # use randomized buffers this time
        bufs = buffers_random(params, 0, 255)

        chan_aves = [None for _ in range(params.channel_count)]

        for (buf, buf_num) in zip(bufs,
                                  range(params.buffers_per_acquisition)):
            ave.process(buf, buf_num)

            for chan in range(params.channel_count):
                chan_mean = np.mean(buf[chan],axis=0)
                if chan_aves[chan] is None:
                    chan_aves[chan] = chan_mean
                else:
                    chan_aves[chan] += chan_mean

        chan_aves = [accum / params.buffers_per_acquisition for accum in chan_aves]

        ave.post_process()

        dat = ave.get_result()

        for chan in range(params.channel_count):

            assert (chan_aves[chan] == dat[chan]).all()

# --- tests for Raw processor

class TestRaw(object):

    def test_process(self):
        raw = proc.Raw()
        params = acq_params()
        raw.initialize()

        bufs = buffers_random(params, 0, 255)

        raw_dat = [np.empty((params.records_per_acquisition, params.samples_per_record),
                            dtype=params.dtype) for _ in range(params.channel_count)]

        for (buf, buf_num) in zip(bufs,
                                  range(params.buffers_per_acquisition)):
            raw.process(buf, buf_num)

            for chan in range(params.channel_count):
                rec_p_buf = params.records_per_buffer
                raw_dat[chan][buf_num*rec_p_buf:(buf_num+1)*rec_p_buf][:] = buf[chan]

        raw.post_process()

        dat = raw.get_result()

        for chan in range(params.channel_count):
            assert (raw[chan] == dat[chan]).all()




