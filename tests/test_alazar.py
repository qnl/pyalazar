import alazar.alazar as alz

class TestAlazar(object):
	@classmethod
	def setup_class(cls):
		self.boards = alz.get_systems_and_boards()

	def test_systems_available(self):
		assert self.boards

	def test(self):
		pass