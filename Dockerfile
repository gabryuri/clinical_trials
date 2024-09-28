FROM apache/airflow:2.7.3
USER airflow

COPY environment/requirements.txt .
RUN pip install -r requirements.txt --no-cache-dir

# USER airflow 


