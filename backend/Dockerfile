# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
# Using --no-cache-dir to reduce image size
RUN pip install --no-cache-dir -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/

# Copy the rest of the application's source code from the host to the container
COPY . .

# Make port 7860 available to the world outside this container
EXPOSE 7860

# Define environment variable
ENV NAME World

# Run server.py when the container launches
CMD ["uvicorn", "server:app", "--proxy-headers", "--host", "0.0.0.0", "--port", "7860"] 