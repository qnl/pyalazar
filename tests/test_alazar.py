import alazar.alazar as alz

# nose module setup
def setup():
	boards = alz.get_systems_and_boards()

class TestAlazar(object):

	def test_systems_available():
		assert boards

	def test():
		pass