FROM python:3.12-slim
WORKDIR /app
COPY . .
ENV BIND_HOST=0.0.0.0
EXPOSE 8000
CMD ["python", "server.py"]
