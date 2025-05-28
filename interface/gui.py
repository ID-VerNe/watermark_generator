import json
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import logging
import re # 导入re模块用于正则表达式替换
import os
from PIL import Image, ImageTk # 导入PIL库
from application.services.watermark_service import WatermarkService
from domain.exceptions import WatermarkGeneratorError, ConfigurationError, FileProcessingError, ImageProcessingError

logger = logging.getLogger(__name__)

class WatermarkApp:
    def __init__(self, master):
        self.master = master
        master.title("水印生成")
        master.geometry("600x460") # 调整窗口大小以容纳更多控件
        master.resizable(False, False)

        # 设置窗口图标
        try:
            icon_path = os.path.join(os.getcwd(), 'config', 'logo.png')
            if os.path.exists(icon_path):
                icon_image = Image.open(icon_path)
                # 调整图标大小，例如 32x32
                icon_image = icon_image.resize((32, 32), Image.Resampling.LANCZOS)
                self.icon_photo = ImageTk.PhotoImage(icon_image)
                master.iconphoto(True, self.icon_photo)
            else:
                logger.warning(f"未找到图标文件: {icon_path}")
        except Exception as e:
            logger.error(f"设置窗口图标失败: {e}")

        self.watermark_service = None
        try:
            self.watermark_service = WatermarkService()
            # 获取配置和库数据
            self.config = self.watermark_service.config
        except WatermarkGeneratorError as e:
            messagebox.showerror("初始化错误", f"应用程序初始化失败: {e}\n请检查配置和文件路径。")
            master.destroy() # 如果服务无法初始化，则关闭应用程序
            return

        self.create_widgets()
        self.set_default_output_path()
        self.load_session_data() # 加载上次会话数据
        self.load_default_input_values() # 加载默认输入值（如果会话数据为空）
        master.protocol("WM_DELETE_WINDOW", self.on_closing) # 绑定窗口关闭事件

    def create_widgets(self):
        # 创建主框架
        main_frame = ttk.Frame(self.master, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 输入字段配置
        input_fields_config = [
            {"label": "城市:", "var_name": "city_var", "data_key": "cities", "is_city": True},
            {"label": "地点:", "var_name": "location_var", "data_key": "locations_by_city", "is_city": False},
            {"label": "相机:", "var_name": "camera_var", "data_key": "cameras", "is_city": False},
            {"label": "镜头:", "var_name": "lens_var", "data_key": "lenses", "is_city": False}
        ]

        self.vars = {}
        self.comboboxes = {} # 存储Combobox实例

        for field_config in input_fields_config:
            label_text = field_config["label"]
            var_name = field_config["var_name"]
            data_key = field_config["data_key"]
            is_city = field_config["is_city"]
            
            row_frame = ttk.Frame(main_frame)
            row_frame.pack(fill=tk.X, pady=5)

            ttk.Label(row_frame, text=label_text, width=10).pack(side=tk.LEFT, padx=(0, 5))
            
            self.vars[var_name] = tk.StringVar()
            
            # 对于城市，直接从 config.cities 获取值
            if is_city:
                combobox = ttk.Combobox(row_frame, textvariable=self.vars[var_name],
                                        values=self.config.cities)
                combobox.bind("<<ComboboxSelected>>", self.on_city_selected) # 城市选择事件
            else:
                # 对于地点、相机、镜头，初始值为空或从config中获取
                combobox = ttk.Combobox(row_frame, textvariable=self.vars[var_name],
                                        values=getattr(self.config, data_key, []))
            
            combobox.pack(side=tk.LEFT, fill=tk.X, expand=True)
            combobox.bind("<KeyRelease>", lambda event, dk=data_key, cb=combobox, is_city_field=is_city: self.on_combobox_key_release(event, dk, cb, is_city_field))
            self.comboboxes[var_name] = combobox # 保存Combobox实例

        # 字体大小设置
        font_size_frame = ttk.Frame(main_frame)
        font_size_frame.pack(fill=tk.X, pady=5)
        ttk.Label(font_size_frame, text="字体大小:", width=10).pack(side=tk.LEFT, padx=(0, 5))
        self.vars["font_size_var"] = tk.StringVar(value=str(self.watermark_service.config.DEFAULT_FONT_SIZE))
        ttk.Entry(font_size_frame, textvariable=self.vars["font_size_var"]).pack(side=tk.LEFT, fill=tk.X, expand=True)

        # 签名Logo宽度设置
        sig_logo_width_frame = ttk.Frame(main_frame)
        sig_logo_width_frame.pack(fill=tk.X, pady=5)
        ttk.Label(sig_logo_width_frame, text="签名Logo宽度:", width=10).pack(side=tk.LEFT, padx=(0, 5))
        self.vars["signature_logo_width_var"] = tk.StringVar(value=str(self.watermark_service.config.DEFAULT_SIGNATURE_LOGO_WIDTH))
        ttk.Entry(sig_logo_width_frame, textvariable=self.vars["signature_logo_width_var"]).pack(side=tk.LEFT, fill=tk.X, expand=True)

        # 输出路径选择
        output_path_frame = ttk.Frame(main_frame)
        output_path_frame.pack(fill=tk.X, pady=5)
        ttk.Label(output_path_frame, text="输出路径:", width=10).pack(side=tk.LEFT, padx=(0, 5))
        self.vars["output_path_var"] = tk.StringVar()
        ttk.Entry(output_path_frame, textvariable=self.vars["output_path_var"]).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(output_path_frame, text="浏览", command=self.browse_output_path).pack(side=tk.LEFT)

        # 文件名配置
        filename_config_frame = ttk.LabelFrame(main_frame, text="文件名配置", padding="10")
        filename_config_frame.pack(fill=tk.X, pady=10)

        self.filename_vars = {
            "city": tk.BooleanVar(value=True),
            "location": tk.BooleanVar(value=True),
            "camera": tk.BooleanVar(value=False),
            "lens": tk.BooleanVar(value=False)
        }
        self.filename_preview_var = tk.StringVar()

        checkbox_frame = ttk.Frame(filename_config_frame)
        checkbox_frame.pack(fill=tk.X)

        ttk.Checkbutton(checkbox_frame, text="城市", variable=self.filename_vars["city"], command=self.update_filename_preview).pack(side=tk.LEFT, padx=5)
        ttk.Checkbutton(checkbox_frame, text="地点", variable=self.filename_vars["location"], command=self.update_filename_preview).pack(side=tk.LEFT, padx=5)
        ttk.Checkbutton(checkbox_frame, text="相机", variable=self.filename_vars["camera"], command=self.update_filename_preview).pack(side=tk.LEFT, padx=5)
        ttk.Checkbutton(checkbox_frame, text="镜头", variable=self.filename_vars["lens"], command=self.update_filename_preview).pack(side=tk.LEFT, padx=5)

        ttk.Label(filename_config_frame, text="文件名预览:").pack(pady=(10, 5))
        ttk.Entry(filename_config_frame, textvariable=self.filename_preview_var, state="readonly").pack(fill=tk.X)

        # 绑定输入框的修改事件，以便实时更新文件名预览
        self.vars["city_var"].trace_add("write", lambda *args: self.update_filename_preview())
        self.vars["location_var"].trace_add("write", lambda *args: self.update_filename_preview())
        self.vars["camera_var"].trace_add("write", lambda *args: self.update_filename_preview())
        self.vars["lens_var"].trace_add("write", lambda *args: self.update_filename_preview())

        # 状态信息 (移到按钮上方或下方，这里选择上方)
        self.status_label = ttk.Label(main_frame, text="", foreground="blue")
        self.status_label.pack(pady=0)

        # 按钮容器框架
        button_container_frame = ttk.Frame(main_frame)
        button_container_frame.pack(fill=tk.X, pady=0)

        # 配置列权重
        button_container_frame.grid_columnconfigure(0, weight=8) # 生成水印按钮
        button_container_frame.grid_columnconfigure(1, weight=2) # 设置按钮

        # 生成水印按钮
        generate_button = ttk.Button(button_container_frame, text="生成水印", command=self.generate_watermark)
        generate_button.grid(row=0, column=0, sticky="ew", padx=(0, 5)) # sticky="ew" 使按钮填充单元格

        # 设置按钮
        settings_button = ttk.Button(button_container_frame, text="设置", command=self.open_settings_window)
        settings_button.grid(row=0, column=1, sticky="ew", padx=(5, 0)) # sticky="ew" 使按钮填充单元格

    def load_session_data(self):
        """从 config.last_session_data 加载上次会话数据并设置到GUI控件。"""
        session_data = self.config.last_session_data
        if session_data:
            self.vars["city_var"].set(session_data.get("city", ""))
            self.vars["location_var"].set(session_data.get("location", ""))
            self.vars["camera_var"].set(session_data.get("camera", ""))
            self.vars["lens_var"].set(session_data.get("lens", ""))
            self.vars["font_size_var"].set(session_data.get("font_size", str(self.config.DEFAULT_FONT_SIZE)))
            self.vars["signature_logo_width_var"].set(session_data.get("signature_logo_width", str(self.config.DEFAULT_SIGNATURE_LOGO_WIDTH)))
            self.vars["output_path_var"].set(session_data.get("output_path", os.path.join(os.getcwd(), "output")))
            
            # 加载文件名配置
            filename_config_data = session_data.get("filename_config", {})
            for key, var in self.filename_vars.items():
                if key in filename_config_data:
                    var.set(filename_config_data[key])
            
            # 立即更新文件名预览，以反映加载的配置
            self.update_filename_preview()

            logger.info("上次会话数据已加载。")
        else:
            logger.info("未找到上次会话数据，将加载默认配置。")

    def save_session_data(self):
        """保存当前GUI控件的值到 config/last_session.json。"""
        session_data = {
            "city": self.vars["city_var"].get().strip(),
            "location": self.vars["location_var"].get().strip(),
            "camera": self.vars["camera_var"].get().strip(),
            "lens": self.vars["lens_var"].get().strip(),
            "font_size": self.vars["font_size_var"].get().strip(),
            "signature_logo_width": self.vars["signature_logo_width_var"].get().strip(),
            "output_path": self.vars["output_path_var"].get().strip(),
            "filename_config": {key: var.get() for key, var in self.filename_vars.items()} # 保存文件名配置
        }
        session_file_path = 'config/last_session.json'
        try:
            with open(session_file_path, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, indent=4, ensure_ascii=False)
            logger.info(f"会话数据已保存到 {session_file_path}")
        except Exception as e:
            logger.error(f"保存会话数据到 '{session_file_path}' 失败: {e}")

    def on_closing(self):
        """处理窗口关闭事件，保存会话数据并退出。"""
        self.save_session_data()
        self.master.destroy()

    def load_default_input_values(self):
        """如果会话数据为空，则从配置中加载默认输入值并设置到Combobox。"""
        # 只有当会话数据没有提供值时才使用默认配置
        if not self.vars["city_var"].get():
            self.vars["city_var"].set(self.config.DEFAULT_CITY)
        if not self.vars["location_var"].get():
            self.vars["location_var"].set(self.config.DEFAULT_LOCATION)
        if not self.vars["camera_var"].get():
            self.vars["camera_var"].set(self.config.DEFAULT_CAMERA)
        if not self.vars["lens_var"].get():
            self.vars["lens_var"].set(self.config.DEFAULT_LENS)
        
        # 初始加载时，更新地点Combobox的值
        self.on_city_selected()

    def on_city_selected(self, event=None):
        """当城市Combobox选择改变时，更新地点Combobox的值。"""
        selected_city = self.vars["city_var"].get().strip().upper()
        locations_for_city = self.config.locations_by_city.get(selected_city, [])
        self.comboboxes["location_var"]['values'] = locations_for_city
        
        # 尝试加载上次该城市使用的地点
        last_location_for_city = self.config.last_session_data.get(selected_city, "")
        if last_location_for_city and last_location_for_city in locations_for_city:
            self.vars["location_var"].set(last_location_for_city)
        else:
            # 如果当前地点不在新城市的地点列表中，则清空地点输入
            if self.vars["location_var"].get().strip().upper() not in locations_for_city:
                self.vars["location_var"].set("")

    def on_combobox_key_release(self, event, data_key, combobox, is_city_field):
        """
        处理Combobox的按键释放事件，实现自动匹配。
        """
        current_text = self.vars[combobox.winfo_name()].get().strip().upper()
        
        # 获取当前库数据
        if is_city_field:
            all_values = self.config.cities
        elif data_key == "locations_by_city":
            selected_city = self.vars["city_var"].get().strip().upper()
            all_values = self.config.locations_by_city.get(selected_city, [])
        else:
            all_values = getattr(self.config, data_key, [])
        
        if current_text:
            # 过滤匹配的项
            matches = [item for item in all_values if item.startswith(current_text)]
            combobox['values'] = matches
        else:
            # 如果输入为空，显示所有值
            combobox['values'] = all_values
        
        # 尝试自动补全
        if matches and len(current_text) > 0:
            # 如果只有一个精确匹配，或者用户按下了Tab键，则自动填充
            if event.keysym == "Tab" or (len(matches) == 1 and matches[0] == current_text):
                self.vars[combobox.winfo_name()].set(matches[0])
                combobox.selection_clear() # 清除选择，避免再次触发
                if is_city_field: # 如果是城市字段，触发地点更新
                    self.on_city_selected()
            elif matches and event.keysym != "BackSpace" and event.keysym != "Delete":
                # 尝试进行部分自动补全
                longest_common_prefix = os.path.commonprefix(matches)
                if len(longest_common_prefix) > len(current_text):
                    combobox.set(longest_common_prefix)
                    combobox.icursor(tk.END) # 将光标移到末尾
                    combobox.selection_range(len(current_text), tk.END) # 选中补全部分
        
        # 弹出下拉列表
        if matches and current_text:
            combobox.event_generate('<Down>') # 模拟按下向下箭头，打开下拉列表
            combobox.focus() # 确保焦点在combobox上

    def _add_to_data_library(self, data_key, new_item, city_for_location=None):
        """将新项添加到对应的库中并保存。"""
        new_item = new_item.strip().upper()
        if not new_item:
            return False

        if data_key == "locations_by_city":
            if city_for_location:
                city_for_location = city_for_location.strip().upper()
                if city_for_location not in self.config.locations_by_city:
                    self.config.locations_by_city[city_for_location] = []
                
                if new_item not in self.config.locations_by_city[city_for_location]:
                    self.config.locations_by_city[city_for_location].append(new_item)
                    self.config.locations_by_city[city_for_location].sort()
                    self._save_data_libraries()
                    # 更新地点Combobox的值
                    if self.vars["city_var"].get().strip().upper() == city_for_location:
                        self.comboboxes["location_var"]['values'] = self.config.locations_by_city[city_for_location]
                    logger.info(f"已将 '{new_item}' 添加到 {city_for_location} 的地点库。")
                    return True
        else:
            current_library = getattr(self.config, data_key)
            if new_item not in current_library:
                current_library.append(new_item)
                current_library.sort() # 保持排序
                self._save_data_libraries()
                # 更新Combobox的值
                for cb_name, cb_instance in self.comboboxes.items():
                    # 找到对应的Combobox并更新其values
                    if (data_key == "cities" and cb_name == "city_var") or \
                       (data_key == "cameras" and cb_name == "camera_var") or \
                       (data_key == "lenses" and cb_name == "lens_var"):
                        cb_instance['values'] = current_library
                logger.info(f"已将 '{new_item}' 添加到 {data_key} 库。")
                return True
        return False

    def _save_data_libraries(self):
        """将当前的库数据保存到 config/data.json 文件。"""
        data_file_path = 'config/data.json'
        data_to_save = {
            "cities": self.config.cities,
            "locations": self.config.locations_by_city, # 保存为字典
            "cameras": self.config.cameras,
            "lenses": self.config.lenses
        }
        try:
            with open(data_file_path, 'w', encoding='utf-8') as f:
                json.dump(data_to_save, f, indent=4, ensure_ascii=False)
            logger.info(f"库数据已保存到 {data_file_path}")
        except Exception as e:
            logger.error(f"保存库数据到 '{data_file_path}' 失败: {e}")
            messagebox.showerror("保存错误", f"无法保存库数据: {e}")

    def set_default_output_path(self):
        """设置默认输出路径为当前工作目录下的 'output' 文件夹。"""
        default_dir = os.path.join(os.getcwd(), "output")
        if not os.path.exists(default_dir):
            os.makedirs(default_dir)
        self.vars["output_path_var"].set(default_dir)

    def browse_output_path(self):
        """打开文件对话框选择输出目录。"""
        directory = filedialog.askdirectory(initialdir=self.vars["output_path_var"].get())
        if directory:
            self.vars["output_path_var"].set(directory)

    def generate_watermark(self):
        """处理生成水印的逻辑。"""
        city = self.vars["city_var"].get().strip()
        location = self.vars["location_var"].get().strip()
        camera = self.vars["camera_var"].get().strip()
        lens = self.vars["lens_var"].get().strip()
        output_dir = self.vars["output_path_var"].get().strip()
        font_size_str = self.vars["font_size_var"].get().strip()
        signature_logo_width_str = self.vars["signature_logo_width_var"].get().strip()

        if not all([city, location, camera, lens, output_dir]):
            messagebox.showwarning("输入错误", "所有文本字段都不能为空！")
            return

        try:
            font_size = int(font_size_str) if font_size_str else None
            signature_logo_width = int(signature_logo_width_str) if signature_logo_width_str else None
        except ValueError:
            messagebox.showwarning("输入错误", "字体大小和签名Logo宽度必须是有效的整数！")
            return

        if not os.path.isdir(output_dir):
            try:
                os.makedirs(output_dir)
            except OSError as e:
                messagebox.showerror("路径错误", f"无法创建输出目录: {e}")
                logger.error(f"无法创建输出目录 {output_dir}: {e}")
                return

        # 将新输入的项添加到库中
        self._add_to_data_library("cities", city)
        self._add_to_data_library("locations_by_city", location, city_for_location=city) # 传入城市信息
        self._add_to_data_library("cameras", camera)
        self._add_to_data_library("lenses", lens)

    def update_filename_preview(self):
        """根据勾选框和输入框内容更新文件名预览。"""
        parts = []
        if self.filename_vars["city"].get():
            parts.append(self._sanitize_filename_part(self.vars["city_var"].get().strip()))
        if self.filename_vars["location"].get():
            parts.append(self._sanitize_filename_part(self.vars["location_var"].get().strip()))
        if self.filename_vars["camera"].get():
            parts.append(self._sanitize_filename_part(self.vars["camera_var"].get().strip()))
        if self.filename_vars["lens"].get():
            parts.append(self._sanitize_filename_part(self.vars["lens_var"].get().strip()))
        
        # 过滤空字符串并连接
        filtered_parts = [p.replace(" ", "_") for p in parts if p]
        if filtered_parts:
            preview_name = "_".join(filtered_parts) + ".png"
        else:
            preview_name = "watermark.png" # 至少有一个默认文件名
        
        self.filename_preview_var.set(preview_name)

    def generate_watermark(self):
        """处理生成水印的逻辑。"""
        city = self.vars["city_var"].get().strip()
        location = self.vars["location_var"].get().strip()
        camera = self.vars["camera_var"].get().strip()
        lens = self.vars["lens_var"].get().strip()
        output_dir = self.vars["output_path_var"].get().strip()
        font_size_str = self.vars["font_size_var"].get().strip()
        signature_logo_width_str = self.vars["signature_logo_width_var"].get().strip()

        if not all([city, location, camera, lens, output_dir]):
            messagebox.showwarning("输入错误", "所有文本字段都不能为空！")
            return

        try:
            font_size = int(font_size_str) if font_size_str else None
            signature_logo_width = int(signature_logo_width_str) if signature_logo_width_str else None
        except ValueError:
            messagebox.showwarning("输入错误", "字体大小和签名Logo宽度必须是有效的整数！")
            return

        if not os.path.isdir(output_dir):
            try:
                os.makedirs(output_dir)
            except OSError as e:
                messagebox.showerror("路径错误", f"无法创建输出目录: {e}")
                logger.error(f"无法创建输出目录 {output_dir}: {e}")
                return

        # 将新输入的项添加到库中
        self._add_to_data_library("cities", city)
        self._add_to_data_library("locations_by_city", location, city_for_location=city) # 传入城市信息
        self._add_to_data_library("cameras", camera)
        self._add_to_data_library("lenses", lens)

        # 获取生成的文件名
        output_filename = self.filename_preview_var.get()
        output_path = os.path.join(output_dir, output_filename)

        self.status_label.config(text="正在生成水印...", foreground="blue")
        self.master.update_idletasks() # 强制更新GUI

        try:
            success = self.watermark_service.generate_watermark(
                city=city,
                location=location,
                camera=camera,
                lens=lens,
                output_path=output_path,
                font_size=font_size,
                signature_logo_width=signature_logo_width
            )
            if success:
                self.status_label.config(text=f"水印生成成功！文件保存至: {output_path}", foreground="green")
                self.save_session_data() # 保存当前会话数据
            else:
                self.status_label.config(text="水印生成失败。", foreground="red")
                logger.error("水印生成失败，请查看日志获取更多信息。")
        except WatermarkGeneratorError as e:
            self.status_label.config(text=f"水印生成失败: {e}", foreground="red")
            logger.error(f"生成水印时发生错误: {e}")
        except Exception as e:
            self.status_label.config(text=f"水印生成失败: {e}", foreground="red")
            logger.critical(f"生成水印时发生未知错误: {e}", exc_info=True)

    def open_settings_window(self):
        """打开设置窗口，允许修改 .env 配置。"""
        settings_window = tk.Toplevel(self.master)
        settings_window.title("设置")
        settings_window.geometry("500x700")

        settings_frame = ttk.Frame(settings_window, padding="10")
        settings_frame.pack(fill=tk.BOTH, expand=True)

        # 读取 .env 文件内容
        env_path = 'config/.env'
        env_vars = {}
        if os.path.exists(env_path):
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        key_value = line.split('=', 1)
                        if len(key_value) == 2:
                            env_vars[key_value[0]] = tk.StringVar(value=key_value[1])
                        else:
                            env_vars[key_value[0]] = tk.StringVar(value="") # 处理没有值的键

        # 创建输入框
        self.settings_vars = {} # 存储设置窗口的StringVar
        for i, (key, var) in enumerate(env_vars.items()):
            row_frame = ttk.Frame(settings_frame)
            row_frame.pack(fill=tk.X, pady=2)
            ttk.Label(row_frame, text=f"{key}:", width=25).pack(side=tk.LEFT)
            entry = ttk.Entry(row_frame, textvariable=var)
            entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
            self.settings_vars[key] = var # 保存StringVar

        def save_settings():
            """保存设置到 .env 文件。"""
            updated_lines = []
            with open(env_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            for line in lines:
                stripped_line = line.strip()
                if stripped_line and not stripped_line.startswith('#'):
                    key_value = stripped_line.split('=', 1)
                    if len(key_value) == 2 and key_value[0] in self.settings_vars:
                        updated_lines.append(f"{key_value[0]}={self.settings_vars[key_value[0]].get()}\n")
                    else:
                        updated_lines.append(line)
                else:
                    updated_lines.append(line)
            
            # 添加新增加的但不在原始文件中的变量
            existing_keys = [line.split('=', 1)[0] for line in lines if line.strip() and not line.strip().startswith('#')]
            for key, var in self.settings_vars.items():
                if key not in existing_keys:
                    updated_lines.append(f"{key}={var.get()}\n")

            try:
                with open(env_path, 'w', encoding='utf-8') as f:
                    f.writelines(updated_lines)
                messagebox.showinfo("设置", "设置已保存，请重启应用程序以应用更改。")
                logger.info("设置已保存到 .env 文件。")
                settings_window.destroy()
            except Exception as e:
                messagebox.showerror("保存错误", f"保存设置失败: {e}")
                logger.error(f"保存设置失败: {e}")

        ttk.Button(settings_frame, text="保存设置", command=save_settings).pack(pady=10)
        ttk.Button(settings_frame, text="取消", command=settings_window.destroy).pack(pady=5)

    def _sanitize_filename_part(self, part):
        """替换文件名中不允许的字符为下划线。"""
        # 替换 / \ : * ? " < > | 为下划线
        invalid_chars = r'[\\/:*?"<>|]'
        return re.sub(invalid_chars, '_', part)
