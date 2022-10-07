import logging
import logging.config as log_config
import pathlib
from dataclasses import dataclass, field
from os import environ

import yaml
from dotenv import load_dotenv, find_dotenv

from .helpers import EnvValue, log_depends_bool

load_dotenv()


class ConfigFactory:
    _env: str

    def create(self) -> 'Config':
        config_dict = {
            'development': DevelopmentConfig,
            'testing': TestingConfig,
            'production': ProductionConfig,
            'docker': DockerConfig
        }

        # 获取运行环境
        env = environ.get('AUM_ENV', 'production')
        if env not in config_dict:
            logging.warning(f'运行环境"{env}"不存在，将使用默认环境production！')
            env = 'production'
        self._env = env

        # 初始化日志模块
        self.__init_logging()

        logging.debug(f'运行环境：{env}')

        # 加载对应环境变量
        load_dotenv(find_dotenv(f'{env}.env'))

        # 创建配置并返回
        return DevelopmentConfig.from_env()

    def __init_logging(self):
        conf_path = pathlib.Path(f'conf/logging.{self._env}.yml')
        if not conf_path.exists():
            logging.warning(f'日志配置文件{conf_path}不存在，将使用默认格式。')
            return

        with open(conf_path, encoding='utf-8') as f:
            log_conf = yaml.safe_load(f)
        log_config.dictConfig(log_conf)


@dataclass(eq=False, frozen=True)
class Config:
    sel_hub_url: str = None  # selenium hub url

    unlock_music_server: str = None  # 音乐解锁服务的地址

    music_dir: pathlib.Path = None  # 音乐所在文件夹
    download_dir: pathlib.Path = None  # selenium hub下载目录

    locked_suffixes: set[str] = field(default_factory=set)  # 待解锁的后缀
    unlocked_suffixes: set[str] = field(default_factory=set)  # 已解锁的音乐文件后缀
    removing_substr: set[str] = field(default_factory=set)  # 文件名中需要移除的多余子串

    def __post_init__(self):
        """在日志中输出配置"""
        log_depends_bool('Selenium Hub', self.sel_hub_url)
        log_depends_bool('Unlock Music服务地址', self.unlock_music_server)

        log_depends_bool('音乐目录', self.music_dir)
        log_depends_bool('Selenium Hub下载目录', self.download_dir)

        log_depends_bool('待解锁的后缀', self.locked_suffixes)
        log_depends_bool('已解锁的后缀', self.unlocked_suffixes)
        log_depends_bool('将要移除的子串', self.removing_substr)

    @classmethod
    def from_env(cls) -> 'Config':
        properties = {}
        try:
            properties = {'sel_hub_url': EnvValue('AUM_SELENIUM_HUB', None).raw(),
                          'unlock_music_server': EnvValue('AUM_UNLOCK_SERVER', None).raw(),
                          'music_dir': EnvValue('AUM_MUSIC_DIR').to_path(),
                          'download_dir': EnvValue('AUM_DOWNLOAD_DIR').to_path(),
                          'locked_suffixes': EnvValue('AUM_LOCKED_SUFFIXES', '').to_str_set(),
                          'unlocked_suffixes': EnvValue('AUM_UNLOCKED_SUFFIXES', '').to_str_set(),
                          'removing_substr': EnvValue('AUM_REMOVING_SUBSTR', '').to_str_set()}
        except ValueError as e:
            logging.debug(e)
            exit(1)

        # 移除所有None value
        properties = {k: v for k, v in properties.items() if v is not None}

        return cls(**properties)


@dataclass(eq=False, frozen=True)
class DevelopmentConfig(Config):
    sel_hub_url: str = 'http://127.0.0.1:4444/wd/hub'
    unlock_music_server: str = 'https://demo.unlock-music.dev/'


@dataclass(eq=False, frozen=True)
class TestingConfig(Config):
    pass


@dataclass(eq=False, frozen=True)
class ProductionConfig(Config):
    pass


@dataclass(eq=False, frozen=True)
class DockerConfig(Config):
    pass
