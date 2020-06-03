# Use an official Python runtime as a parent image
FROM python:3.8

# Set the working directory to /app
WORKDIR /app

# COPY requirements to /app dir
COPY requirements.txt /app

# Install any needed packages specified in base.txt
RUN pip install --trusted-host pypi.python.org -r requirements.txt

#Install webwhatsappapi
RUN pip install "git+https://github.com/matheusfebarbosa/WebWhatsapp-Wrapper.git@8347bbaac4985a15abd31894307258c6f45a3471"

# COPY the source code
COPY source /app

# Set the default command
CMD ["python", "get_messages.py"]