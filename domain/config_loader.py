import os
import sys # 新增导入
import json
from dotenv import load_dotenv
from domain.exceptions import ConfigurationError
import logging

logger = logging.getLogger(__name__)

class Config:
    """
    存储应用程序配置的类。
    """
    def __init__(self):
        self.LOCATION_LOGO_PATH = None
        self.SIGNATURE_LOGO_PATH = None
        self.FONT_PATH = None
        self.CANVAS_WIDTH = None
        self.CANVAS_HEIGHT = None
        self.PADDING = None
        self.DEFAULT_FONT_SIZE = None
        self.DEFAULT_SIGNATURE_LOGO_WIDTH = None
        self.LOCATION_LOGO_TEXT_SPACING = None
        self.TEXT_COLOR_R = None
        self.TEXT_COLOR_G = None
        self.TEXT_COLOR_B = None
        self.TEXT_COLOR_A = None
        self.LOCATION_SEPARATOR = None
        self.INFO_SEPARATOR = None
        self.CAMERA_LENS_SEPARATOR = None
        self.LOCATION_VERTICAL_OFFSET = None # 新增参数
        self.LOCATION_TEXT_HORIZONTAL_OFFSET = None # 新增参数
        self.DEFAULT_CITY = None # 新增默认值参数
        self.DEFAULT_LOCATION = None # 新增默认值参数
        self.DEFAULT_CAMERA = None # 新增默认值参数
        self.DEFAULT_LENS = None # 新增默认值参数

        self.cities = [] # 城市库
        self.locations_by_city = {} # 地点库，现在是字典
        self.cameras = [] # 相机库
        self.lenses = [] # 镜头库
        self.last_session_data = {} # 上次会话数据

def load_config(): # 移除env_path参数，因为我们将动态构建它
    """
    从 .env 文件加载配置。
    """
    # 获取当前脚本的运行路径，对于打包后的exe，这将是exe所在的目录
    if getattr(sys, 'frozen', False):
        # 如果是打包后的exe
        base_path = os.path.dirname(sys.executable)
    else:
        # 如果是未打包的脚本，则使用当前文件所在的目录作为基准
        base_path = os.path.dirname(os.path.abspath(__file__))
        # 对于未打包的情况，config文件夹在项目根目录，而不是domain/config_loader.py的同级目录
        # 所以需要向上两级目录
        base_path = os.path.abspath(os.path.join(base_path, '..', '..'))


    # 构建config文件夹的绝对路径
    config_dir = os.path.join(base_path, 'config')

    # 调整env_path以使用绝对路径
    absolute_env_path = os.path.join(config_dir, '.env')
    load_dotenv(dotenv_path=absolute_env_path)
    config = Config()

    try:
        # 调整所有文件路径为绝对路径
        # 检查os.getenv的结果是否为空，避免os.path.join(config_dir, None)
        # 从.env中获取的路径可能包含'config/'前缀，这里只取文件名
        location_logo_full_path = os.getenv('LOCATION_LOGO_PATH')
        if location_logo_full_path:
            location_logo_name = os.path.basename(location_logo_full_path)
            config.LOCATION_LOGO_PATH = os.path.join(config_dir, location_logo_name)
        else:
            config.LOCATION_LOGO_PATH = None

        signature_logo_full_path = os.getenv('SIGNATURE_LOGO_PATH')
        if signature_logo_full_path:
            signature_logo_name = os.path.basename(signature_logo_full_path)
            config.SIGNATURE_LOGO_PATH = os.path.join(config_dir, signature_logo_name)
        else:
            config.SIGNATURE_LOGO_PATH = None

        font_full_path = os.getenv('FONT_PATH')
        if font_full_path:
            font_name = os.path.basename(font_full_path)
            config.FONT_PATH = os.path.join(config_dir, font_name)
        else:
            config.FONT_PATH = None

        config.CANVAS_WIDTH = int(os.getenv('CANVAS_WIDTH', '4000'))
        config.CANVAS_HEIGHT = int(os.getenv('CANVAS_HEIGHT', '764'))
        config.PADDING = int(os.getenv('PADDING', '20'))
        config.DEFAULT_FONT_SIZE = int(os.getenv('DEFAULT_FONT_SIZE', '40'))
        config.DEFAULT_SIGNATURE_LOGO_WIDTH = int(os.getenv('DEFAULT_SIGNATURE_LOGO_WIDTH', '300'))
        config.LOCATION_LOGO_TEXT_SPACING = int(os.getenv('LOCATION_LOGO_TEXT_SPACING', '10'))

        config.TEXT_COLOR_R = int(os.getenv('TEXT_COLOR_R', '255'))
        config.TEXT_COLOR_G = int(os.getenv('TEXT_COLOR_G', '255'))
        config.TEXT_COLOR_B = int(os.getenv('TEXT_COLOR_B', '255'))
        config.TEXT_COLOR_A = int(os.getenv('TEXT_COLOR_A', '255'))

        config.LOCATION_SEPARATOR = os.getenv('LOCATION_SEPARATOR', ' · ')
        config.INFO_SEPARATOR = os.getenv('INFO_SEPARATOR', ' & ')
        config.CAMERA_LENS_SEPARATOR = os.getenv('CAMERA_LENS_SEPARATOR', ' & ')
        config.LOCATION_VERTICAL_OFFSET = int(os.getenv('LOCATION_VERTICAL_OFFSET', '0'))
        config.LOCATION_TEXT_HORIZONTAL_OFFSET = int(os.getenv('LOCATION_TEXT_HORIZONTAL_OFFSET', '0'))

        config.DEFAULT_CITY = os.getenv('DEFAULT_CITY', 'GUANGZHOU')
        config.DEFAULT_LOCATION = os.getenv('DEFAULT_LOCATION', 'HUANGPU')
        config.DEFAULT_CAMERA = os.getenv('DEFAULT_CAMERA', 'LICE-7c')
        config.DEFAULT_LENS = os.getenv('DEFAULT_LENS', 'SIGMA 24-70mm F2.8 DG DN II Art')

        # 加载库数据
        data_file_path = os.path.join(config_dir, 'data.json')
        if os.path.exists(data_file_path):
            try:
                with open(data_file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    config.cities = data.get('cities', [])
                    config.locations_by_city = data.get('locations', {})
                    config.cameras = data.get('cameras', [])
                    config.lenses = data.get('lenses', [])
            except json.JSONDecodeError as e:
                logger.error(f"加载数据文件 '{data_file_path}' 失败，JSON格式错误: {e}")
            except Exception as e:
                logger.error(f"加载数据文件 '{data_file_path}' 时发生未知错误: {e}")
        else:
            logger.warning(f"数据文件 '{data_file_path}' 未找到，将使用空库。")

        # 加载上次会话数据
        session_file_path = os.path.join(config_dir, 'last_session.json')
        if os.path.exists(session_file_path):
            try:
                with open(session_file_path, 'r', encoding='utf-8') as f:
                    config.last_session_data = json.load(f)
            except json.JSONDecodeError as e:
                logger.error(f"加载会话文件 '{session_file_path}' 失败，JSON格式错误: {e}")
            except Exception as e:
                logger.error(f"加载会话文件 '{session_file_path}' 时发生未知错误: {e}")
        else:
            logger.warning(f"会话文件 '{session_file_path}' 未找到，将使用默认会话数据。")

        # 检查关键文件路径是否存在
        if not config.FONT_PATH or not os.path.exists(config.FONT_PATH):
            raise ConfigurationError(f"字体文件未找到或路径无效: {config.FONT_PATH}")
        if config.LOCATION_LOGO_PATH and not os.path.exists(config.LOCATION_LOGO_PATH): # 只有当路径存在时才检查
            logger.warning(f"地点Logo文件未找到或路径无效: {config.LOCATION_LOGO_PATH}。将不加载地点Logo。")
            config.LOCATION_LOGO_PATH = None
        if config.SIGNATURE_LOGO_PATH and not os.path.exists(config.SIGNATURE_LOGO_PATH): # 只有当路径存在时才检查
            logger.warning(f"签名Logo文件未找到或路径无效: {config.SIGNATURE_LOGO_PATH}。将不加载签名Logo。")
            config.SIGNATURE_LOGO_PATH = None

    except (ValueError, TypeError) as e:
        raise ConfigurationError(f"配置值类型错误: {e}")
    except Exception as e:
        raise ConfigurationError(f"加载配置时发生未知错误: {e}")

    logger.info("配置已成功加载。")
    return config
