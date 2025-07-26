FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/logs

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "app:app"]

curl -X POST -H "Content-Type: application/json" -d '{"questions_url": "https://beta.onlinetcsv5.meshilogic.co.in/website/ReadCourseQuestionDetails?PaperNameID=94"}' http://127.0.0.1:5000/group_similar_questions