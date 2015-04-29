import multiprocessing as mp
import h5py as h5
import time

def accum_channels_and_write(buf_queue, samples_per_record, records_per_buffer, buffers_per_acquisition, channel_count, file_path, dtype):
    """Accumulate all records, re-arrange into channels, and save to an hdf5 file.

    Test function.

    No exception handling yet.
    """

    record_count = records_per_buffer * buffers_per_acquisition

    f = h5.File(file_path, 'w')
    dset = f.create_dataset("test data", (channel_count, record_count, samples_per_record), dtype=dtype)

    # size of a contiguous set of channel records in a buffer
    channel_chunk_size = samples_per_record * records_per_buffer

    bufs_processed = 0
    start_time = time.clock()

    while bufs_processed < buffers_per_acquisition:

        buf = buf_queue.get()

        for chan in range(channel_count):

            chan_dat = buf[chan*channel_chunk_size : (chan+1)*channel_chunk_size]

            chan_dat.shape = (records_per_buffer,samples_per_record)

            dset[chan,bufs_processed*records_per_buffer:(bufs_processed+1)*records_per_buffer,:] = chan_dat

        bufs_processed += 1

        if bufs_processed % 10 == 0:
            
            print "processed {} buffers".format(bufs_processed)

    stop_time = time.clock()
    print "worker write time: {} s".format(stop_time-start_time)

    f.close()



