FROM python:2.7.16
RUN mkdir /app && \
    pip install flask
COPY . /app
WORKDIR /app
CMD ["python" ,"parser.py"]