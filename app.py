#!/usr/bin/env python3
import os

import aws_cdk as cdk

from praktika.praktika_stack import PraktikaStack


app = cdk.App()
env = cdk.Environment(
    account=os.getenv("CDK_DEFAULT_ACCOUNT"), region=os.getenv("CDK_DEFAULT_REGION")
)
PraktikaStack(app, "PraktikaStack", env=env)

app.synth()
