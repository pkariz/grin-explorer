FROM python:3.8.15-bullseye


ENV PYTHONUNBUFFERED=1
WORKDIR /code
RUN pip install pipenv
COPY Pipfile /code/
COPY Pipfile.lock /code/
RUN pipenv install
COPY . /code/
COPY docker/django/start.sh /start-django.sh
COPY docker/django/start-prod.sh /start-prod-django.sh
RUN chmod +x /start-django.sh
RUN chmod +x /start-prod-django.sh
