FROM public.ecr.aws/docker/library/python:3.12-slim

# Add Lambda Web Adapter
COPY --from=public.ecr.aws/awsguru/aws-lambda-adapter:0.9.1 /lambda-adapter /opt/extensions/lambda-adapter

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy app code
COPY src/ .

# Start with Lambda Web Adapter (not uvicorn directly)
CMD ["/opt/extensions/lambda-adapter"]
