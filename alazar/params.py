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
from collections import OrderedDict

# use OrderedDict so that _*_rates.keys() gives you a pretty list

# --- channels ---
channels = OrderedDict()
channels.update({"A": 1})
channels.update({"B": 2})

# --- trigger sources ---
trig_sources = OrderedDict()
trig_sources.update({"A": 0x0,})
trig_sources.update({"B": 0x1,})
trig_sources.update({"ext": 0x2})

# --- clock sources ---
clock_sources = OrderedDict()
clock_sources.update({"internal":1,})
clock_sources.update({"external slow":4,})
clock_sources.update({"external fast":5,})
clock_sources.update({"external 10 MHz ref":7})

# --- sample rates ---

sample_rates_9870 = OrderedDict()
sample_rates_9870.update({"1 kS/s": 0x1,})
sample_rates_9870.update({"2 kS/s": 0x2,})
sample_rates_9870.update({"5 kS/s": 0x4,})
sample_rates_9870.update({"10 kS/s": 0x8,})
sample_rates_9870.update({"20 kS/s": 0xA,})
sample_rates_9870.update({"50 kS/s": 0xC,})
sample_rates_9870.update({"100 kS/s": 0xE,})
sample_rates_9870.update({"200 kS/s": 0x10,})
sample_rates_9870.update({"500 kS/s": 0x12,})
sample_rates_9870.update({"1 MS/s": 0x14,})
sample_rates_9870.update({"2 MS/s": 0x18,})
sample_rates_9870.update({"5 MS/s": 0x1A,})
sample_rates_9870.update({"10 MS/s": 0x1C,})
sample_rates_9870.update({"20 MS/s": 0x1E,})
sample_rates_9870.update({"50 MS/s": 0x22,})
sample_rates_9870.update({"100 MS/s": 0x24,})
sample_rates_9870.update({"250 MS/s": 0x2B,})
sample_rates_9870.update({"500 MS/s": 0x30,})
sample_rates_9870.update({"1 GS/s": 0x35,})
sample_rates_9870.update({"user-defined": 0x40,})
sample_rates_9870.update({"10 MHz ref": 1000000000})

sample_rates_9360 = OrderedDict()
sample_rates_9360.update({"1 kS/s": 0x1,})
sample_rates_9360.update({"2 kS/s": 0x2,})
sample_rates_9360.update({"5 kS/s": 0x4,})
sample_rates_9360.update({"10 kS/s": 0x8,})
sample_rates_9360.update({"20 kS/s": 0xA,})
sample_rates_9360.update({"50 kS/s": 0xC,})
sample_rates_9360.update({"100 kS/s": 0xE,})
sample_rates_9360.update({"200 kS/s": 0x10,})
sample_rates_9360.update({"500 kS/s": 0x12,})
sample_rates_9360.update({"1 MS/s": 0x14,})
sample_rates_9360.update({"2 MS/s": 0x18,})
sample_rates_9360.update({"5 MS/s": 0x1A,})
sample_rates_9360.update({"10 MS/s": 0x1C,})
sample_rates_9360.update({"20 MS/s": 0x1E,})
sample_rates_9360.update({"50 MS/s": 0x22,})
sample_rates_9360.update({"100 MS/s": 0x24,})
sample_rates_9360.update({"200 MS/s": 0x28,})
sample_rates_9360.update({"500 MS/s": 0x30,})
sample_rates_9360.update({"800 MS/s": 0x32,})
sample_rates_9360.update({"1 GS/s": 0x35,})
sample_rates_9360.update({"1.2 GS/s": 0x37,})
sample_rates_9360.update({"1.5 GS/s": 0x3A,})
sample_rates_9360.update({"1.8 GS/s": 0x3D,})
sample_rates_9360.update({"user-defined": 0x40,})

# --- ranges ---

ranges_9870 = OrderedDict()
ranges_9870.update({"40 mV": 0x2,})
ranges_9870.update({"100 mV": 0x5,})
ranges_9870.update({"200 mV": 0x6,})
ranges_9870.update({"400 mV": 0x7,})
ranges_9870.update({"1 V": 0xA,})
ranges_9870.update({"2 V": 0xB})

ranges_9360 = {"400 mV": 0x7}

# --- input coupling ---

couplings_9870 = OrderedDict()
couplings_9870.update({"ac": 1,})
couplings_9870.update({"dc": 2,})

couplings_9360 = {"dc": 2,}

# --- trigger ranges ---

trig_ranges_9870 = {"5 V": 0}

trig_ranges_9360 = OrderedDict()
trig_ranges_9360.update({"2.5 V": 0x3,})
trig_ranges_9360.update({"TTL": 0x2})

# --- numeric board type keys ---

board_types = {13: 'ATS9870',
			   25: 'ATS9360',}