import os

from pyramid.config import Configurator

from mozsvc.config import Config


def main(global_config, **settings):
    config_file = global_config['__file__']
    config_file = os.path.abspath(
                    os.path.normpath(
                    os.path.expandvars(
                        os.path.expanduser(
                        config_file))))

    settings['config'] = config = Config(config_file)

    # Put values from the config file into the pyramid settings dict.
    for section in config.sections():
        setting_prefix = section.replace(":", ".")
        for name, value in config.get_map(section).iteritems():
            settings[setting_prefix + "." + name] = value

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
