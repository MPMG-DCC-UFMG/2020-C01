# Use an official Python runtime as a parent image
FROM python:3.8

# Set the working directory to /app
WORKDIR /app

# COPY requirements to /app dir
COPY requirements.txt /app

# Install any needed packages specified in base.txt
RUN pip install --trusted-host pypi.python.org -r requirements.txt

# COPY the source code
COPY source /app

# Set the default run command
CMD python get_messages.py


# Install kafka-needed java library and zookeeper
RUN apt-get install -y default-jre
RUN apt-get install zookeeperd

# Create needed folders
RUN mkdir /data && mkdir /data/kafka

# Install kafka-scripts
# COPY data/kafka.tgz /home/mp/Downloads/kafka/kafka.tgz
RUN wget https://downloads.apache.org/kafka/2.6.0/kafka_2.13-2.6.0.tgz -O /data/kafka/kafka.tgz
RUN tar -xvzf /data/kafka/kafka.tgz --strip 1 --directory /data/kafka/

