import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))


class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'app.db')
    # SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', '') or \
    #     'postgresql+psycopg2://postgres:roller0099@localhost:5432/store_run'
    #путь для сохранение файлов пользователей
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024
    SAVE_IMG_REVIEW_USER = 'images_users/review/'
    UPLOAD_FOLDER_REVIEW = '/Store/app/static/images_users/review'
    UPLOAD_FOLDER_PROFILE = '/Store/app/static/images_users/profile'
    UPLOAD_EXTENSIONS = ['.bmp', '.png', '.jpg', '.gif']

    # отключение сигнализации приложению каждый раз, когда в базе данных должно быть внесено изменение.
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # количество товара отображаемое на странице
    POSTS_PER_PAGE = 18
    # количество отзывов отображаемое на странице
    POSTS_PER_PAGE_REVIEW = 1

    ELASTICSEARCH_URL = os.environ.get('ELASTICSEARCH_URL')