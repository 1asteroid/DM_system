FROM python:3.12-slim
WORKDIR /app
COPY . ./bot/
RUN pip install --no-cache-dir -r ./bot/requirements.txt
ENV PYTHONPATH=/app:$PYTHONPATH
CMD ["python", "-m", "bot.run"]
