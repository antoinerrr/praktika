.PHONY: synth deploy test

## synth: Synthesize the CloudFormation template from the CDK app
synth:
	@echo "Synthesizing the CloudFormation template..."
	cdk synth

## deploy: Deploy the CloudFormation stack
deploy:
	@echo "Deploying the stack..."
	cdk deploy

## test: Run unit tests
test:
	@echo "Running unit tests..."
	python -m unittest tests/unit/test_lambda_resize.py
	python -m unittest tests/unit/test_praktika_stack.py

## clean: Clean up the project (virtual environment, synth artifacts)
clean:
	@echo "Cleaning up..."
	rm -rf .venv
	cdk destroy