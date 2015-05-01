"""Buffer processors for Alazar acquisitions.

This module defines various buffer processors for Alazar acquisitions,
as well as their companion future object to get their result."""

import numpy as np
import h5py as h5

# base class for buffer processors
class BufferProcessor(object):
    """Example class for alazar buffer processors.

    This class demonstrates the methods necessary to define a processor.

    Processors should NOT raise exceptions; if a processing task fails,
        processor should store the error internally and ignore further input,
        ensuring that processors running in parallel are not interrupted.
        If an error does occur, the processor should re-raise the error when it
        is queried for it's result.

    initialize is called by the worker at the start of the acquisition.
    process is the function called with each individual buffer.
    post_process is called by the worker when the acquisition is finished. The
        result of the acquisition should be sent back to the client here.
    abort is called by the worker if the acquisition failed; the processor
        should safely clean up if this happens.
    """
    def __init__(self):
        self.params = None
        self.error = None

    def initialize(self, params):
        """Initialize this processor to process buffers.

        Do things like allocate memory here.
        """
        self.params = params

    def process(self, chan_bufs, buf_num):
        """Process a list of channel buffers."""
        pass

    def post_process(self):
        """Do any post-processing."""
        pass

    def get_result(self):
        """Return the result of the acquisition."""
        self.check_error()
        pass

    def abort(self, error):
        """If the acquisition failed, clean up."""
        self.error = error

    def check_error(self):
        if self.error is not None:
            raise ProcessorException("Acquisition failed: " + str(self.error))

class Raw(BufferProcessor):
    """Simple processor to return the raw acquisition data."""

    def __init__(self):
        super(Raw, self).__init__()
        self.dat_bufs = None

    def initialize(self, params):
        """Initialize the data buffer."""
        super(Raw, self).initialize(params)

        # create list of channel buffers to store the data
        # initial shape is 1D for simplicity
        self.dat_bufs = [np.empty((params.records_per_acquisition * params.samples_per_record,),
                                  params.dtype,)
                         for _ in range(params.channel_count)]

    def process(self, chan_bufs, buf_num):
        """Dump the buffer into the data buffer."""
        # this should be the same as the length of chan_buf
        chunk_size = self.params.channel_chunk_size

        # copy each channel into the appropriate buffer
        for (chan_buf, dat_buf) in zip(chan_bufs, self.dat_bufs):
            dat_buf[buf_num*chunk_size:(buf_num+1)*chunk_size] = chan_buf

    def post_process(self):
        """Reshape data into n_records x n_samples."""
        for dat_buf in self.dat_bufs:
            dat_buf.shape = (params.records_per_acquisition,
                             params.samples_per_record,)

    def get_result(self):
        """Return the data.

        Raises a ProcessorException if an error occurred."""
        self.check_error()
        return self.dat_bufs


class Average(BufferProcessor):
    """Simple processor to average all buffers together."""

    def __init__(self):
        super(Average, self).__init__()
        self.ave_bufs = None

    def initialize(self, params):
        """Initialize the averaging buffer."""
        super(Average, self).initialize(params)

        # create list of channel buffers to sum the results
        self.ave_bufs = [np.zeros((params.samples_per_record,), np.float)
                         for _ in range(params.channel_count)]

    def process(self, chan_bufs, buf_num):
        """Average the channel records together and add them to the averaging buffer."""

        for (chan_buf, ave_buf) in zip(chan_bufs, self.ave_bufs):
            ave_buf += np.sum(chan_buf,axis=0)

    def post_process(self):
        """Normalize the averages."""
        for ave_buf in self.ave_bufs:
            ave_buf /= self.params.records_per_acquisition

    def get_result(self):
        """Return the averages.

        Raises a ProcessorException if an error occurred."""
        self.check_error()
        return self.ave_bufs



# --- error handling

class ProcessorException(Exception):
    """Exception class for Processor errors."""
    pass
