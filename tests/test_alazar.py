import alazar.board as alz

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
