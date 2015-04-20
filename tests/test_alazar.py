import alazar.alazar as alz

class TestAlazar(object):

	@classmethod
	def setup_class(cls):
		sys_list = alz.get_systems_and_boards()
		cls.boards = []

		sys = 1
		for n_boards in sys_list:
			for board in range(n_boards):
				cls.boards.append(alz.Alazar(sys,board+1))
			sys += 1


	# make sure we have some boards to test, or everything will fail anyway
	def test_systems_available(self):
		assert self.boards

	# test the decimation parameter check for 10 MHz clock
	def test_decimation_10MHz(self):
		for board in self.boards:
			for dec in range(-1,11):
				yield self.check_decimation_10MHz, board.get_board_type(), dec,
		
	def check_decimation_10MHz(self,board_type,dec):

		dec_check = alz.check_decimation(board_type, "external 10 MHz ref", dec)

		if dec in [1,2,4] or (dec > 0 and dec % 10 == 0):
			assert dec_check
		else:
			assert not dec_check