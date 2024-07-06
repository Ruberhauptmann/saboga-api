FROM thehale/python-poetry:1.8.3-py3.12-slim as builder

COPY src/ /build/src
COPY pyproject.toml /build
COPY README.md /build

WORKDIR /build
RUN poetry build


FROM python:3.12.3-slim
ENV FASTAPI_ENV=production
COPY --from=builder /build/dist/ dist/
RUN pip3 install dist/*.whl
RUN rm -r dist/

EXPOSE 8000

# set working directory
WORKDIR /app

# add non-root user
RUN adduser user && chown -R user /app

# run command as user
USER user

CMD uvicorn sabogaapi.main:app --root-path /api --workers 1 --host 0.0.0.0 --port 8000
