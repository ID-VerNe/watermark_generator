import logging
from domain.config_loader import load_config
from domain.image_processor import ImageProcessor
from domain.exceptions import WatermarkGeneratorError, ConfigurationError, FileProcessingError, ImageProcessingError

logger = logging.getLogger(__name__)

class WatermarkService:
    def __init__(self):
        self.config = None
        self.image_processor = None
        self._load_dependencies()

    def _load_dependencies(self):
        """加载配置和图像处理器实例。"""
        try:
            self.config = load_config()
            self.image_processor = ImageProcessor(self.config)
            logger.info("水印服务依赖加载成功。")
        except ConfigurationError as e:
            logger.critical(f"配置加载失败: {e}")
            raise
        except FileProcessingError as e:
            logger.critical(f"文件处理错误（如字体文件）: {e}")
            raise
        except Exception as e:
            logger.critical(f"初始化水印服务时发生未知错误: {e}")
            raise WatermarkGeneratorError(f"初始化失败: {e}")

    def generate_watermark(self, city: str, location: str, camera: str, lens: str, output_path: str,
                           font_size: int = None, signature_logo_width: int = None) -> bool:
        """
        接收用户输入，调用图像处理器生成水印。
        返回 True 表示成功，False 表示失败。
        """
        if not self.image_processor:
            logger.error("ImageProcessor 未初始化。")
            return False

        try:
            logger.info(f"开始生成水印：城市={city}, 地点={location}, 相机={camera}, 镜头={lens}, 输出={output_path}")
            self.image_processor.generate_watermark(
                city=city,
                location=location,
                camera=camera,
                lens=lens,
                output_path=output_path,
                font_size=font_size,
                signature_logo_width=signature_logo_width
            )
            logger.info("水印生成成功。")
            return True
        except WatermarkGeneratorError as e:
            logger.error(f"生成水印时发生业务逻辑错误: {e}")
            return False
        except Exception as e:
            logger.error(f"生成水印时发生意外错误: {e}")
            return False
