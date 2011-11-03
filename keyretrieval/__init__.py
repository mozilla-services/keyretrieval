import os

from pyramid.config import Configurator

from mozsvc.config import load_into_settings


def main(global_config, **settings):
    config_file = global_config['__file__']
    load_into_settings(config_file, settings)

    config = Configurator(settings=settings)

    # adds auth from config file
    config.include("pyramid_multiauth")

    # adds cornice
    config.include("cornice")

    # adds Mozilla default views
    config.include("mozsvc")

    # adds application-specific views
    config.scan("keyretrieval.views")

    return config.make_wsgi_app()
