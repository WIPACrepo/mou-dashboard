FROM python:3.8

RUN useradd -m -U app

WORKDIR /home/app
USER app

COPY --chown=app:app . .

RUN pip install --no-cache-dir .
ENV PYTHONPATH=/home/app

CMD ["python", "-m", "rest_server"]
CMD ["python", "-m", "web_app"]