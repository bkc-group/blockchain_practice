import os


basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))


class Config:
    DATABASE_DIR = '{}/{}'.format(basedir, 'db')
    LOG_FILE = '{}/logging/log_file'.format(DATABASE_DIR)

class AppConfig(Config):
    HOST = '0.0.0.0'
    PORT = 8080
    CLIENT_MAX_SIZE = 20*1024**2