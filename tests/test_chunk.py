# class for holding tests with setup and teardown

from cbl_workflow.utils.chunk import chunk


class TestChunk:
    def setup_method(self):
        pass

    def teardown_method(self):
        pass

    def test_split_list(self):
        input_list = [1, 2, 3, 4, 5]
        chunk_size = 2
        expected_output = [[1, 2], [3, 4], [5]]
        assert chunk(input_list, chunk_size) == expected_output
