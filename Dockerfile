FROM python:3.13

RUN groupadd -g 1000 app && useradd -m -g 1000 -u 1000 app

RUN mkdir /app
WORKDIR /app

COPY rest_server /app/rest_server
COPY web_app /app/web_app
COPY universal_utils /app/universal_utils
COPY resources /app/resources
COPY tests /app/tests
COPY pyproject.toml /app/pyproject.toml
COPY README.md /app/README.md

RUN chown -R app:app /app

USER app

RUN git config --global --add safe.directory /app

ENV VIRTUAL_ENV=/app/venv

RUN python3 -m venv $VIRTUAL_ENV

ENV PATH="$VIRTUAL_ENV/bin:$PATH"

ARG VERSION
ENV SETUPTOOLS_SCM_PRETEND_VERSION_FOR_REST_SERVER_WEB_APP_UNIVERSAL_UTILS=$VERSION

RUN --mount=type=bind,source=.git,target=.git,ro pip install --no-cache -e .

CMD []
