cdef extern from "AlazarCmd.h":
	"""Cython API for AlazarCmd.h"""
	pass

cdef extern from "AlazarError.h":
	"""Cython API for definitions in AlazarError.h"""

	# we never raise these and we use the default handling library, so
	# we don't need to fill the enum variants.
	enum _RETURN_CODE:
		pass

	ctypedef _RETURN_CODE ReturnCode
	"""Acquisition card return codes."""


cdef extern from "AlazarApi.h":
	"""Cython API for Alazar C API."""

	# typedefs

	ctypedef unsigned long U32
	"""Keep the Alazar conventions for integert type shorthand."""

	ctypedef void* Handle
	"""Raw pointer to an Alazar board."""

	# handle and system management

	U32 AlazarNumOfSystems()
	"""Get the number of board systems detected."""

	U32 AlazarBoardsInSystemBySystemID(U32 system_id)
	"""Get the number of boards in a board system."""

	Handle AlazarGetBoardBySystemID(U32 system_id, U32 board_number)
	"""Get a handle to an Alazar board by board system id and board number."""

	ReturnCode AlazarSetLED(Handle h, U32 state)
	"""Set the LED on a board; off = 0, on = 1."""
	