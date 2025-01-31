FROM python:3.12-alpine

WORKDIR /data/qr-doc/

COPY ./requirements.txt /data/qr-doc/requirements.txt

RUN pip install --no-cache-dir --upgrade -r requirements.txt

COPY . /data/qr-doc/

EXPOSE 8000

CMD ["fastapi", "run", "main.py", "--port", "8000"]