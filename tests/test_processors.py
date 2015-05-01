import alazar.processor as proc
#from alazar.alazar import AlazarException

from nose.tools import raises

class TestAverage(object):

    @raises(Exception)
    def test_abort(self):

        ave = proc.Average()
        e = Exception()

        ave.abort(e)
        ave.get_result()