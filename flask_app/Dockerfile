FROM python:3-alpine

WORKDIR /var/server/

COPY requirements.txt requirements.txt

RUN pip install -r requirements.txt

COPY . .

CMD ["gunicorn", "app:app", "-b", "0.0.0.0:8080"]

#CMD ["python", "app.py", "--host=0.0.0.0", "--port=8080"]