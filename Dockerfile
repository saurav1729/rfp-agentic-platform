FROM python:3.12

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]


# --- START DOCKER ---
# To build the Docker image, use:
#    docker build -t rfp-api .
# To run the Docker container, use:
#    docker run -d -p 8000:8000 rfp-api