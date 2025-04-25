FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY setup.py .
COPY README.md .
COPY backend/requirements.txt ./backend/
COPY frontend/requirements.txt ./frontend/

# Install all requirements
RUN pip install --no-cache-dir -e .

# Copy the rest of the code
COPY . .

# Expose ports
EXPOSE 8000
EXPOSE 8501

# Run the application
CMD ["python", "run.py"]
