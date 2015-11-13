# Copyright (C) 2015  Chris Macklin
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
import alazar.processor as proc
from alazar.processor import ProcessorException
from alazar.board import def_acq_params

from nose.tools import raises

import numpy as np

# some fake but realistic acquisition parameters
def mock_acq_params():

    dtype = np.uint8

    return def_acq_params(samples_per_record=1024,
                          records_per_acquisition=128,
                          records_per_buffer=64,
                          channel_count=2,
                          dtype=dtype)

# make a bunch of test buffers with the same value
def buffers_same_val(params, value):
    bufs = [[np.full((params["records_per_buffer"], params["samples_per_record"]),
                     value,
                     dtype=params["dtype"],)
             for _ in range(params["channel_count"])]
            for _ in range(params["buffers_per_acquisition"])]
    return bufs

def buffers_random(params, min_val, max_val, seed=0):
    # seed the random number generator with a constant value
    np.random.seed(seed)
    bufs = [[(np.random.rand(params["records_per_buffer"],
                             params["samples_per_record"])*(max_val-min_val)+min_val
             ).astype(params["dtype"])
             for _ in range(params["channel_count"])]
            for _ in range(params["buffers_per_acquisition"])]
    return bufs

# --- Automatic tests for various basic functions of all processors ---

class TestAllProcessors(object):

    def _setup_all_procs(self):
        # make a list of all the types of processors
        processors = []
        processors.append(proc.BufferProcessor())
        processors.append(proc.Average())
        processors.append(proc.Raw())
        processors.append(proc.AverageN(1))
        processors.append(proc.Chunk(1,0,1))

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
        yield self.check_process, mock_acq_params()

    def check_process(self, params):

        ave = proc.Average()

        bufs = buffers_same_val(params, 1)

        emulate_acq(params, bufs, ave)

        dat = ave.get_result()

        for chan in range(params["channel_count"]):
            assert (bufs[chan][0] == dat[chan]).all()

        # test re-use of same processor with re-initializtion

        # use randomized buffers this time
        bufs = buffers_random(params, 0, 255)

        raw_dat = bufs_to_raw_array(bufs, params)

        chan_aves = [np.mean(chan_dat,axis=0) for chan_dat in raw_dat]

        emulate_acq(params, bufs, ave)

        dat = ave.get_result()

        for chan in range(params["channel_count"]):

            assert (chan_aves[chan] == dat[chan]).all()

# --- tests for Raw processor

class TestRaw(object):

    def test_process(self):
        yield self.check_process, mock_acq_params()

    def check_process(self, params):
        raw = proc.Raw()

        bufs = buffers_random(params, 0, 255)

        raw_dat = bufs_to_raw_array(bufs, params)

        emulate_acq(params, bufs, raw)

        dat = raw.get_result()

        for chan in range(params["channel_count"]):
            assert (raw_dat[chan] == dat[chan]).all()

# --- tests for AverageN processor

class TestAverageN(object):

    @raises(ProcessorException)
    def test_total_records_not_divisible_by_n(self):

        params = mock_acq_params()
        assert params["records_per_acquisition"] % 3 != 0

        ave_n = proc.AverageN(3)

        bufs = buffers_same_val(params, 1)

        emulate_acq(params, bufs, ave_n)

        ave_n.get_result()

    @raises(ProcessorException)
    def test_zero_n(self):
        proc.AverageN(0)

    @raises(ProcessorException)
    def test_negative_n(self):
        proc.AverageN(-1)

    def test_process(self):

        n_vals = [1, 2, 16]

        for val in n_vals:
            yield self.check_process_for_n_val, val, mock_acq_params()

    def check_process_for_n_val(self, n_val, params):

        ave_n = proc.AverageN(n_val)

        bufs = buffers_random(params, 0, 255)

        raw_dat = bufs_to_raw_array(bufs, params)

        correct_results = [np.empty((n_val, params["samples_per_record"]), np.float)
                           for _ in range(params["channel_count"])]

        # make the correct averaged data
        for rec_type in range(n_val):
            for result, chan_dat in zip(correct_results, raw_dat):
                result[rec_type] = np.mean(chan_dat[rec_type::n_val],axis=0)

        emulate_acq(params, bufs, ave_n)

        result = ave_n.get_result()

        for (correct, returned) in zip(correct_results, result):

            assert (correct == returned).all()

class TestChunk(object):

    @raises(ProcessorException)
    def test_total_records_not_divisible_by_n(self):
        params = mock_acq_params()
        assert params["records_per_acquisition"] % 3 != 0

        chunk = proc.Chunk(3, 0, 1)

        bufs = buffers_same_val(params, 1)

        emulate_acq(params, bufs, chunk)

        chunk.get_result()

    @raises(ProcessorException)
    def test_chunk_stop_larger_than_rec_size(self):
        params = mock_acq_params()

        chunk = proc.Chunk(1, 0, params["samples_per_record"] + 1)

        bufs = buffers_same_val(params, 1)

        emulate_acq(params, bufs, chunk)

        chunk.get_result()

    def test_process(self):
        n_rec_types = [1, 2, 4, 16]

        for n_rec_type in n_rec_types:
            yield (self.check_process_for_n_rec_types_start_stop,
                   n_rec_type, 0, 10, mock_acq_params())

    def check_process_for_n_rec_types_start_stop(self, n_rec_types, start, stop, params):

        chunk = proc.Chunk(n_rec_types, start, stop)

        bufs = buffers_random(params, 0, 255)

        raw_dat = bufs_to_raw_array(bufs, params)

        chunked_dat = [np.mean(chan_dat[:,start:stop], axis=1) for chan_dat in raw_dat]


        records_per_rec_type = params["records_per_acquisition"] / n_rec_types

        correct_result = [np.empty((n_rec_types, records_per_rec_type), dtype=np.float) for _ in raw_dat]
        for (chan_dat, result_buf) in zip(chunked_dat, correct_result):
            for rec_type in range(n_rec_types):
                result_buf[rec_type] = chan_dat[rec_type::n_rec_types]

        emulate_acq(params, bufs, chunk)

        result = chunk.get_result()

        for (result_chan, correct_result_chan) in zip(result, correct_result):

            assert (result_chan == correct_result_chan).all()




# --- Helper functions

def bufs_to_raw_array(bufs, params):

    raw_dat = [np.empty((params["records_per_acquisition"], params["samples_per_record"]),
                        dtype=params["dtype"]) for _ in range(params["channel_count"])]

    for (buf_num, buf) in enumerate(bufs):

        for chan in range(params["channel_count"]):
            rec_p_buf = params["records_per_buffer"]
            raw_dat[chan][buf_num*rec_p_buf:(buf_num+1)*rec_p_buf][:] = buf[chan]

    return raw_dat

def run_process(bufs, procs):
    """Run this processor on all of these buffers.

    procs can be a single processor or a list of processors.
    """
    for (buf_num, buf) in enumerate(bufs):
        if isinstance(procs, list):
            for processor in procs:
                processor.process(buf, buf_num)
        else:
            procs.process(buf, buf_num)

def emulate_acq(params, bufs, procs):
    """Emulate the action of the acquire() function."""
    is_list = isinstance(procs, list)

    if is_list:
        for processor in procs:
            processor.initialize(params)
    else:
        procs.initialize(params)

    run_process(bufs, procs)

    if is_list:
        for processor in procs:
            processor.post_process()
    else:
        procs.post_process()









