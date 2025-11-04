# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Install uv, the project's package manager
RUN pip install uv

# Copy dependency definition files
# This leverages Docker's layer caching, so dependencies are only re-installed when they change.
COPY pyproject.toml uv.lock* ./

# Install project dependencies using the lock file for reproducibility
RUN uv sync --system

# Copy the rest of the application's source code
COPY . .

# Command to run the application
# IMPORTANT: This is a placeholder. You may need to adjust this command
# based on how your application or specific agents are started.
CMD ["python", "main.py"]
