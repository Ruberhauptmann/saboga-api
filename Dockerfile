# pull official python base image
FROM python:3.12.0

# set work directory
WORKDIR /app

# add non-root user
RUN adduser user && chown -R user /app

# copy migrations
COPY --chown=user:user migrations/ /app/


# install app
RUN pip install sabogaapi --index-url https://gitlab.com/api/v4/projects/52722115/packages/pypi/simple

# run command as user
USER user

# run wsgi server
CMD uvicorn sabogaapi.main:app --workers 1 --host 0.0.0.0 --port 8000
