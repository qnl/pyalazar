from alazar import processor

from board import (Alazar, get_systems_and_boards, AlazarException,
                          channels, trigger_sources, clock_sources,
                          sample_rates, ranges, input_couplings,
                          ext_trig_range,)

from board_mock import MockAlazar, MockAlazarException