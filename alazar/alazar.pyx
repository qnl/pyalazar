cimport c_alazar_api

# C wrapper class to represent an Alazar digitizer
cdef class Alazar(object):

	# handle to an alazar board
	cdef c_alazar_api.HANDLE board

	# use __cinit__ to make sure this is run
	def __cinit__(self, systemID, boardID):
		self.board = c_alazar_api.AlazarGetBoardBySystemID(systemID,boardID)
		if self.board is NULL:
			raise AlazarException("Could not connect to an Alazar board with system ID " + str(systemID) + ", board ID " + str(boardID))

	def set_capture_clock(self, clock_source, sample_rate, decimation, edge):
		c_alazar_api.AlazarSetCaptureClock(self.board, clock_source, sample_rate, edge, decimation)
		# c_alazar_api.AlazarSetCaptureClock(self.board, 1, 1, 1, 1)

def get_systems_and_boards():
	"""Return a list of the number of boards in each Alazar system detected.
	Obnoxiously, Alazar indexes the systems and boards from 0 rather than 1."""
	n_sys = c_alazar_api.AlazarNumOfSystems()
	n_b = []
	for s in range(n_sys):
		n_b.append(c_alazar_api.AlazarBoardsInSystemBySystemID(s+1))

	return n_b


# --- Exception class for Alazar boards
class AlazarException(Exception):
	pass

def clock_sources():
	return {"internal":1,
			"slow external":4,
			"external AC":5,
			"external 10MHz ref":7}

def sample_rates():
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