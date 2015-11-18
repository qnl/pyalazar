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

import pickle

import numpy as np

from board import (def_acq_params, AlazarException, is_9870, is_9360,
                   _reshape_buffer, _make_channel_mask)
import params

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
                                    sample_type)

        mock_buffer = make_mock_buffer(records_per_buffer, samples_per_record,
                                       bits_per_sample, sample_type)

        chan_bufs = [mock_buffer for _ in xrange(channel_count)]

        # pickle and unpickle the processors
        # could probably just use deepcopy or something but this mimics how the
        # real board processes data as closely as possible.
        processors = pickle.loads(pickle.dumps(processors))

        # initialize the processors
        for proc in processors:
            proc.initialize(acq_params)

        for buf_num in xrange(buffers_per_acquisition):
            for proc in processors:
                proc.process(chan_bufs, buf_num)

        for proc in processors:
            proc.post_process()

        return processors


def make_mock_buffer(records_per_buffer, record_len, bit_depth, dtype):
    """Return a buffer of rising sawtooth records.

    Each record has the form [0, 1, 2, 3, ... 2**bit_depth - 1, 0, 1, ...]

    Args:
        records_per_buffer: the number of records in the buffer, also the first
            value of the shape of the output array
        record_len: the number of samples in each records, also the second value
            of the shape of the output array
        bit_depth: the bit depth of the board to emulate
        dtype: the dtype of the resulting numpy array
    """
    buff = np.empty((records_per_buffer, record_len), dtype=dtype)
    for i in xrange(record_len):
        buff[:, i] = i % bit_depth

    return buff


# --- Exception and error handling for MockAlazar boards


class MockAlazarException(Exception):
    pass



