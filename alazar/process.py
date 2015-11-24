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
"""Move this function to a separate module to work around cython packaging issue."""

def _process_buffers(buf_queue,
                    comm,
                    processors,
                    acq_params,):
    """Process buffers from the board."""
    # initialize the buffer processors
    for processor in processors:
        processor.initialize(acq_params)
    failure = False

    # loop over all the buffers we expect to receive
    for buf_num in xrange(acq_params["buffers_per_acquisition"]):
        # get the next buffer from the queue
        (buf, err) = buf_queue.get()
        # check for error condition
        if err is not None:
            # tell the data processors to abort
            for proc in processors:
                proc.abort(err)
            failure = True
            # end processing
            break
        # reshape the buffer
        chan_bufs = [_reshape_buffer(buf, chan, acq_params)
                     for chan in xrange(acq_params["channel_count"])]
        for proc in processors:
            proc.process(chan_bufs, buf_num)
            # TODO: exception handling for processor failure?
    # acquisition was successful, do post-processing
    if not failure:
        for proc in processors:
            proc.post_process()
    # send the finished processors back
    comm.put(processors)
    # done with buffer processing

# helper function for processing
def _reshape_buffer(buf, chan, acq_params):
    """Reshape a buffer from linear into n_records x m_samples."""
    chunk_size = acq_params["channel_chunk_size"]
    chan_dat = buf[chan*chunk_size : (chan+1)*chunk_size]
    chan_dat.shape = (acq_params["records_per_buffer"],
                      acq_params["samples_per_record"])
    return chan_dat