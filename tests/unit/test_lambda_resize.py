import unittest
from unittest.mock import MagicMock, patch
from lambda_code.resize_function import handler, is_valid_image, create_s3_client
from botocore.exceptions import ClientError
from botocore.config import Config
from PIL import Image
import io

class TestLambdaFunction(unittest.TestCase):

    def test_is_valid_image(self):
        self.assertTrue(is_valid_image("test.jpg"))
        self.assertTrue(is_valid_image("test.png"))
        self.assertFalse(is_valid_image("test.txt"))

    @patch('lambda_code.resize_function.boto3')
    def test_create_s3_client(self, mock_boto3):
        config = Config(retries=dict(max_attempts=2))
        create_s3_client(config)
        mock_boto3.client.assert_called_once_with("s3", config=config)

    @patch('lambda_code.resize_function.boto3')
    def test_handler_valid_image(self, mock_boto3):
        mock_s3_client = MagicMock()
        mock_boto3.client.return_value = mock_s3_client

        mock_event = {
            "Records": [
                {
                    "s3": {
                        "bucket": {"name": "source_bucket"},
                        "object": {"key": "test.jpg"}
                    }
                }
            ]
        }
        imgMock = open("tests/unit/test_image.jpg", "rb")
        mock_s3_client.get_object.return_value = {
            "Body": MagicMock(read=MagicMock(return_value=imgMock.read()))
        }
        imgMock.close()
        mock_s3_client.put_object.return_value = {}

        handler(mock_event, None)

        mock_s3_client.get_object.assert_called_once_with(Bucket="source_bucket", Key="test.jpg")
        mock_s3_client.put_object.assert_called_once()
        mock_s3_client.put_object.assert_called_with(Bucket="output-bucket", Key="test.jpg", Body=mock_s3_client.put_object.call_args[1]["Body"], ContentType="image/jpeg")
        mock_s3_client.put_object.call_args[1]["Body"].seek(0)
        thumbnail_data = mock_s3_client.put_object.call_args[1]["Body"].read()
        thumbnail_image = Image.open(io.BytesIO(thumbnail_data))
        self.assertEqual(thumbnail_image.size, (200, 134))

    @patch('lambda_code.resize_function.boto3')
    def test_handler_invalid_image(self, mock_boto3):
        mock_s3_client = MagicMock()
        mock_boto3.client.return_value = mock_s3_client

        mock_event = {
            "Records": [
                {
                    "s3": {
                        "bucket": {"name": "source_bucket"},
                        "object": {"key": "test.txt"}
                    }
                }
            ]
        }

        handler(mock_event, None)

        mock_s3_client.get_object.assert_not_called()
        mock_s3_client.put_object.assert_not_called()

    @patch('lambda_code.resize_function.boto3')
    def test_handler_get_object_error(self, mock_boto3):
        mock_s3_client = MagicMock()
        mock_boto3.client.return_value = mock_s3_client

        mock_event = {
            "Records": [
                {
                    "s3": {
                        "bucket": {"name": "source_bucket"},
                        "object": {"key": "test.jpg"}
                    }
                }
            ]
        }

        mock_s3_client.get_object.side_effect = ClientError({"Error": {"Code": "NoSuchKey"}}, "GetObject")

        with self.assertLogs(level="ERROR") as cm:
            handler(mock_event, None)

        self.assertIn("Error downloading test.jpg from source_bucket", cm.output[0])

    @patch('lambda_code.resize_function.boto3')
    def test_handler_put_object_error(self, mock_boto3):
        mock_s3_client = MagicMock()
        mock_boto3.client.return_value = mock_s3_client

        mock_event = {
            "Records": [
                {
                    "s3": {
                        "bucket": {"name": "source_bucket"},
                        "object": {"key": "test.jpg"}
                    }
                }
            ]
        }

        imgMock = open("tests/unit/test_image.jpg", "rb")
        mock_s3_client.get_object.return_value = {
            "Body": MagicMock(read=MagicMock(return_value=imgMock.read()))
        }
        imgMock.close()
        mock_s3_client.put_object.side_effect = ClientError({"Error": {"Code": "AccessDenied"}}, "PutObject")

        with self.assertLogs(level="ERROR") as cm:
            handler(mock_event, None)

        self.assertIn("Error uploading test.jpg to output-bucket", cm.output[0])

if __name__ == '__main__':
    unittest.main()
