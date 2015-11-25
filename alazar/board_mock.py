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
"""Mock of a board for testing purposes."""
import multiprocessing as mp

import numpy as np

from board import (def_acq_params, AlazarException, is_9870, is_9360,
                   _make_channel_mask)
import params

from process import _process_buffers, _reshape_buffer
from processor import BufferProcessor


class MockAlazar(object):
    """Mock version of an Alazar board."""

    def __init__(self, board_type):
        """Initialize a new MockAlazar digitizer.

        Args:
            board_type: the numeric code for which board type to imitate.
        """
        self.board_type = board_type
        self.systemID = 1
        self.boardID = 1

    # Cython needs a getter to access this, imitate the same API
    def get_board_type(self):
        return self.board_type

    def get_board_model(self):
        return params.board_types[self.board_type]

    def setup_capture_clock(self, clock_source, sample_rate, decimation=0, edge="rising"):
        """Set the capture clock for this alazar board.

        This mock function is just a placeholder, it always returns success and
        doesn't do any validation of the inputs.
        """
        pass

    def setup_input_channels(self,
                             input_range,
                             channel="all",
                             coupling="dc",
                             impedance="50ohm",
                             bw="open"):
        """Set the input parameters for a digitizer channel.

        This mock function is just a placeholder, it always returns success and
        doesn't do any validation of the inputs.
        """
        pass

    def setup_one_trigger(self,
                          source_channel="ext",
                          slope="rising",
                          level=0.2,
                          ext_coupling="dc",
                          ext_range="5 V",
                          delay = 0):
        """Configure the Alazar trigger engine.

        This mock function is just a placeholder, it always returns success and
        doesn't do any validation of the inputs.
        """
        pass


    def acquire(self,
                samples_per_record,
                records_per_acquisition,
                records_per_buffer,
                channels_to_acquire="all",
                processors = [BufferProcessor()],
                buffer_count = 64,
                timeout = 5000):
        """Perform an acquisition using two-port NPT DMA mode.

        This mock function operates on the processors like a real board.  Each
        mock record is a rising sawtooth where each successive sample rises by
        one digitizer unit, wrapping back to zero.  It does not do any validation
        of the inputs, and never raises an exception.  It actually does pickle
        and unpickle the processors to mimic the behavior of the real processing
        function, to avoid possible confusion of mutating the input buffers.
        """
        buffers_per_acquisition = records_per_acquisition / records_per_buffer

        if is_9870(self.board_type):
            bits_per_sample = 8
        elif is_9360(self.board_type):
            bits_per_sample = 12
        else:
            raise MockAlazarException("MockAlazar only has bit depths for the "
                                      "9870 and 9360; got board type of {}"
                                      .format(self.board_type))

        (_, channel_count) = _make_channel_mask(self.board_type, channels_to_acquire)

        bytes_per_sample = (bits_per_sample + 7) / 8

        if bytes_per_sample <= 1:
            sample_type = np.uint8
        else:
            sample_type = np.uint16
        acq_params = def_acq_params(samples_per_record,
                                    records_per_acquisition,
                                    records_per_buffer,
                                    channel_count,
                                    sample_type,
                                    bits_per_sample)
        # get a queue to send buffers to the buffer processor
        buf_queue = mp.Queue()
        # get a queue to receive messages back from the processors
        comm = mp.Queue()
        # start a buffer processor to do the acquisition:
        buf_processor = mp.Process(target = _process_buffers,
                                   args = (buf_queue,
                                           comm,
                                           processors,
                                           acq_params,))
        buf_processor.start()

        try:

            ch1_buf = make_mock_buffer(records_per_buffer, samples_per_record,
                                       bits_per_sample, sample_type)
            ch1_buf.shape = records_per_buffer * samples_per_record

            ch2_buf = make_mock_buffer(records_per_buffer, samples_per_record,
                                       bits_per_sample, sample_type, True)
            ch2_buf.shape = records_per_buffer * samples_per_record

            buf = ch1_buf

            if channel_count > 1:
                buf = np.append(ch1_buf, ch2_buf)

            # handle each buffer
            for _ in xrange(buffers_per_acquisition):

                # pickles the buffer and sends to the worker
                buf_queue.put( (buf, None) )
        except Exception as err:
            buf_queue.put((None, err))

        # get the processors and return them
        return comm.get()


def make_mock_buffer(records_per_buffer, record_len, bit_depth, dtype, reverse=False):
    """Return a buffer of sawtooth records.

    Each record has the form [0, 1, 2, 3, ... 2**bit_depth - 1, 0, 1, ...];
    however, for sample depths greater than 8 bits, this value is bit-shifted
    into the most significant bits to fully mimic the behavior of the Alazar
    boards.

    Args:
        records_per_buffer: the number of records in the buffer, also the first
            value of the shape of the output array
        record_len: the number of samples in each records, also the second value
            of the shape of the output array
        bit_depth: the bit depth of the board to emulate
        dtype: the dtype of the resulting numpy array
        reverse (default=False): reverse the sawtooth pattern
    """
    buff = np.empty((records_per_buffer, record_len), dtype=dtype)
    the_iter = xrange(record_len)
    if reverse:
        the_iter = reversed(the_iter)
    for i in the_iter:
        buff[:, i] = i % bit_depth

    if bit_depth > 8:
        return buff << (16 - bit_depth)
    else:
        return buff


# --- Exception and error handling for MockAlazar boards


class MockAlazarException(Exception):
    pass



