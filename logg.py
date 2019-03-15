# coding: utf-8
import logging

logger = logging.getLogger('main')
logger.setLevel(logging.INFO)
handler = logging.FileHandler('vol/main.log')
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s: %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
