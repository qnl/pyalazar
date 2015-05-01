import alazar.processor as proc

from alazar.processor import ProcessorException

from nose.tools import raises

class TestAverage(object):

    @raises(ProcessorException)
    def test_abort(self):

        ave = proc.Average()
        e = Exception()

        ave.abort(e)
        ave.get_result()