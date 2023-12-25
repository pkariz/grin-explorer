import os
from .dev import *

DEBUG = False
ALLOWED_HOSTS = []
CORS_ORIGIN_WHITELIST = []
INSTALLED_APPS += ['gunicorn']

