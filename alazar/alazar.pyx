cimport c_alazar_api

import numpy as np
cimport numpy as np

# C wrapper class to represent an Alazar digitizer
cdef class Alazar(object):

    # handle to an alazar board
    cdef c_alazar_api.HANDLE board
    cdef int board_type

    # use __cinit__ to make sure this is run
    def __cinit__(self, systemID, boardID):
        """Initialize a new Alazar digitizer wrapper.

        systemID and boardID identify which board to wrap.
        raises an AlazarException if the board cannot be connected to or identified.
        Ideally, do not construct more than one wrapper to a board simultaneously.
        """
        self.board = c_alazar_api.AlazarGetBoardBySystemID(systemID,boardID)
        if self.board is NULL:
            raise AlazarException("Could not connect to an Alazar board with system ID {}, board ID {}.".format(systemID,boardID))

        self.board_type = c_alazar_api.AlazarGetBoardKind(self.board)
        if self.board_type == 0:
            raise AlazarException("Connected to board with system ID {}, board ID {}, but could not identify board!".format(systemID,boardID))

    # need a getter to access this from python
    def get_board_type(self):
        return self.board_type


    def setup_capture_clock(self, clock_source, sample_rate, decimation=0, edge="rising"):
        """Set the capture clock for this alazar board.

        clock_source is the name of a valid clock source for this board
        sample_rate is the name of a valid sample rate for this board, or the numeric sample
            rate in MHz for the case of 9360 10 MHz PLL clock
        for 9870, if clock_source is not "internal", sample_rate is ignored
        for clock_source = "external 10 MHz ref":
            for 9870: decimation determines the sample clock as 1 GHz / decimation,
                with decimination equal to 1, 2, 4, or a multiple of 10.
            for 9360: decimation is ignored, sample_rate determines the sample clock
        edge = "rising" or "falling" determines whether the alazar sample clock
            triggers on the rising or falling edge of the reference clock

        Raises an AlazarException for invalid parameters, or if the set clock call fails.

        The logic of this function is presently hardwired for the ATS9870 and ATS9360.
        Extending to other models will require modifying this function.
        """

        # validate edge
        if edge == "rising":
            edge_code = 0
        elif edge == "falling":
            edge_code = 1
        else:
            raise AlazarException("Edge must be either 'rising' or 'falling'; supplied: '{}'".format(edge))



        # validate clock_source and get code
        try:
            source_code = clock_sources(self.board_type)[clock_source]
        except KeyError:
            raise AlazarException("Clock source '{}' is not valid.".format(clock_source))


        # validate sample_rate, decimation, and set the board
        if clock_source == "internal":

            # get the sample rate ID
            try:
                rate_code = sample_rates(self.board_type)[sample_rate]
            except KeyError:
                raise AlazarException("Sample rate '{}' is not valid.".format(sample_rate))

            if sample_rate == "user-defined" or sample_rate == "10 MHz ref":
                raise AlazarException("Internal clock requires an explicit sample rate; supplied: '{}'".format(sample_rate))

            ret_code = c_alazar_api.AlazarSetCaptureClock(self.board, source_code, rate_code, edge_code, 0)

        elif clock_source == "external 10 MHz ref": # 10 MHz PLL

            if is_9870(self.board_type):
                # validate the decimation parameter
                if not _check_decimation(self.board_type, decimation):
                    raise AlazarException("Invalid decimation '{}' for clock source '{}'.".format(decimation,clock_source))

                rate_code = sample_rates(self.board_type)["10 MHz ref"]
                ret_code = c_alazar_api.AlazarSetCaptureClock(self.board, source_code, rate_code, edge_code, decimation)


            elif is_9360(self.board_type):
                # validate sample rate
                if sample_rate < 300 or sample_rate > 1800:
                    raise AlazarException("Sample rate for 10 MHz ref must be between 300 MHz and 1800 MHz; supplied: {}".format(sample_rate))

                rate_code = sample_rate * 1000000
                ret_code = c_alazar_api.AlazarSetCaptureClock(self.board, source_code, rate_code, edge_code, 1)

            else:
                raise AlazarException("Could not set clock source for board type {}".format(self.board_type))

        else: # external sample clock
            rate_code = sample_rates(self.board_type)["user-defined"]
            ret_code = c_alazar_api.AlazarSetCaptureClock(self.board, source_code, rate_code, edge_code, 0)

        # raise exception if ret_code was an error
        _check_return_code(ret_code, "Set capture clock failed with code {}:".format(ret_code))


    def setup_input_channels(self, input_range, channel="all", coupling="dc", impedance="50ohm", bw="open"):
        """Set the input parameters for a digitizer channel.

        If channel = "all", all available channels are set to the given parameters.
        Otherwise, channel should be 'A', 'B', 'C', etc.  Defaults to "all".
        couling is either "ac" or "dc", defaults to "dc"; 9360 only supports DC
        range is a valid range string
        impedance is optional as the ATS9870/ATS9360 are not switchable
        bw is either "open" or "limit" to engage 20 MHz filter, default is "open"
        """

        # validate coupling
        try:
            coupling_code = input_couplings(self.board_type)[coupling]
        except KeyError:
            raise AlazarException("Invalid input coupling: {}".format(coupling))

        # validate range
        try:
            range_code = ranges(self.board_type)[input_range]
        except KeyError:
            raise AlazarException("Invalid range parameter: '{}'".format(input_range))

        # validate impedance
        if impedance != "50ohm":
            raise AlazarException("Impedance must be '50ohm'; provided: '{}'".format(impedance))

        # validate bandwidth
        if bw == "open":
            bw_code = 0
        elif bw == "limit":
            bw_code = 1
        else:
            raise AlazarException("Bandwidth must be 'open' or 'limit'; provided: '{}'".format(bw))

        # validate channel parameter and set input
        if channel == "all":
            for chan, chan_code in channels(self.board_type).iteritems():
                # impedance hard-coded to 50 ohm code
                ret_code = c_alazar_api.AlazarInputControl(self.board,
                                                           chan_code,
                                                           coupling_code,
                                                           range_code,
                                                           2)
                # check for API success
                _check_return_code(ret_code, "Error setting channel {} input:".format(chan))

                ret_code = c_alazar_api.AlazarSetBWLimit(self.board, chan_code, bw_code)
                _check_return_code(ret_code, "Error setting channel {} BW limit:".format(chan))
        else:
            try:
                chan_code = channels(self.board_type)[channel]
            except KeyError:
                raise AlazarException("Invalid channel: '{}'".format(channel))

            # impedance hard-coded to 50 ohm code
            ret_code = c_alazar_api.AlazarInputControl(self.board,
                                                       chan_code,
                                                       coupling_code,
                                                       range_code,
                                                       2)
            # check for API success
            _check_return_code(ret_code, "Error setting channel {} input:".format(channel))

            ret_code = c_alazar_api.AlazarSetBWLimit(self.board, chan_code, bw_code)
            _check_return_code(ret_code, "Error setting channel {} BW limit:".format(channel))

    def setup_one_trigger(self,
                          source_channel="ext",
                          slope="rising",
                          level=0.2,
                          ext_coupling="dc",
                          ext_range="5 V",
                          delay = 0):
        """Configure the Alazar trigger engine.

        The Alazar boards actually have two trigger engines which can be combined
        in interesting and complex ways, which we have never used even once.
        So, this function configures just one engine (J) and disables the other (K).
        This function defaults to configuring an external rising 5 V range trigger
            with a crossing at about 1 V.  This should be generally TTL-compatible.
        This function always disables trigger timeout to ensure the board does not self-
            trigger.
        This default is not compatible with the 9360; 9360 users must specify a range if
            using an external trigger.

        source_channel is a named channel 'A', 'B', or 'ext' to use the external input
        slope is "rising" or "falling"
        level is a float on the range -1 to 1 which determines the scaled input level
            at which the trigger engine fires.
        ext_couping is "ac" or "dc", defaults to "dc"
        ext_range should be a selection from the valid external trigger ranges
        delay is the number of samples between the trigger and the start of acquisition;
            The ATS9870 requires this to be a multiple of 16 for a 1-channel acquisition
            or a multiple of 8 for a 2-channel acquisition.
        """

        # validate source channel
        try:
            source_code = trigger_sources(self.board_type)[source_channel]
        except KeyError:
            raise AlazarException("Invalid trigger source channel: '{}'".format(source_channel))

        # validate slope
        if slope == "rising":
            slope_code = 1
        elif slope == "falling":
            slope_code = 2
        else:
            raise AlazarException("Slope must be 'rising' or 'falling'; provided: '{}'".format(slope))

        # validate level
        if level < -1.0 or level > 1.0:
            raise AlazarException("Level must be in the range [-1,1]; provided: {}".format(level))
        else:
            # set level code using the bit depth from the board
            level_code = int((level + 1.0)*127.5)

        # validate external coupling
        if ext_coupling == "ac":
            coupling_code = 1
        elif ext_coupling == "dc":
            coupling_code = 2
        else:
            raise AlazarException("External coupling must be 'ac' or 'dc'; provided: '{}'".format(ext_coupling))

        # validate external range
        try:
            range_code = ext_trig_range(self.board_type)[ext_range]
        except KeyError:
            raise AlazarException("Invalid external trigger range: '{}'".format(ext_range))

        # validate delay
        delay = int(delay)
        if delay < 0 or delay > 9999999:
            raise AlazarException("Delay must be >= 0 and <9,999,999; provided: '{}'".format(delay))
        elif delay % 8 != 0:
            raise AlazarException("Delay must be a multiple of 8; provided: '{}'".format(delay))

        ret_code = c_alazar_api.AlazarSetTriggerOperation(self.board,
                                                          0, # use trigger engine J
                                                          0, # configure engine J
                                                          source_code,
                                                          slope_code,
                                                          level_code,
                                                          1, # configure engine K,
                                                          0x3, # disable K
                                                          1, # set K slope positive
                                                          128) # set K level mid-range
        _check_return_code(ret_code, "Error setting trigger operation:")

        # configure external trigger if using
        if source_channel == "ext":

            ret_code = c_alazar_api.AlazarSetExternalTrigger(self.board, coupling_code, range_code)
            _check_return_code(ret_code, "Error setting external trigger:")

        # set trigger delay
        ret_code = c_alazar_api.AlazarSetTriggerDelay(self.board, delay)
        _check_return_code(ret_code, "Error setting trigger delay:")

        # disable trigger timeout
        ret_code = c_alazar_api.AlazarSetTriggerTimeOut(self.board, 0)
        _check_return_code(ret_code, "Error setting trigger timeout:")

    def acquire(self,
                samples_per_record,
                records_per_acquisition,
                records_per_buffer,
                channels_to_acquire="all",
                buffer_count=64,
                timeout = 5000):
        """Perform an acquisition using two-port NPT DMA mode.

        THIS FUNCTION IS FOR BOARD AND CODE DEBUGGING AND SHOULD NOT BE USED IN A
            REAL DATA ACQUISITION SITUATION.

        samples_per_record is the number of individual measurements in a measurement record;
            this has a minimum value of 256 and must be a multiple of 64.
        records_per_acquisition is the number of records to acquire
        records_per_buffer is the number of records in a single DMA buffer

        records_per_acquisition must be a multiple of records_per_buffer

        channels_to_acquire is "all" for all channels, or "A", "B" for a single channel.
        buffer_count is the number of DMA buffers to allocate; default is 64, min is 2.
        timeout (ms) is the time to wait for a buffer to be filled by the board; default is 5000
        """

        # validate inputs
        if records_per_acquisition < 1:
            raise AlazarException("Records per acquisition must be at least 1.")

        if records_per_buffer < 1:
            raise AlazarException("Records per buffer must be at least 1.")

        if records_per_acquisition % records_per_buffer != 0:
            raise AlazarException("Records per acquisition must be a multiple of records per buffer. Provided: {} records, {} records per buffer.".format(records_per_acquisition, records_per_buffer))

        # raises an exception if invalid number of samples
        _check_buffer_alignment(self.board_type, samples_per_record)

        # validate channels, raises an exception on invalid input
        channel_mask, channel_count = _make_channel_mask(self.board_type, channels_to_acquire)

        # check buffer count
        if buffer_count < 2:
            raise AlazarException("Buffer count must be at least two. Provided: {}".format(buffer_count))

        # all input has been validated

        cdef c_alazar_api.U8 bits_per_sample
        cdef c_alazar_api.U32 max_samples_per_channel

        # get channel info
        ret_code = c_alazar_api.AlazarGetChannelInfo(self.board, &max_samples_per_channel, &bits_per_sample,)
        _check_return_code(ret_code, "Get channel info failed:")

        bytes_per_sample = (bits_per_sample + 7) / 8
        bytes_per_record = bytes_per_sample * samples_per_record
        bytes_per_buffer = bytes_per_record * records_per_buffer * channel_count

        # set the record size
        ret_code = c_alazar_api.AlazarSetRecordSize(self.board, 0, samples_per_record)
        _check_return_code(ret_code, "Set record size failed for {} samples:".format(samples_per_record))

        # allocate list of NumPy arrays as data buffers
        # indexing this will cost a Python overhead, but this may not be important
        # these are refcounted so we don't need to manually manage their memory
        if bytes_per_sample <= 8:
            sample_type = np.uint8
        else:
            sample_type = np.uint16

        buffers = [np.empty(bytes_per_buffer, dtype=sample_type) for n in range(buffer_count)]

        # make a list of the address of each buffer to pass to the digitizer
        cdef list buffer_addresses = []

        # make a Cython memoryview of each buffer and add it to the list
        # get a C pointer to the buffer with the syntax &buf_vew[0]
        cdef unsigned char[:] buf_view
        for buf in buffers:
            buf_view = buf
            buffer_addresses.append(buf_view)

        # configure the board to make an NPT AutoDMA acquisition
        # first flag is the value of ADMA_EXTERNAL_STARTCAPTURE
        # second flag is the value of ADMA_NPT and sets no pretrigger sample acquisition
        if self.board_type == 13: #9870:
            autoDMA_flags = 0x00000001 | 0x00000200
        elif self.board_type == 25: #9360:
            autoDMA_flags = 0x00000001 | 0x00000200 | 0x00000800
            # third flag is ADMA_FIFO_ONLY_STREAMING
        else:
            raise AlazarException("Could not make autoDMA flag for board type {}".format(self.board_type))

        ret_code = c_alazar_api.AlazarBeforeAsyncRead(self.board,
                                                      channel_mask,
                                                      0,
                                                      samples_per_record,
                                                      records_per_buffer,
                                                      records_per_acquisition,
                                                      autoDMA_flags)
        _check_return_code(ret_code,"Setup NPT AutoDMA acquisition failed:")

        # have to preallocate all of the c variables
        cdef unsigned char[:] data_view
        cdef int buffers_per_acquisition
        cdef int buffers_completed
        cdef long long bytes_handled
        cdef int buffer_index

        # initialize a NumPy array to hold the data, temporary for this test function
        data = np.empty((bytes_per_record * records_per_acquisition * channel_count), dtype=sample_type)

        # get a pointer to the NumPy backing array
        data_view = data

        # ensure we abort the acquisition after this point
        # otherwise the digitizer will become stuck in DmaInProgress and require manual abort command
        # would be nice to use a contextmanager here but it gets weird with Cython cdefs
        try:

            # add the buffers to the list of buffers available to the board
            for b in range(buffer_count):
                buf_view = buffer_addresses[b]
                ret_code = c_alazar_api.AlazarPostAsyncBuffer(self.board, &buf_view[0], bytes_per_buffer)
                _check_return_code(ret_code, "Failed to send buffer address to board:")

            # arm the board
            ret_code = c_alazar_api.AlazarStartCapture(self.board)
            _check_return_code(ret_code, "Failed to start capture:")

            # process buffers; for now stuff into a NumPy array

            buffers_per_acquisition = records_per_acquisition / records_per_buffer

            buffers_completed = 0
            bytes_handled = 0

            # handle each buffer
            while buffers_completed < buffers_per_acquisition:
                buffer_index = buffers_completed % buffer_count

                buf_view = buffer_addresses[buffer_index]

                ret_code = c_alazar_api.AlazarWaitAsyncBufferComplete(self.board, &buf_view[0], timeout)

                _check_return_code(ret_code,"Wait for buffer complete failed on buffer {}:".format(buffers_completed))

                buffers_completed += 1

                # for now, copy the data into pre-allocated array
                data_view[bytes_handled:bytes_handled + bytes_per_buffer] = buf_view

                bytes_handled += bytes_per_buffer

                # hand the buffer back to the board
                ret_code = c_alazar_api.AlazarPostAsyncBuffer(self.board, &buf_view[0], bytes_per_buffer)
                _check_return_code(ret_code,"Failed to send buffer address back to board during acquisition:")

        finally:
            self._abort_acquisition()

        # we acquired all the buffers, return the data
        return data

    def _abort_acquisition(self):
        """Command the board to abort a running acquisition.

        The user should never need to call this manually, as any acquisition code should
        ensure that this is called regardless of what happens.
        This is left exposed as a method for debugging purposes if the board has gotten
        stuck in DmaInProgress."""
        ret_code = c_alazar_api.AlazarAbortAsyncRead(self.board)
        _check_return_code(ret_code,"Failed to abort acquisition:")


# end of Alazar() class definition

def get_systems_and_boards():
    """Return a dict of the number of boards in each Alazar system detected.

    Obnoxiously, Alazar indexes the systems and boards from 1 rather than 0."""
    n_sys = c_alazar_api.AlazarNumOfSystems()
    n_b = {}
    for s in range(n_sys):
        n_b[s+1] = c_alazar_api.AlazarBoardsInSystemBySystemID(s+1)

    return n_b


# --- Exception and error handling for Alazar boards
class AlazarException(Exception):
    pass

def _check_return_code(return_code, msg):
    """Check an Alazar return code for success.

    Raises an AlazarException if return_code is not 512, including the
    provided message and the text version of the Alazar error code.
    """
    if return_code != 512:
        raise AlazarException(msg + " " + _return_code_to_string(return_code))


def _return_code_to_string(return_code):
    """Convert a Alazar return code to a string.

    This function assumes a valid return code.
    """
    return <bytes> c_alazar_api.AlazarErrorToText(return_code)

# --- valid parameter settings by board type

def channels(board_type):
    """Get the dictionary of channel names.

    board_type can be the numerical ID or the string "ATS####"
    """
    if is_9870(board_type) or is_9360(board_type):
        return {"A":1,"B":2}
    else:
        AlazarException("Could not get channels for board type " + str(board_type))

def trigger_sources(board_type):
    """Get the dictionary of trigger sources.

    board_type can be the numerical ID or the string "ATS####"
    """
    if is_9870(board_type) or is_9360(board_type):
        return {"A":0x0,
                "B":0x1,
                "ext":0x2}
    else:
        AlazarException("Could not get trigger sources for board type " + str(board_type))

def clock_sources(board_type):
    """Get the dictionary of valid clock sources for this board type.

    board_type can be the numerical ID or the string "ATS####"
    At present, only the ATS9870 and ATS9360 are supported.
    """
    if (board_type == 13 or board_type == "ATS9870" or
        board_type == 25 or board_type == "ATS9360"):
        return {"internal":1,
                "external slow":4,
                "external fast":5,
                "external 10 MHz ref":7}
    else:
        raise AlazarException("Could not get clock sources for board type " + str(board_type))


def sample_rates(board_type):
    """Get the dictionary of valid sample rates for this board type.

    board_type can be the numerical ID or the string "ATS####"
    At present, only the ATS9870 and ATS9360 are supported.
    """
    if is_9870(board_type):
        return {"1 kS/s": 0x1,
                "2 kS/s": 0x2,
                "5 kS/s": 0x4,
                "10 kS/s": 0x8,
                "20 kS/s": 0xA,
                "50 kS/s": 0xC,
                "100 kS/s": 0xE,
                "200 kS/s": 0x10,
                "500 kS/s": 0x12,
                "1 MS/s": 0x14,
                "2 MS/s": 0x18,
                "5 MS/s": 0x1A,
                "10 MS/s": 0x1C,
                "20 MS/s": 0x1E,
                "50 MS/s": 0x22,
                "100 MS/s": 0x24,
                "250 MS/s": 0x2B,
                "500 MS/s": 0x30,
                "1 GS/s": 0x35,
                "user-defined": 0x40,
                "10 MHz ref": 1000000000}
    elif is_9360(board_type):
        return {"1 kS/s": 0x1,
                "2 kS/s": 0x2,
                "5 kS/s": 0x4,
                "10 kS/s": 0x8,
                "20 kS/s": 0xA,
                "50 kS/s": 0xC,
                "100 kS/s": 0xE,
                "200 kS/s": 0x10,
                "500 kS/s": 0x12,
                "1 MS/s": 0x14,
                "2 MS/s": 0x18,
                "5 MS/s": 0x1A,
                "10 MS/s": 0x1C,
                "20 MS/s": 0x1E,
                "50 MS/s": 0x22,
                "100 MS/s": 0x24,
                "200 MS/s": 0x28,
                "500 MS/s": 0x30,
                "800 MS/s": 0x32,
                "1 GS/s": 0x35,
                "1.2 GS/s": 0x37,
                "1.5 GS/s": 0x3A,
                "1.8 GS/s": 0x3D,
                "user-defined": 0x40}
    else:
        raise AlazarException("Could not get sample rates for board type " + str(board_type))


def ranges(board_type):
    """Get the dictionary of valid range names.

    board_type can be the numerical ID or the string "ATS####"
    At present, only the ATS9870 and ATS9360 are supported.
    """
    if is_9870(board_type):
        return {"40 mV": 0x2,
                "100 mV": 0x5,
                "200 mV": 0x6,
                "400 mV": 0x7,
                "1 V": 0xA,
                "2 V": 0xB}
    elif is_9360(board_type):
        return {"400 mV": 0x7}
    else:
        raise AlazarException("Could not get input ranges for board type " + str(board_type))

def input_couplings(board_type):
    """Get the dictionary of valid input coupings.

    board_type can be the numerical ID or the string "ATS####"
    At present, only the ATS9870 and ATS9360 are supported.
    """
    if is_9870(board_type):
        return {"ac": 1,
                "dc": 2}
    elif is_9360(board_type):
        return {"dc": 2}
    else:
        raise AlazarException("Could not get input couplings for board type " + str(board_type))

def ext_trig_range(board_type):
    """Get the dictionary of valid external trigger ranges.

    board_type can be the numerical ID or the string "ATS####"
    At present, only the ATS9870 and ATS9360 are supported.
    The SDK guide does specify which ranges are valid for which board.
    """
    if is_9870(board_type):
        return {"5 V": 0,}
    elif is_9360(board_type):
        return {"2.5 V": 0x3,
                "TTL": 0x2}
    else:
        raise AlazarException("Could not get trigger input ranges for board type " + str(board_type))

# --- parameter validation

max_decimation = 100000

def _check_decimation(board_type, decimation):
    """Check the decimation parameter given a board type.

    This function does not raise an exception.
    This function currently only supports the ATS9870.
    """

    if decimation >= max_decimation:
        return False

    if is_9870(board_type):
        if decimation in [1,2,4] or (decimation >= 0 and decimation % 10 == 0):
            # 10 MHz ref requires decimation of 1, 2, 4, or mult. of 10
            return True
        else:
            return False
    else:
        return False


#
def _check_buffer_alignment(board_type, n_samples):
    """Check the record length for minimum length and buffer alignment.

    This function currently only supports the ATS9870.
    """
    if is_9870(board_type):
        # ATS9870: min record size is 256, n_samples must be a multiple of 64.
        min_record_size = 256
        buffer_alignment = 64

    elif is_9360(board_type):
        # ATS9360: min record size is 256, n_samples must be a multiple of 128.
        min_record_size = 256
        buffer_alignment = 128
    else:
        raise AlazarException("Could not validate record length for board type {}.".format(board_type))

    if n_samples < min_record_size:
        raise AlazarException("Minimum record length is {}. Provided: {}".format(min_record_size,n_samples))
    elif n_samples % buffer_alignment != 0:
        raise AlazarException("Sample size must be a multiple of {}. Provided: {}".format(buffer_alignment, n_samples))


# build the channel mask
# channels interface will require refactoring to support boards with
# more than two channels.
def _make_channel_mask(board_type, channels):
    """Make the channel mask for a channel selection.

    This function currently only supports the ATS9870 and ATS9360.
    Support for boards with more than two channels will require
        refactoring the channel selection interface.

    Raises an AlazarException for invalid input or unsupported board type.

    Returns a tuple with the channel mask and channel count.
    """
    if is_9870(board_type) or is_9360(board_type):

        if channels == "all":
            return (3,2)
        else:
            try:
                channel_mask = channels(board_type)[channels]
            except KeyError:
                raise AlazarException("Invalid channel selection: '{}'".format(channels))
            return (channel_mask,1)

    else:
        raise AlazarException("Could not make channel mask for board type {}.".format(board_type))

# --- helper functions

def is_9870(board_type):
    return board_type == 13 or board_type == "ATS9870"

def is_9360(board_type):
    return board_type == 25 or board_type == "ATS9360"
