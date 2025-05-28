class WatermarkGeneratorError(Exception):
    """水印生成工具的基类异常。"""
    pass

class ConfigurationError(WatermarkGeneratorError):
    """配置相关的异常。"""
    pass

class FileProcessingError(WatermarkGeneratorError):
    """文件处理相关的异常（如文件不存在、读取失败）。"""
    pass

class ImageProcessingError(WatermarkGeneratorError):
    """图像处理相关的异常。"""
    pass
