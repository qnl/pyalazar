cimport c_alazar_api

from time import sleep

print "Searching for boards."
n_s = c_alazar_api.AlazarNumOfSystems()
n_b = c_alazar_api.AlazarBoardsInSystemBySystemID(1)
print "Found " + str(n_s) + " board system(s); system 1 has " + str(n_b) + " board(s)."

cdef c_alazar_api.HANDLE board = c_alazar_api.AlazarGetBoardBySystemID(1,1)

if board is not NULL:
	kind = c_alazar_api.AlazarGetBoardKind(board)
	print str(kind)