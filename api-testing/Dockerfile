# pull official python base image
FROM python:3.12.0

# set work directory
WORKDIR /app

# add non-root user
RUN adduser user && chown -R user /app

# copy migrations
#COPY --chown=user:user migrations/ /app/

# install app
COPY --chown=user:user ./dist /app/dist
RUN pip3 install dist/*.whl

# run command as user
USER user

# run wsgi server
CMD uvicorn sabogaapi.main:app --workers 1 --host 0.0.0.0 --port 8000
