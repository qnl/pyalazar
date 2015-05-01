import alazar.processor as proc
from alazar.processor import ProcessorException
from alazar.board import _AcqParams

from nose.tools import raises

import numpy as np

# some fake but realistic acquisition parameters
def params():

    dtype = np.uint8

    return _AcqParams(samples_per_record=1024,
                      records_per_acquisition=128,
                      records_per_buffer=64,
                      channel_count=2,
                      dtype=dtype)

# make a bunch of test buffers with the same value
def test_buffers_same_val(params, value):
    bufs = [[np.empty((params.records_per_buffer, params.samples_per_record),
                     dtype=params.dtype,).fill(value)
             for _ in range(params.channel_count)]
            for _ in range(params.buffers_per_acquisition)]
    return bufs


class TestAverage(object):

    @raises(ProcessorException)
    def test_abort(self):

        ave = proc.Average()
        e = Exception()

        ave.abort(e)
        ave.get_result()

    def test_process(self):
        ave = proc.Average()
        params = params()
        ave.initialize(params)

        bufs = test_buffers_same_val(params,1)

        for (buf, buf_num) in zip(bufs,
                                  range(params.buffers_per_acquisition)):
            ave.process(buf, buf_num)

        ave.post_process()

        dat = ave.get_result()

        assert bufs[0][0] == dat[0]
        assert bufs[0][0] == dat[1]




