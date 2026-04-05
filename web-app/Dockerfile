FROM python:3.9-slim
WORKDIR /app 
RUN pip install --no-cache-dir flask boto3
COPY web-ce2/app.py . 
EXPOSE 5001
CMD ["python", "app.py"] 
