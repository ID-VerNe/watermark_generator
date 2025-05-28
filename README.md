# 水印生成工具

一个基于 Python 和 Tkinter 的桌面应用程序，用于为图片生成定制化的水印。用户可以输入城市、地点、相机和镜头信息，并将其作为水印添加到图片中。

## 功能特性

*   **定制化水印**: 根据用户输入的城市、地点、相机和镜头信息生成水印。
*   **可配置字体和Logo**: 支持自定义字体、地点Logo和签名Logo。
*   **会话保存**: 自动保存上次会话的输入数据，方便下次使用。
*   **数据管理**: 通过 `data.json` 管理城市、地点、相机和镜头库，支持自动补全和新增。
*   **文件名定制**: 可根据城市、地点、相机、镜头信息自定义输出文件名。
*   **GUI 界面**: 提供直观的用户图形界面。

## 文件结构

```
.
├── application/
│   └── services/
│       └── watermark_service.py  # 水印生成的核心服务逻辑
├── config/
│   ├── .env                      # 环境变量和配置参数
│   ├── data.json                 # 城市、地点、相机、镜头等数据库
│   ├── last_session.json         # 上次会话数据保存
│   ├── location_logo.png         # 地点Logo图片
│   ├── logo.png                  # 应用程序图标
│   ├── misans.ttf                # 默认字体文件
│   └── signature_logo.png        # 签名Logo图片
├── domain/
│   ├── config_loader.py          # 配置加载模块
│   ├── exceptions.py             # 自定义异常类
│   └── image_processor.py        # 图像处理和水印生成逻辑
├── interface/
│   └── gui.py                    # Tkinter 用户界面实现
├── utils/
│   └── logger.py                 # 日志配置
├── main.py                       # 应用程序入口
├── LICENSE                       # 项目许可证文件 (MIT License)
├── README.md                     # 项目说明文件
└── requirements.txt              # 项目依赖
```

## 安装与运行

### 1. 克隆仓库

```bash
git clone https://github.com/ID-VerNe/watermark_generator.git
cd watermark_generator_tkinter
```

### 2. 创建虚拟环境 (推荐)

```bash
python -m venv venv
# Windows
.\venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 运行应用程序

```bash
python main.py
```

## 使用说明

1.  **启动应用**: 运行 `main.py` 后，将出现水印生成工具的图形界面。
2.  **输入信息**: 在相应的输入框中填写城市、地点、相机和镜头信息。这些字段支持自动补全，并且您输入的新项会自动添加到 `data.json` 库中。
3.  **字体大小与签名Logo宽度**: 可以调整水印的字体大小和签名Logo的宽度。
4.  **输出路径**: 选择水印图片的保存目录。默认是项目根目录下的 `output` 文件夹。
5.  **文件名配置**: 勾选您希望包含在输出文件名中的信息（城市、地点、相机、镜头），下方会实时预览文件名。
6.  **生成水印**: 点击“生成水印”按钮，水印图片将保存到指定的输出路径。
7.  **设置**: 点击“设置”按钮可以打开配置窗口，修改 `.env` 文件中的参数。修改后需要重启应用程序才能生效。

## 配置说明

项目的主要配置通过 `config/.env` 文件管理。您可以根据需要修改这些参数：

*   `LOCATION_LOGO_PATH`: 地点Logo图片路径。
*   `SIGNATURE_LOGO_PATH`: 签名Logo图片路径。
*   `FONT_PATH`: 字体文件路径。
*   `CANVAS_WIDTH`, `CANVAS_HEIGHT`: 生成水印图片的画布尺寸。
*   `PADDING`: 边缘留白。
*   `DEFAULT_FONT_SIZE`: 默认字体大小。
*   `DEFAULT_SIGNATURE_LOGO_WIDTH`: 默认签名Logo宽度。
*   `LOCATION_LOGO_TEXT_SPACING`: 地点Logo与文字的间距。
*   `TEXT_COLOR_R`, `TEXT_COLOR_G`, `TEXT_COLOR_B`, `TEXT_COLOR_A`: 水印文字颜色 (RGBA)。
*   `LOCATION_SEPARATOR`, `INFO_SEPARATOR`, `CAMERA_LENS_SEPARATOR`: 水印文本中的分隔符。
*   `LOCATION_VERTICAL_OFFSET`, `LOCATION_TEXT_HORIZONTAL_OFFSET`: 地点Logo和文字的垂直/水平偏移量。
*   `DEFAULT_CITY`, `DEFAULT_LOCATION`, `DEFAULT_CAMERA`, `DEFAULT_LENS`: 默认输入值。

## 许可证

本项目采用 MIT 许可证。详情请参阅 [LICENSE](LICENSE) 文件。

Copyright (c) 2024 [Your Name/Organization Name]
