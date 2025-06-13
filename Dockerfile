# Use the official Python image
FROM python:3.11

# Set the working directory in the container
WORKDIR /app

# Copy your code into the container
COPY . /app

# Install dependencies
RUN pip install --upgrade pip
RUN pip install pandas matplotlib

# Set the default command to run your script
CMD ["python", "src/energy_usage_reader.py"]