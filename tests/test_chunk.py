"""
SEED Platform (TM), Copyright (c) Alliance for Sustainable Energy, LLC, and other contributors.
See also https://github.com/SEED-platform/cbl-workflow/blob/main/LICENSE.md
"""

# class for holding tests with setup and teardown

from building_data_utilities.chunk import chunk


class TestChunk:
    def test_split_list(self):
        input_list = [1, 2, 3, 4, 5]
        chunk_size = 2
        expected_output = [[1, 2], [3, 4], [5]]
        assert chunk(input_list, chunk_size) == expected_output
