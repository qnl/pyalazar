import multiprocessing as mp
import h5py as h5

def accum_channels_and_write(buf_queue, record_length, buf_size, buf_count, channel_count, file_path, dtype):
    """Accumulate all records, re-arrange into channels, and save to an hdf5 file.

    Test function.

    No exception handling yet.
    """

    record_count = buf_size * buf_count

    f = h5.File(file_path, 'w')
    dset = f.create_dataset("test data", (channel_count, record_count, record_length), dtype=dtype)

    # size of a contiguous set of channel records in a buffer
    channel_chunk_size = record_length * buf_size


    bufs_processed = 0
    while bufs_processed < buf_count:


        buf = buf_queue.recv()


        for chan in range(channel_count):

            chan_dat = buf[chan*channel_chunk_size : (chan+1)*channel_chunk_size]

            chan_dat.shape = (buf_count,record_length)

            dset[chan,bufs_processed*buf_size:(bufs_processed+1)*buf_size,:] = chan_dat

        bufs_processed += 1

    f.close()



