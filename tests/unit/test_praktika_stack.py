import unittest
from aws_cdk import App
from aws_cdk.assertions import Template, Capture, Match
from praktika.praktika_stack import PraktikaStack


class TestPraktikaStack(unittest.TestCase):

    def setUp(self):
        self.app = App()
        self.stack = PraktikaStack(self.app, "PraktikaStack")
        self.template = Template.from_stack(self.stack)

    def test_s3_buckets_created(self):
        self.template.resource_count_is("AWS::S3::Bucket", 2)

    def test_lambda_functions_created(self):
        # two function because of the handler one
        self.template.resource_count_is("AWS::Lambda::Function", 2)


    def test_lambda_environment_variables(self):
        output_bucket_ref = Capture()

        self.template.has_resource_properties(
            "AWS::Lambda::Function",
            {
                "Handler": "resize_function.handler",
                "Runtime": "python3.12",
                "Environment": {"Variables": {"OUTPUT_BUCKET_NAME": output_bucket_ref}},
            },
        )

        self.assertIsInstance(output_bucket_ref.as_object(), dict)
        self.assertIn("Ref", output_bucket_ref.as_object())

    def test_s3_notifications_configured(self):
        self.template.has_resource_properties(
            "Custom::S3BucketNotifications",
            {
                "NotificationConfiguration": {
                    "LambdaFunctionConfigurations": Match.array_with(
                        [
                            {
                                "Events": ["s3:ObjectCreated:*"],
                                "LambdaFunctionArn": Match.any_value(),
                            }
                        ]
                    )
                }
            },
        )

    def test_lambda_permissions(self):
        self.template.has_resource_properties(
            "AWS::IAM::Policy",
            {
                "PolicyDocument": {
                    "Statement": Match.array_with(
                        [
                            {
                                "Action": [
                                    "s3:GetObject*",
                                    "s3:GetBucket*",
                                    "s3:List*",
                                ],
                                "Effect": "Allow",
                                "Resource": Match.any_value(),
                            },
                            {
                                "Action": [
                                    "s3:DeleteObject*",
                                    "s3:PutObject",
                                    "s3:PutObjectLegalHold",
                                    "s3:PutObjectRetention",
                                    "s3:PutObjectTagging",
                                    "s3:PutObjectVersionTagging",
                                    "s3:Abort*",
                                ],
                                "Effect": "Allow",
                                "Resource": Match.any_value(),
                            },
                        ]
                    )
                }
            },
        )


if __name__ == "__main__":
    unittest.main()
