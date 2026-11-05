FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY simulation/pyproject.toml simulation/README.md /app/simulation/
COPY simulation/src /app/simulation/src
COPY simulation/models /app/simulation/models
WORKDIR /app/simulation
RUN pip install --no-cache-dir ".[server]"
ENV OCTOPUS_MODEL_PATH=/app/simulation/models/octopus_dt_cad.xml
ENV OCTOPUS_CALIBRATION_DIR=/app/research/calibration
EXPOSE 8000
CMD ["uvicorn", "octopus_dt.server:app", "--host", "0.0.0.0", "--port", "8000"]
