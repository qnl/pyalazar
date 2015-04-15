cimport c_alazar_api

# C wrapper class to represent an Alazar digitizer
cdef class Alazar(object):

	# handle to an alazar board
	cdef c_alazar_api.HANDLE board

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
		
		self.board_type = c_alazar_api.AlazarGetBoardKind()
		if self.board_type == 0:
			raise AlazarException("Connected to board with system ID {}, board ID {}, but could not identify board!".format(systemID,boardID))


	def setup_capture_clock(self, clock_source, sample_rate, decimation=0, edge="rising"):
		"""Set the capture clock for this alazar board.

		clock_source is the name of a valid clock source for this board
		sample_rate is the name of a valid sample rate for this board
		if clock_source is not "internal", sample_rate is ignored
		if clock source is not "internal", decimation determines the sample clock as
			external clock period / decimation.  decimation = 0 disables clock decimation
			decimation may be any integer between 0 and 100000.
		for clock_source = "external 10 MHz ref", decimation determines the sample clock
			as 1 GHz / decimation, with decimination equal to 1, 2, 4, or a multiple of 10.
		edge = "rising" or "falling" determines whether the alazar sample clock
		triggers on the rising or falling edge of the reference clock

		Raises an AlazarException for invalid parameters, or if the set clock call fails.

		The logic of this function is presently hardwired for the ATS9870.
		Extending to other models will require modifying this function.
		"""
		if edge == "rising":
			edge_code = 0
		elif edge == "falling":
			edge_code = 1
		else:
			raise AlazarException("Edge must be either 'rising' or 'falling'; supplied: '{}'".format(edge))



		# get the clock source ID
		try:
			source_code = clock_sources(self.board_type)[clock_source]
		except KeyError:
			raise AlazarException("Clock source '{}' is not valid.".format(clock_source))


		if clock_source == "internal":
			# get the sample rate ID
			try:
				rate_code = sample_rates(self.board_type)[sample_rate]
			except KeyError:
				raise AlazarException("Sample rate '{}' is not valid.".format(sample_rate))

			if sample_rate == "User-defined" or sample_rate = "10 MHz ref":
				raise AlazarException("Internal clock requires an explicit sample rate; supplied: '{}'".format(sample_rate))

			code = c_alazar_api.AlazarSetCaptureClock(self.board, source_code, rate_code, edge_code, 0)

		else:
			if check_decimation(self.board_type, clock_source, decimation):
				if clock_source == "external 10 MHz ref":
					rate_code = sample_rates(self.board_type)["10 MHz ref"]
				else:
					rate_code = sample_rates(self.board_type)["User-defined"]
				ret_code = c_alazar_api.AlazarSetCaptureClock(self.board, source_code, rate_code, edge_code, decimation)
			else:
				raise AlazarException("Invalid decimation '{}' for clock source '{}'.".format(decimation,clock_source))
		
		# raise exception if ret_code was an error
		check_return_code(ret_code, "Set capture clock failed:")


	def setup_input_channels(self, channel="all", coupling="dc", input_range, impedance="50ohm", bw="open"):
		"""Set the input parameters for a digitizer channel.

		If channel = "all", all available channels are set to the given parameters.
		Otherwise, channel should be 'A', 'B', 'C', etc.  Defaults to "all".
		couling is either "ac" or "dc", defaults to "dc"
		range is a valid range string
		impedance is optional as the ATS9870 is not switchable
		bw is either "open" or "limit" to engage 20 MHz filter, default is "open"
		"""

		# validate coupling
		if coupling == "ac":
			coupling_code = 1
		elif coupling == "dc":
			coupling_code = 2
		else:
			raise AlazarException("Input coupling must be 'ac' or 'dc'; provided: '{}'".format(coupling))

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
				check_return_code(ret_code, "Error setting channel {} input:".format(chan))

				ret_code = c_alazar_api.AlazarSetBWLimit(self.board, chan_code, bw_code)
				check_return_code(ret_code, "Error setting channel {} BW limit:".format(chan))
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
			check_return_code(ret_code, "Error setting channel {} input:".format(chan))

			ret_code = c_alazar_api.AlazarSetBWLimit(self.board, chan_code, bw_code)
			check_return_code(ret_code, "Error setting channel {} BW limit:".format(chan))

	def setup_one_trigger(self,
						  source_channel="ext",
						  slope="rising",
						  level=0.0,
						  ext_coupling="dc",
						  ext_range="TTL",
						  delay = 0):
		"""Configure the Alazar trigger engine.

		The Alazar boards actually have two trigger engines which can be combined
		in interesting and complex ways, which we have never used even once.
		So, this function configures just one engine (J) and disables the other (K).
		This function defaults to configuring an external rising TTL half-scale trigger.
		This function always disables trigger timeout to ensure the board does not self-
			trigger.

		channel is a named channel 'A', 'B', or 'ext' to use the external input
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
			source_code = trigger_sources()[source_channel]
		except KeyError:
			raise AlazarException("Invalid trigger source channel: '{}'".format(source_channel))

		# validate slope
		if slope = "rising":
			slope_code = 1
		elif slope = "falling":
			slope_code = 2
		else:
			raise AlazarException("Slope must be 'rising' or 'falling'; provided: '{}'".format(slope))

		# validate level
		if level < -1.0 or level > 1.0:
			raise AlazarException("Level must be in the range [-1,1]; provided: {}".format(level))
		else:
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
			range_code = ext_trig_range()[ext_range]
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
		check_return_code(ret_code, "Error setting trigger operation:")

		# configure external trigger if using
		if source_channel == "ext":

			ret_code = c_alazar_api.AlazarSetExternalTrigger(self.board, coupling_code, range_code)
			check_return_code(ret_code, "Error setting external trigger:")

		# set trigger delay
		ret_code = c_alazar_api.AlazarSetTriggerDelay(self.board, delay)
		check_return_code(ret_code, "Error setting trigger delay:")

		# disable trigger timeout
		ret_code = c_alazar_api.AlazarSetTriggerTimeOut(self.board, 0)
		check_return_code(ret_code, "Error setting trigger timeout:")


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

def check_return_code(return_code, msg):
	"""Check an Alazar return code for success.

	Raises an AlazarException if return_code is not 512, including the
	provided message and the text version of the Alazar error code.
	"""
	if return_code != 512:
		raise AlazarException(msg + " " + return_code_to_string(return_code))


def return_code_to_string(return_code):
	"""Convert a Alazar return code to a string.

	This function assumes a valid return code.
	"""
	return <bytes> c_alazar_api.AlazarErrorToText(return_code)

# --- valid parameter settings by board type

def channels(board_type):
	"""Get the dictionary of channel names.

	board_type can be the numerical ID or the string "ATS####"
	Only supports ATS9870.
	"""
	if board_type == 13 or board_type == "ATS9870":
		return {"A":1,"B":2}
	else:
		AlazarException("Could not get channels for board type " + str(board_type))

def trigger_sources(board_type):
	"""Get the dictionary of trigger sources.

	board_type can be the numerical ID or the string "ATS####"
	Only supports ATS9870.
	"""
	if board_type == 13 or board_type == "ATS9870":
		return {"A":0x0,
				"B":0x1,
				"ext":0x2}
	else:
		AlazarException("Could not get trigger sources for board type " + str(board_type))

def clock_sources(board_type):
	"""Get the dictionary of valid clock sources for this board type.

	board_type can be the numerical ID or the string "ATS####"
	At present, only the ATS9870 is supported.
	"""
	if board_type == 13 or board_type == "ATS9870":
		return {"internal":1,
				"external slow":4,
				"external fast":5,
				"external 10 MHz ref":7}
	else:
		raise AlazarException("Could not get clock sources for board type " + str(board_type))


def sample_rates(board_type):
	"""Get the dictionary of valid sample rates for this board type.

	board_type can be the numerical ID or the string "ATS####"
	At present, only the ATS9870 is supported.
	"""
	if board_type == 13 or board_type == "ATS9870":
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
				"User-defined": 0x40,
				"10 MHz ref": 1000000000}
	else:
		raise AlazarException("Could not get sample rates for board type " + str(board_type))


def ranges(board_type):
	"""Get the dictionary of valid range names.

	board_type can be the numerical ID or the string "ATS####"
	At present, only the ATS9870 is supported.
	"""
	if board_type == 13 or board_type == "ATS9870":
		return {"40 mV": 0x2,
				"100 mV": 0x5,
				"200 mV": 0x6,
				"400 mV": 0x7,
				"1 V": 0xA,
				"2 V": 0xB}
	else:
		raise AlazarException("Could not get input ranges for board type " + str(board_type))

def ext_trig_range():
	"""Get the dictionary of valid external trigger ranges."""
	return {"1 V": 1,
			"2.5 V": 3,
			"5 V": 0,
			"TTL": 2}

# --- parameter validation

max_decimation = 100000

def check_decimation(board_type, clock_source, decimation):
	"""Check the decimation parameter given a board type and clock source.

	This function assumes the clock source and board type are valid,
	otherwise an exception may occur.
	This function currently only supports the ATS9870
	"""

	if board_type == 13 or board_type == "ATS9870":
		if clock_source == "external 10 MHz ref":
			# 10 MHz ref requires decimation of 1, 2, 4, or mult. of 10
			if decimation in [1,2,4] or (decimation != 0 and decimation and 10 == 0) and decimation <= max_decimation:
				return True
			else:
				return False

		elif clock_soure == "external slow" or clock_source == "external fast":
			if decimation >= 0 and decimation <= max_decimation:
				return True
			else:
				return False

	else:
		raise ( AlazarException("Could not check decimation for board type '"
			   + str(board_type) + "' for clock source '" + str(clock_source) +"'") )