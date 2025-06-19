# Use the official Python image
FROM python:3.11

# Set the working directory in the container
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Copy your code into the container
COPY . /app

# Install dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Expose the port your app runs on
EXPOSE 8000

# Set the default command to run your script
CMD ["uvicorn", "src.energy_usage_reader:app", "--host", "0.0.0.0", "--port", "8000"]