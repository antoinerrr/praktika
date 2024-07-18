
# Praktika Technical test

You will need to have the aws-cdk installed already
To manually create a virtualenv on MacOS and Linux:

```
python3 -m venv .venv
```

After the init process completes and the virtualenv is created, you can use the following
step to activate your virtualenv.

```
source .venv/bin/activate
```

Once the virtualenv is activated, you can install the required dependencies.

```
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

If not done already bootstrap the cdk

```
cdk bootstrap
```

To run the test you can use:

```
make test
```

All the boto call are mocked to test the lambda locally without any issue

At this point you can now synthesize the CloudFormation template for this code.

```
cdk synth
```

Or deploy the app

```
cdk deploy
```
