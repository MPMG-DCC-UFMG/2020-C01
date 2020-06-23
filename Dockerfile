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

#Install webwhatsappapi
RUN pip install "git+https://github.com/matheusfebarbosa/WebWhatsapp-Wrapper.git@23f278a417bae382380970125da49bb91e5fa215"

# COPY the source code
COPY source /app

# Set the default command
CMD python get_messages.py