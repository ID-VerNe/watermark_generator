import tkinter as tk
import logging
from utils.logger import setup_logging
from interface.gui import WatermarkApp
from domain.exceptions import WatermarkGeneratorError

def main():
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("应用程序启动。")

    root = tk.Tk()
    try:
        app = WatermarkApp(root)
        root.mainloop()
    except WatermarkGeneratorError as e:
        logger.critical(f"应用程序启动失败: {e}")
        # 错误信息已在 WatermarkApp 构造函数中通过 messagebox 显示
    except Exception as e:
        logger.critical(f"应用程序发生意外错误: {e}", exc_info=True)
        tk.messagebox.showerror("严重错误", f"应用程序发生意外错误: {e}\n请查看日志获取更多信息。")
    finally:
        logger.info("应用程序退出。")

if __name__ == "__main__":
    main()
