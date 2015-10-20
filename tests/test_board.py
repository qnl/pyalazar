# Copyright (C) 2015  Chris Macklin
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
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
