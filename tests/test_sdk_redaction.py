import unittest

from deepgram.core import ApiError


class SdkRedactionTest(unittest.TestCase):
    def test_api_error_redacts_authorization_value(self):
        marker = "synthetic-api-key"
        error = ApiError(headers={"Authorization": f"Token {marker}"})

        self.assertNotIn(marker, str(error))
