from abc import ABC, abstractmethod
from configparser import ConfigParser
from typing import Optional


class ConfigurationBase(ABC):
    """
    Base class that defines only the methods used at read time. Allows for efficient test mocks.
    """

    _the_one_configuration: Optional['ConfigurationBase'] = None

    @staticmethod
    def create_config_parser(full_filename: str) -> ConfigParser:
        config = ConfigParser()
        config.read(full_filename)

        return config

    @classmethod
    def set_instance(cls, configuration: 'ConfigurationBase'):
        cls._the_one_configuration = configuration

    @classmethod
    def get_config(cls):
        return cls._the_one_configuration

    @abstractmethod
    def get_git_username(self) -> str:
        pass

    @abstractmethod
    def get_git_token(self) -> str:
        pass

    @abstractmethod
    def get_viewer_directory(self) -> str:
        pass

    @abstractmethod
    def get_additional_viewer_launch_options(self) -> Optional[str]:
        pass


class Configuration(ConfigurationBase):

    @classmethod
    def initialize_from_ini_file(cls, full_filename: str) -> Optional[ConfigurationBase]:

        config_parser = cls.create_config_parser(full_filename=full_filename)

        return Configuration(config_parser)

    @classmethod
    def do_standard_initialization(cls) -> Optional[ConfigurationBase]:

        config = Configuration.initialize_from_ini_file('config.linux.ini')

        ConfigurationBase.set_instance(config)

        return config

    def __init__(self, config: ConfigParser):

        super().__init__()

        self.log_filename: Optional[str] = config['logs']['logfile']

        self.git_username: Optional[str] = config['git']['username']
        self.git_token: Optional[str] = config['git']['token']
        self.viewer_directory: Optional[str] = config['picture viewer']['directory']

        # this option is optional
        self.additional_launch_options: Optional[str] = None
        try:
            self.additional_launch_options: Optional[str] = config['picture viewer']['additional_options']
        except KeyError:
            # not an error - leave value as None
            pass

    def get_git_username(self) -> str:

        return self.git_username

    def get_git_token(self) -> str:

        return self.git_token

    def get_viewer_directory(self) -> str:

        return self.viewer_directory

    def get_additional_viewer_launch_options(self) -> Optional[str]:

        return self.additional_launch_options