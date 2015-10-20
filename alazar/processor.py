"""Buffer processors for Alazar acquisitions.

This module defines various buffer processors for Alazar acquisitions,
as well as their companion future object to get their result."""

import numpy as np
import h5py as h5

# base class for buffer processors
class BufferProcessor(object):
    """Example class for alazar buffer processors.

    This class demonstrates the methods necessary to define a processor.

    Processors should NOT raise exceptions; if a processing task fails, the
    processor should store the error internally and ignore further input,
    ensuring that processors running in parallel are not interrupted.
    If an error does occur, the processor should re-raise the error when it
    is queried for its result.

    initialize is called at the start of the acquisition.
    process is the function called with each individual buffer.
    post_process is called when the acquisition is finished; do any work that
        requires all of the data here, or post-processing tasks like reshaping
        data buffers, writing arrays to disk, etc.
    abort is called if the acquisition failed; the processor should safely clean
        up if this happens, and store and re-raise the acquisition error if it
        is later queried for its result.
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
        # If this processor already failed, do not overwrite the internal error
        # with the acquisition error.
        if not self.error:
            self.error = error

    def check_error(self):
        if self.error:
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
        self.dat_bufs = [np.empty((params.records_per_acquisition, params.samples_per_record,),
                                  params.dtype,)
                         for _ in range(params.channel_count)]

    def process(self, chan_bufs, buf_num):
        """Dump the buffer into the data buffer."""
        recs_per_buf = self.params.records_per_buffer

        # copy each channel into the appropriate buffer
        for (chan_buf, dat_buf) in zip(chan_bufs, self.dat_bufs):
            dat_buf[buf_num*recs_per_buf: (buf_num+1)*recs_per_buf,:] = chan_buf

    def post_process(self):
        pass

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
        if self.error:
            return
        for (chan_buf, ave_buf) in zip(chan_bufs, self.ave_bufs):
            ave_buf += np.sum(chan_buf,axis=0, dtype=np.int64)

    def post_process(self):
        """Normalize the averages."""
        if self.error:
            return
        for ave_buf in self.ave_bufs:
            ave_buf /= self.params.records_per_acquisition

    def get_result(self):
        """Return the averages.

        Raises a ProcessorException if an error occurred."""
        self.check_error()
        return self.ave_bufs

class AverageN(BufferProcessor):
    """Processor to average all buffers into N types of records.

    This processor expects each consecutive set of N records
        to contain one of each of the N types, in order.
    """

    def __init__(self, n_rec_types):
        """Create a new AverageN processor.

        Args:
            n_rec_types (int): The number of record types to average into.  Must
                be a positive non-zero integer.  The number of records in the
                acquisition must be a multiple of this or this processor will
                return an error condition.
        """
        super(AverageN, self).__init__()
        if n_rec_types < 1:
            raise ProcessorException("n_rec_types must be greater than 0."
                                     " Provided: {}".format(n_rec_types))
        self.ave_bufs = None
        self.n_rec_types = n_rec_types

    def initialize(self, params):
        """Initialize the averaging buffers."""
        super(AverageN, self).initialize(params)
        if params.records_per_acquisition % self.n_rec_types != 0:
            self.error = ProcessorException("Records per acquisition ({}) must be a"
                                            " multiple of n_rec_types ({})"
                                            .format(params.records_per_acquisition,
                                                    self.n_rec_types))
            return
        # create list of channel buffers to sum the results
        self.ave_bufs = [np.zeros((self.n_rec_types,params.samples_per_record,), np.float)
                         for _ in range(params.channel_count)]

    def process(self, chan_bufs, buf_num):
        """Average the channel records together and add them to the averaging buffers."""
        if self.error:
            return
        # figure out what the type of the first record in the buffer is
        first_rec_type = (buf_num*self.params.records_per_buffer) % self.n_rec_types

        for (chan_buf, ave_buf) in zip(chan_bufs, self.ave_bufs):
            for rec_type in range(self.n_rec_types):
                # calculate the offset needed to index the channel buffer into this record type
                offset = (rec_type + first_rec_type) % self.n_rec_types
                # if records_per_buffer is less than n_rec_types this record may lack this type
                if offset < self.params.records_per_buffer:
                    ave_buf[rec_type] += np.sum(chan_buf[offset::self.n_rec_types], axis=0, dtype=np.int64)

    def post_process(self):
        """Normalize the averages."""
        if self.error:
            return
        # normalize by the total number of each record type collected
        for ave_buf in self.ave_bufs:
            ave_buf /= (self.params.records_per_acquisition / self.n_rec_types)

    def get_result(self):
        """Return the averages.

        Returns:
            List of channel results for the acquisition; each entry is a numpy
            array of shape (n_rec_types, samples_per_record).

        Raises:
            ProcessorException if an error occurred.
        """
        self.check_error()
        return self.ave_bufs

class Chunk(BufferProcessor):
    """Processor to collect a chunk of N record types."""
    def __init__(self, n_rec_types, start, stop):
        """Create a new Chunk processor.

        Args:
            n_rec_types (int): The number of record types.  Must
                be a positive non-zero integer.  The number of records in the
                acquisition must be a multiple of this or this processor will
                return an error.

            start (int): The sample number at the start of the chunk (inclusive).
            stop (int): The sample number at the end of the chunk (exclusive).
        """
        super(Chunk, self).__init__()
        if n_rec_types < 1:
            raise ProcessorException("n_rec_types must be greater than 0."
                                     " Provided: {}".format(n_rec_types))
        if start < 0 or start >= stop:
            raise ProcessorException("Invalid start ({}) and stop ({}) parameters."
                                     .format(start, stop))
        self.n_rec_types = n_rec_types
        self.start = start
        self.stop = stop

    def initialize(self, params):
        """Initialize the data array."""
        super(Chunk, self).initialize(params)
        if params.records_per_acquisition % self.n_rec_types != 0:
            self.error = ProcessorException("Records per acquisition ({}) must be a"
                                            " multiple of n_rec_types ({})"
                                            .format(params.records_per_acquisition,
                                                    self.n_rec_types))
            return
        if self.stop > params.samples_per_record:
            self.error = ProcessorException("Chunk stop ({}) is greater than "
                                            "samples per record ({})"
                                            .format(self.stop,
                                                    params.samples_per_record))
        self.chunk_bufs = [np.empty((params.records_per_acquisition,), dtype=np.float)
                           for _ in range(params.channel_count)]

    def process(self, chan_bufs, buf_num):
        """Collect all of the chunks."""
        if self.error:
            return
        recs_per_buf = self.params.records_per_buffer
        rec_offset = buf_num*recs_per_buf
        for (chan_buf, chunk_buf) in zip(chan_bufs, self.chunk_bufs):
                chunk_buf_view = chunk_buf[rec_offset:rec_offset+recs_per_buf]
                # integrate this chunk and put result into the data array
                chunk_buf_view[:] = np.mean(chan_buf[:,self.start:self.stop], axis=1)

    def post_process(self):
        """Reshape the data into record types."""
        if self.error:
            return
        # reshape the linear buffer into (rec type, records) in place
        for chan, chunk_buf in enumerate(self.chunk_bufs):
            chunk_buf.shape = (self.params.records_per_acquisition / self.n_rec_types,
                               self.n_rec_types)
            self.chunk_bufs[chan] = np.swapaxes(chunk_buf,0,1)

    def get_result(self):
        """Return the chunked records.

        Returns:
            List of channel chunks for the acquisition; each entry is a numpy array
            of shape (n_rec_types, n_recs_per_rec_type).

        Raises:
            ProcessorException if an error occurred.
        """
        self.check_error()
        return self.chunk_bufs

# --- error handling

class ProcessorException(Exception):
    """Exception class for Processor errors."""
    pass
