from aws_cdk import (
    Stack,
    aws_lambda as lambda_,
    aws_s3_notifications as s3n,
    aws_s3 as s3,
)
from constructs import Construct


class PraktikaStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create S3 buckets for input and output (with default permission so NO public access)
        input_bucket = s3.Bucket(self, "PraktikaInputBucket")
        output_bucket = s3.Bucket(self, "PraktikaOutputBucket")

        # Create the lambda function and add the layer
        resize_function = lambda_.Function(
            self,
            "ResizeImageFunction",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="resize_function.handler",
            code=lambda_.Code.from_asset("lambda_code"),
            environment={"OUTPUT_BUCKET_NAME": output_bucket.bucket_name},
        )
        # Add Pillow layer, pillow could (should) be included directly in the lambda package, but for this test i decided to keep it simple.
        pillow_layer = lambda_.LayerVersion.from_layer_version_arn(
            self,
            "PillowLayer",
            "arn:aws:lambda:"
            + self.region
            + ":770693421928:layer:Klayers-p312-Pillow:2",
        )
        resize_function.add_layers(pillow_layer)

        # Grand read on input bucket and write on output bucket
        input_bucket.grant_read(resize_function)
        output_bucket.grant_write(resize_function)

        # Add event notification for input bucket to trigger the lambda
        # This part is the one responsible for the 2nd lambda created by cloudformation,
        # the handler for "Custom::S3BucketNotifications", see: https://github.com/aws/aws-cdk/issues/9552#issuecomment-677512510
        input_bucket.add_event_notification(
            s3.EventType.OBJECT_CREATED, s3n.LambdaDestination(resize_function)
        )
