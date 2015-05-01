import processor as proc
from alazar import AlazarException

class TestAverage(object):

    @raises(AlazarException)
    def test_abort(self):

        ave = proc.Average()
        e = AlazarException()

        ave.abort(e)
        ave.get_result()