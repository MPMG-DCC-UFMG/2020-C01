# Use an official Python runtime as a parent image
FROM python:3.8

# Set the working directory to /app
WORKDIR /app

# COPY requirements to /app dir
COPY requirements.txt /app

# Solve numpy dependency
RUN python -mpip install numpy

# Install any needed packages specified in base.txt
RUN pip install --trusted-host pypi.python.org -r requirements.txt

# Install webwhatsappapi lib
RUN pip install "git+https://github.com/matheusfebarbosa/WebWhatsapp-Wrapper.git@b66bfa81e2fc6e2375e9a3b522e0030907931e27"

# COPY the source code
COPY source /app

# Set the default run command
CMD python get_messages.py