import os
from PIL import Image, ImageDraw, ImageFont
import logging
from domain.config_loader import load_config, Config
from domain.exceptions import FileProcessingError, ImageProcessingError, ConfigurationError

logger = logging.getLogger(__name__)

class ImageProcessor:
    def __init__(self, config: Config):
        self.config = config
        self.font = self._load_font()
        self.location_logo = self._load_logo(self.config.LOCATION_LOGO_PATH)
        self.signature_logo = self._load_logo(self.config.SIGNATURE_LOGO_PATH)

    def _load_font(self):
        """加载字体文件。"""
        if not self.config.FONT_PATH:
            raise ConfigurationError("字体文件路径未配置。")
        try:
            return ImageFont.truetype(self.config.FONT_PATH, self.config.DEFAULT_FONT_SIZE)
        except IOError as e:
            raise FileProcessingError(f"无法加载字体文件 '{self.config.FONT_PATH}': {e}")
        except Exception as e:
            raise ConfigurationError(f"字体配置错误: {e}")

    def _load_logo(self, logo_path: str):
        """加载并返回 Logo 图片，如果路径无效则返回 None。"""
        if not logo_path:
            return None
        try:
            logo = Image.open(logo_path).convert("RGBA")
            logger.debug(f"成功加载Logo: {logo_path}")
            return logo
        except FileNotFoundError:
            logger.warning(f"Logo文件未找到: {logo_path}")
            return None
        except Exception as e:
            logger.error(f"加载Logo文件 '{logo_path}' 时发生错误: {e}")
            return None

    def _resize_logo_to_text_height(self, logo: Image.Image, text_height: int):
        """根据文本高度缩放 Logo。"""
        if not logo:
            return None
        original_width, original_height = logo.size
        if original_height == 0:
            return logo # 避免除以零
        new_height = text_height
        new_width = int(original_width * (new_height / original_height))
        return logo.resize((new_width, new_height), Image.Resampling.LANCZOS)

    def _get_text_dimensions(self, text: str, font: ImageFont.FreeTypeFont):
        """获取文本的尺寸 (宽度和高度)。"""
        # 使用 getmask().getbbox() 获取更精确的文本边界框
        # 这可以更好地处理不同字体和字符的实际渲染尺寸
        if not text:
            return 0, 0
        
        # 创建一个临时的ImageDraw对象来获取文本mask的bbox
        # 注意：getmask().getbbox() 返回的是 (left, top, right, bottom)
        # 这些坐标是相对于文本绘制的起始点 (0,0) 的
        mask = font.getmask(text, mode="L")
        bbox = mask.getbbox()
        
        if bbox:
            width = bbox[2] - bbox[0]
            height = bbox[3] - bbox[1]
            return width, height
        return 0, 0

    def generate_watermark(self, city: str, location: str, camera: str, lens: str, output_path: str,
                           font_size: int = None, signature_logo_width: int = None):
        """
        生成带有定制水印的透明 PNG 图片。
        """
        try:
            # 更新字体大小（如果用户指定）
            current_font = self.font
            if font_size and font_size != self.config.DEFAULT_FONT_SIZE:
                try:
                    current_font = ImageFont.truetype(self.config.FONT_PATH, font_size)
                except IOError as e:
                    raise FileProcessingError(f"无法加载指定字体大小的字体文件 '{self.config.FONT_PATH}': {e}")

            # 创建透明画布
            img = Image.new('RGBA', (self.config.CANVAS_WIDTH, self.config.CANVAS_HEIGHT), (255, 255, 255, 0))
            draw = ImageDraw.Draw(img)

            text_color = (self.config.TEXT_COLOR_R, self.config.TEXT_COLOR_G,
                          self.config.TEXT_COLOR_B, self.config.TEXT_COLOR_A)

            # 组合文本信息
            location_text = f"{city}{self.config.LOCATION_SEPARATOR}{location}".upper()
            info_text = f"SHOT ON {camera}{self.config.CAMERA_LENS_SEPARATOR}{lens}".upper()

            # 计算文本尺寸
            location_text_width, location_text_height = self._get_text_dimensions(location_text, current_font)
            info_text_width, info_text_height = self._get_text_dimensions(info_text, current_font)

            # 确定共同的底部 Y 坐标
            common_bottom_y = self.config.CANVAS_HEIGHT - self.config.PADDING

            # --- 绘制左侧部分 (地点 Logo + 地点文本) ---
            current_x_left = self.config.PADDING
            
            # 绘制地点 Logo
            scaled_location_logo = None
            
            # 绘制地点文本 (先计算文本的Y坐标，因为Logo要和文本底部对齐)
            location_text_y = common_bottom_y - location_text_height
            location_text_x = current_x_left + self.config.LOCATION_TEXT_HORIZONTAL_OFFSET
            draw.text((location_text_x, location_text_y), location_text, font=current_font, fill=text_color)
            
            if self.location_logo:
                # 缩放地点 Logo 使其与地点文本高度等高
                scaled_location_logo = self._resize_logo_to_text_height(self.location_logo, location_text_height)
                
                # 计算地点 Logo 的 Y 坐标，使其底部与文本底部对齐，并应用垂直偏移量
                location_logo_y = location_text_y + location_text_height - scaled_location_logo.height + self.config.LOCATION_VERTICAL_OFFSET
                
                # 计算地点 Logo 的 X 坐标，使其在文本左侧，并考虑文本的水平偏移量
                location_logo_x = current_x_left + self.config.LOCATION_TEXT_HORIZONTAL_OFFSET - self.config.LOCATION_LOGO_TEXT_SPACING - scaled_location_logo.width
                
                img.paste(scaled_location_logo, (location_logo_x, location_logo_y), scaled_location_logo)
                
                # 更新左侧部分的起始X坐标，以便后续计算总宽度（如果需要）
                # current_x_left += scaled_location_logo.width + self.config.LOCATION_LOGO_TEXT_SPACING + location_text_width
            else:
                # 如果没有Logo，只移动文本的起始X坐标
                # current_x_left += location_text_width # 文本已经绘制，这里只是为了后续计算
                pass # 文本已经绘制，不需要再移动 current_x_left

            # --- 绘制右侧部分 (签名 Logo + 信息文本) ---
            current_x_right = self.config.CANVAS_WIDTH - self.config.PADDING

            # 绘制信息文本 (相机 & 镜头)
            info_text_x = current_x_right - info_text_width
            info_text_y = common_bottom_y - info_text_height
            draw.text((info_text_x, info_text_y), info_text, font=current_font, fill=text_color)
            
            # 绘制签名 Logo (在信息文本上方，右对齐)
            scaled_signature_logo = None
            if self.signature_logo:
                if signature_logo_width is None:
                    signature_logo_width = self.config.DEFAULT_SIGNATURE_LOGO_WIDTH
                
                original_sig_width, original_sig_height = self.signature_logo.size
                if original_sig_width == 0:
                    sig_logo_height = original_sig_height
                else:
                    sig_logo_height = int(original_sig_height * (signature_logo_width / original_sig_width))
                
                scaled_signature_logo = self.signature_logo.resize((signature_logo_width, sig_logo_height), Image.Resampling.LANCZOS)
                
                # 签名Logo的X坐标与信息文本右对齐
                sig_logo_x = current_x_right - scaled_signature_logo.width
                # 签名Logo在信息文本上方，垂直间距为 PADDING / 2
                sig_logo_y = info_text_y - (self.config.PADDING // 2) - scaled_signature_logo.height
                
                img.paste(scaled_signature_logo, (sig_logo_x, sig_logo_y), scaled_signature_logo)

            # 保存图片
            img.save(output_path)
            logger.info(f"水印图片已成功生成并保存到: {output_path}")
            return True
        except (FileProcessingError, ImageProcessingError, ConfigurationError) as e:
            logger.error(f"生成水印时发生错误: {e}")
            raise
        except Exception as e:
            logger.error(f"生成水印时发生未知错误: {e}")
            raise ImageProcessingError(f"生成水印时发生未知错误: {e}")
