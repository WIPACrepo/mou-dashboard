FROM python:3.8

RUN useradd -m -U app

RUN pip install --no-cache-dir .

WORKDIR /home/app
USER app

COPY --chown=app:app . .

ENV PYTHONPATH=/home/app

CMD ["python", "-m", "rest_server"]
CMD ["python", "-m", "web_app"]