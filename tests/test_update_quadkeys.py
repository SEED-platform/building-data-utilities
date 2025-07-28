# !/usr/bin/env python
"""
Tests for quadkey update utilities
Simple tests for downloading and managing quadkey data
"""

import shutil
import tempfile
from pathlib import Path
from unittest.mock import Mock, mock_open, patch

import pandas as pd

from building_data_utilities.utils.update_quadkeys import update_quadkeys


class TestUpdateQuadkeys:
    """Simple tests for quadkey update functionality"""

    def setup_method(self):
        """Create temporary directory for tests"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.save_dir = self.temp_dir / "quadkeys"

    def teardown_method(self):
        """Clean up temporary files"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def create_mock_dataset_links(self):
        """Create a mock dataset-links.csv file"""
        self.save_dir.mkdir(parents=True, exist_ok=True)
        dataset_data = pd.DataFrame(
            {
                "QuadKey": [123, 456, 789],
                "Url": [
                    "https://example.com/123.geojsonl.gz",
                    "https://example.com/456.geojsonl.gz",
                    "https://example.com/789.geojsonl.gz",
                ],
            }
        )
        dataset_data.to_csv(self.save_dir / "dataset-links.csv", index=False)

    @patch("building_data_utilities.utils.update_quadkeys.requests")
    @patch("pandas.read_csv")
    @patch("builtins.open", new_callable=mock_open)
    def test_update_quadkeys_basic_download(self, mock_file, mock_read_csv, mock_requests):
        """Test basic quadkey download functionality"""
        # Mock the dataset CSV
        mock_df = pd.DataFrame(
            {"QuadKey": [123, 456], "Url": ["https://example.com/123.geojsonl.gz", "https://example.com/456.geojsonl.gz"]}
        )
        mock_read_csv.return_value = mock_df

        # Mock HTTP responses
        mock_head_response = Mock()
        mock_head_response.headers = {"Content-Length": "1000"}
        mock_requests.head.return_value = mock_head_response

        mock_get_response = Mock()
        mock_get_response.content = b"fake geojsonl data"
        mock_requests.get.return_value = mock_get_response

        # Mock file doesn't exist (so it will download)
        with patch("pathlib.Path.exists", return_value=False):
            update_quadkeys([123], save_directory=self.save_dir)

        # Verify dataset CSV was read
        mock_read_csv.assert_called_once()

        # Verify requests were made - when file doesn't exist,
        # only get() is called (no head() call needed)
        mock_requests.head.assert_not_called()  # No head when file missing
        mock_requests.get.assert_called_once_with("https://example.com/123.geojsonl.gz")

        # Verify file was written
        mock_file.assert_called()

    @patch("building_data_utilities.utils.update_quadkeys.requests")
    @patch("pandas.read_csv")
    def test_update_quadkeys_skip_existing_file(self, mock_read_csv, mock_requests):
        """Test that existing files with correct size are skipped"""
        # Mock the dataset CSV
        mock_df = pd.DataFrame({"QuadKey": [123], "Url": ["https://example.com/123.geojsonl.gz"]})
        mock_read_csv.return_value = mock_df

        # Create a mock existing file
        self.save_dir.mkdir(parents=True, exist_ok=True)
        test_file = self.save_dir / "123.geojsonl.gz"
        test_file.write_bytes(b"x" * 1000)  # 1000 bytes

        # Mock HTTP head response with same size
        mock_head_response = Mock()
        mock_head_response.headers = {"Content-Length": "1000"}
        mock_requests.head.return_value = mock_head_response

        update_quadkeys([123], save_directory=self.save_dir)

        # Should have checked head but not downloaded
        mock_requests.head.assert_called_once()
        mock_requests.get.assert_not_called()

    @patch("building_data_utilities.utils.update_quadkeys.requests")
    @patch("pandas.read_csv")
    @patch("builtins.open", new_callable=mock_open)
    def test_update_quadkeys_redownload_different_size(self, mock_file, mock_read_csv, mock_requests):
        """Test that files with different sizes are re-downloaded"""
        # Mock the dataset CSV
        mock_df = pd.DataFrame({"QuadKey": [123], "Url": ["https://example.com/123.geojsonl.gz"]})
        mock_read_csv.return_value = mock_df

        # Mock existing file with different size
        mock_stat = Mock()
        mock_stat.st_size = 500  # Local file is 500 bytes
        with patch("pathlib.Path.exists", return_value=True), patch("pathlib.Path.stat", return_value=mock_stat):
            # Mock HTTP responses
            mock_head_response = Mock()
            # Remote is 1000 bytes
            mock_head_response.headers = {"Content-Length": "1000"}
            mock_requests.head.return_value = mock_head_response

            mock_get_response = Mock()
            mock_get_response.content = b"updated data"
            mock_requests.get.return_value = mock_get_response

            update_quadkeys([123], save_directory=self.save_dir)

        # Should have downloaded the updated file
        mock_requests.get.assert_called_once()

    @patch("pandas.read_csv")
    def test_update_quadkeys_missing_quadkey_error(self, mock_read_csv):
        """Test error handling for missing quadkey"""
        # Mock dataset without the requested quadkey
        mock_df = pd.DataFrame(
            {"QuadKey": [456, 789], "Url": ["https://example.com/456.geojsonl.gz", "https://example.com/789.geojsonl.gz"]}
        )
        mock_read_csv.return_value = mock_df

        import pytest

        with pytest.raises(ValueError, match="QuadKey not found in dataset: 123"):
            update_quadkeys([123], save_directory=self.save_dir)

    @patch("building_data_utilities.utils.update_quadkeys.requests")
    @patch("pandas.read_csv")
    def test_update_quadkeys_multiple_urls_uses_latest(self, mock_read_csv, mock_requests):
        """Test that when multiple URLs exist, the latest is used"""
        # Mock dataset with duplicate quadkeys (different URLs)
        mock_df = pd.DataFrame(
            {
                "QuadKey": [123, 123, 456],
                "Url": [
                    "https://example.com/old/123.geojsonl.gz",
                    # This should be used (latest)
                    "https://example.com/new/123.geojsonl.gz",
                    "https://example.com/456.geojsonl.gz",
                ],
            }
        )
        mock_read_csv.return_value = mock_df

        # Mock responses
        mock_head_response = Mock()
        mock_head_response.headers = {"Content-Length": "1000"}
        mock_requests.head.return_value = mock_head_response

        mock_get_response = Mock()
        mock_get_response.content = b"new data"
        mock_requests.get.return_value = mock_get_response

        with patch("pathlib.Path.exists", return_value=False), patch("builtins.open", mock_open()):
            update_quadkeys([123], save_directory=self.save_dir)

        # Verify dataset CSV was read
        mock_read_csv.assert_called_once()

        # Should use the new URL (last one in the dataframe)
        # When file doesn't exist, only get() is called
        mock_requests.head.assert_not_called()
        mock_requests.get.assert_called_with("https://example.com/new/123.geojsonl.gz")

    @patch("building_data_utilities.utils.update_quadkeys.requests")
    @patch("pandas.read_csv")
    @patch("builtins.open", new_callable=mock_open)
    def test_update_quadkeys_multiple_quadkeys(self, mock_file, mock_read_csv, mock_requests):
        """Test downloading multiple quadkeys"""
        # Mock dataset
        mock_df = pd.DataFrame(
            {
                "QuadKey": [123, 456, 789],
                "Url": [
                    "https://example.com/123.geojsonl.gz",
                    "https://example.com/456.geojsonl.gz",
                    "https://example.com/789.geojsonl.gz",
                ],
            }
        )
        mock_read_csv.return_value = mock_df

        # Mock responses
        mock_head_response = Mock()
        mock_head_response.headers = {"Content-Length": "1000"}
        mock_requests.head.return_value = mock_head_response

        mock_get_response = Mock()
        mock_get_response.content = b"data"
        mock_requests.get.return_value = mock_get_response

        with patch("pathlib.Path.exists", return_value=False):
            update_quadkeys([123, 789], save_directory=self.save_dir)

        # Verify dataset CSV was read
        mock_read_csv.assert_called_once()

        # Should have made requests for both quadkeys
        # When files don't exist, only get() calls are made
        mock_requests.head.assert_not_called()
        assert mock_requests.get.call_count == 2

        # Check the URLs called
        get_calls = [call[0][0] for call in mock_requests.get.call_args_list]
        assert "https://example.com/123.geojsonl.gz" in get_calls
        assert "https://example.com/789.geojsonl.gz" in get_calls

    def test_update_quadkeys_creates_directory(self):
        """Test that the save directory is created if it doesn't exist"""
        non_existent_dir = self.temp_dir / "new_dir" / "quadkeys"
        assert not non_existent_dir.exists()

        # This should create the directory structure
        with patch("pandas.read_csv") as mock_read_csv:
            mock_df = pd.DataFrame({"QuadKey": [], "Url": []})
            mock_read_csv.return_value = mock_df

            update_quadkeys([], save_directory=non_existent_dir)

        # Directory should now exist
        assert non_existent_dir.exists()
        assert non_existent_dir.is_dir()

    @patch("pandas.read_csv")
    def test_update_quadkeys_empty_list(self, mock_read_csv):
        """Test that empty quadkey list is handled gracefully"""
        mock_df = pd.DataFrame({"QuadKey": [], "Url": []})
        mock_read_csv.return_value = mock_df

        # Should not raise an error
        update_quadkeys([], save_directory=self.save_dir)

        # Directory should be created but no downloads attempted
        assert self.save_dir.exists()
