import boto3
import os
from PIL import Image
import io
import logging
from botocore.exceptions import ClientError
from botocore.config import Config

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Basic retry strategy for the boto call
config = Config(retries=dict(max_attempts=2))

THUMBNAIL_SIZE = (200, 200)
THUMBNAIL_BUCKET = os.environ.get("OUTPUT_BUCKET_NAME", "output-bucket")
ALLOWED_EXTENSIONS = (".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff")


def is_valid_image(key):
    return key.lower().endswith(ALLOWED_EXTENSIONS)


# Used for testing
def create_s3_client(config):
    return boto3.client("s3", config=config)


def handler(event, context, s3_client=None):
    if s3_client is None:
        s3_client = create_s3_client(config)

    for record in event["Records"]:
        source_bucket = record["s3"]["bucket"]["name"]
        source_key = record["s3"]["object"]["key"]

        if not is_valid_image(source_key):
            logger.warning(f"Skipping {source_key}: Not a supported image format")
            continue

        try:
            # Download the image from S3
            try:
                response = s3_client.get_object(Bucket=source_bucket, Key=source_key)
                image_content = response["Body"].read()
            except ClientError as e:
                logger.error(
                    f"Error downloading {source_key} from {source_bucket}: {e}"
                )
                raise

            # Create thumbnail
            try:
                with Image.open(io.BytesIO(image_content)) as img:
                    # There is no info on how to resize the image, if we need to force 200x200 
                    # or keep the aspect ratio, so we use the thumbnail method that keeps the aspect ratio
                    img.thumbnail(THUMBNAIL_SIZE)
                    buffer = io.BytesIO()
                    img.save(buffer, format=img.format)
                    buffer.seek(0)
            except Exception as e:
                logger.error(f"Error creating thumbnail: {e}")
                raise

            # Upload the thumbnail to S3
            thumbnail_key = f"{source_key}"
            try:
                s3_client.put_object(
                    Bucket=THUMBNAIL_BUCKET,
                    Key=thumbnail_key,
                    Body=buffer,
                    ContentType=f"image/{img.format.lower()}",
                )
            except ClientError as e:
                logger.error(
                    f"Error uploading {thumbnail_key} to {THUMBNAIL_BUCKET}: {e}"
                )
                raise

            logger.info(f"Successfully created thumbnail for {source_key}")

        except Exception as e:
            logger.exception(f"Unhandled error processing {source_key}: {str(e)}")
