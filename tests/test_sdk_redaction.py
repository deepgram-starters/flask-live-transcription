import unittest

from deepgram.core import ApiError
import app as starter


class SdkRedactionTest(unittest.TestCase):
    def test_api_error_redacts_authorization_value(self):
        marker = "synthetic-api-key"
        error = ApiError(headers={"Authorization": f"Token {marker}"})

        self.assertNotIn(marker, str(error))

    def test_invalid_websocket_numeric_parameters_are_rejected(self):
        with self.assertRaises(ValueError):
            starter.parse_stream_numeric_parameters({'sample_rate': 'abc'})
