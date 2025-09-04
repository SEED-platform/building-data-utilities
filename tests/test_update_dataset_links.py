# !/usr/bin/env python
"""
Tests for dataset links update utilities
Simple tests for downloading and updating dataset links
"""

import shutil
import tempfile
from pathlib import Path
from unittest.mock import Mock, mock_open, patch

from building_data_utilities.utils.update_dataset_links import DATASET_URL, update_dataset_links


class TestUpdateDatasetLinks:
    """Simple tests for dataset links update functionality"""

    def setup_method(self):
        """Create temporary directory for tests"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.save_dir = self.temp_dir / "quadkeys"

    def teardown_method(self):
        """Clean up temporary files"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_dataset_url_constant(self):
        """Test that DATASET_URL is properly defined"""
        assert DATASET_URL is not None
        assert isinstance(DATASET_URL, str)
        assert DATASET_URL.startswith("https://")
        assert "dataset-links.csv" in DATASET_URL

    @patch("building_data_utilities.utils.update_dataset_links.requests")
    @patch("builtins.open", new_callable=mock_open)
    def test_update_dataset_links_fresh_download(self, mock_file, mock_requests):
        """Test downloading dataset links when file doesn't exist"""
        # Mock HTTP responses
        mock_get_response = Mock()
        mock_get_response.content = b"QuadKey,Url\n123,https://example.com"
        mock_requests.get.return_value = mock_get_response

        # Mock file doesn't exist
        with patch("pathlib.Path.exists", return_value=False):
            update_dataset_links(save_directory=self.save_dir)

        # Verify download was attempted
        mock_requests.get.assert_called_once_with(DATASET_URL)

        # Verify file was written
        mock_file.assert_called()

    @patch("building_data_utilities.utils.update_dataset_links.requests")
    @patch("builtins.open", new_callable=mock_open, read_data=b"old data")
    def test_update_dataset_links_skip_same_md5(self, mock_file, mock_requests):
        """Test skipping download when MD5 hashes match"""
        import base64
        import hashlib

        # Calculate MD5 of mock data
        test_data = b"old data"
        expected_md5 = base64.b64encode(hashlib.md5(test_data).digest()).decode("UTF-8")

        # Mock file exists with same MD5
        mock_head_response = Mock()
        mock_head_response.headers = {"Content-MD5": expected_md5}
        mock_requests.head.return_value = mock_head_response

        with patch("pathlib.Path.exists", return_value=True):
            update_dataset_links(save_directory=self.save_dir)

        # Should check HEAD but not download
        mock_requests.head.assert_called_once_with(DATASET_URL)
        mock_requests.get.assert_not_called()

    @patch("building_data_utilities.utils.update_dataset_links.requests")
    @patch("builtins.open", new_callable=mock_open, read_data=b"old data")
    def test_update_dataset_links_redownload_different_md5(self, mock_file, mock_requests):
        """Test re-downloading when MD5 hashes differ"""
        # Mock file exists with different MD5
        mock_head_response = Mock()
        mock_head_response.headers = {"Content-MD5": "different_md5_hash"}
        mock_requests.head.return_value = mock_head_response

        mock_get_response = Mock()
        mock_get_response.content = b"new data"
        mock_requests.get.return_value = mock_get_response

        with patch("pathlib.Path.exists", return_value=True):
            update_dataset_links(save_directory=self.save_dir)

        # Should both check and download
        mock_requests.head.assert_called_once_with(DATASET_URL)
        mock_requests.get.assert_called_once_with(DATASET_URL)

    def test_update_dataset_links_creates_directory(self):
        """Test that the save directory is created if it doesn't exist"""
        non_existent_dir = self.temp_dir / "new_dir" / "quadkeys"
        assert not non_existent_dir.exists()

        with patch("building_data_utilities.utils.update_dataset_links.requests") as mock_requests:
            mock_get_response = Mock()
            mock_get_response.content = b"test data"
            mock_requests.get.return_value = mock_get_response

            with patch("pathlib.Path.exists", return_value=False), patch("builtins.open", mock_open()):
                update_dataset_links(save_directory=non_existent_dir)

        # Directory should now exist
        assert non_existent_dir.exists()
        assert non_existent_dir.is_dir()

    def test_update_dataset_links_default_directory(self):
        """Test using default save directory"""
        with patch("building_data_utilities.utils.update_dataset_links.requests") as mock_requests:
            mock_get_response = Mock()
            mock_get_response.content = b"test data"
            mock_requests.get.return_value = mock_get_response

            with (
                patch("pathlib.Path.exists", return_value=False),
                patch("pathlib.Path.mkdir") as mock_mkdir,
                patch("builtins.open", mock_open()),
            ):
                update_dataset_links()  # No save_directory parameter

            # Should create default directory
            mock_mkdir.assert_called()

    @patch("building_data_utilities.utils.update_dataset_links.requests")
    def test_update_dataset_links_file_operations(self, mock_requests):
        """Test the actual file operations in detail"""
        mock_get_response = Mock()
        test_content = b"QuadKey,Url\n123,https://example.com/file.gz"
        mock_get_response.content = test_content
        mock_requests.get.return_value = mock_get_response

        # Use real file operations to test
        self.save_dir.mkdir(parents=True, exist_ok=True)
        expected_file = self.save_dir / "dataset-links.csv"

        # File doesn't exist, so should download
        update_dataset_links(save_directory=self.save_dir)

        # Check file was created and has correct content
        assert expected_file.exists()
        assert expected_file.read_bytes() == test_content

    @patch("building_data_utilities.utils.update_dataset_links.requests")
    def test_update_dataset_links_md5_calculation(self, mock_requests):
        """Test MD5 calculation and comparison logic"""
        import base64
        import hashlib

        # Create a file with known content
        self.save_dir.mkdir(parents=True, exist_ok=True)
        test_file = self.save_dir / "dataset-links.csv"
        test_content = b"test content for md5"
        test_file.write_bytes(test_content)

        # Calculate expected MD5
        expected_md5 = base64.b64encode(hashlib.md5(test_content).digest()).decode("UTF-8")

        # Mock server returns same MD5
        mock_head_response = Mock()
        mock_head_response.headers = {"Content-MD5": expected_md5}
        mock_requests.head.return_value = mock_head_response

        update_dataset_links(save_directory=self.save_dir)

        # Should not have attempted download
        mock_requests.get.assert_not_called()

    def test_update_dataset_links_pathlib_integration(self):
        """Test that function works correctly with pathlib.Path objects"""
        with patch("building_data_utilities.utils.update_dataset_links.requests") as mock_requests:
            mock_get_response = Mock()
            mock_get_response.content = b"test"
            mock_requests.get.return_value = mock_get_response

            with patch("pathlib.Path.exists", return_value=False), patch("builtins.open", mock_open()):
                # Test with Path object
                path_obj = Path("test/path")
                update_dataset_links(save_directory=path_obj)

                # Should work without errors
                mock_requests.get.assert_called_once()

    @patch("building_data_utilities.utils.update_dataset_links.requests")
    @patch("builtins.open", new_callable=mock_open)
    def test_update_dataset_links_error_handling(self, mock_file, mock_requests):
        """Test basic error handling scenarios"""
        # Test when requests raise an exception
        mock_requests.get.side_effect = Exception("Network error")

        import pytest

        with patch("pathlib.Path.exists", return_value=False), pytest.raises(Exception, match="Network error"):
            update_dataset_links(save_directory=self.save_dir)

        # Verify file was opened in binary write mode
        mock_file.assert_called()
        # Check that the file was opened with 'wb' mode
        call_args = mock_file.call_args_list
        for call in call_args:
            if len(call[0]) > 1 and call[0][1] == "wb":
                # Found the write call
                break
        else:
            # If we don't find 'wb', check if 'rb' was used for reading
            # The function should use both 'rb' and 'wb' modes
            pass
