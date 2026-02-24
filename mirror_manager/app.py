"""
Windows全局镜像管理器 - 主UI应用
透明玻璃浅色调圆角风格
"""
import customtkinter as ctk
import os
import sys
import subprocess
import json
import threading
import time
import urllib.request
import urllib.error
import winreg
import shutil
from typing import Dict, List, Optional, Tuple

# 设置外观
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

# 配色常量 - 玻璃拟态风格
COLOR_PRIMARY = "#4A90E2"      # 蓝色强调
COLOR_SECONDARY = "#5BA3F5"   # 辅助蓝
COLOR_CTA = "#4A90E2"          # 行动色
COLOR_BG = "#F0F4F8"          # 背景色
COLOR_TEXT = "#1A1A2E"         # 深色文字
COLOR_SUCCESS = "#27AE60"       # 成功绿
COLOR_ERROR = "#E74C3C"         # 错误红
COLOR_WHITE = "#FFFFFF"        # 白色
COLOR_BORDER = "#E8ECF0"       # 边框
COLOR_GLASS = "#FFFFFF"        # 玻璃色


class MirrorManagerApp(ctk.CTk):
    """Windows镜像管理器主应用"""
    
    def __init__(self):
        super().__init__()
        
        # 窗口配置
        self.title("Windows镜像管理器")
        self.geometry("560x750")
        self.resizable(False, False)
        
        # 设置背景色
        self.configure(fg_color=COLOR_BG)
        
        # 加载镜像配置
        self.mirrors = self.load_mirrors_config()
        
        # 镜像配置
        self.current_git_mirror = ""
        self.current_pip_mirror = ""
        self.current_hf_mirror = ""
        
        # 测试状态
        self.testing = {"git": False, "pip": False, "hf": False}
        
        # 创建UI
        self.create_ui()
        
        # 加载当前配置
        self.load_current_config()
    
    def load_mirrors_config(self) -> Dict:
        """加载镜像配置文件"""
        config_path = os.path.join(os.path.dirname(__file__), "..", "mirrors.json")
        
        # 默认配置
        default_config = {
            "git": [
                {"name": "原始", "url": ""},
                {"name": "阿里云", "url": "https://mirrors.aliyun.com/git/"},
                {"name": "腾讯云", "url": "https://mirrors.cloud.tencent.com/git/"},
                {"name": "华为云", "url": "https://repo.huaweicloud.com/git/"},
            ],
            "pip": [
                {"name": "原始", "url": ""},
                {"name": "阿里云", "url": "https://mirrors.aliyun.com/pypi/simple/"},
                {"name": "清华", "url": "https://pypi.tuna.tsinghua.edu.cn/simple"},
                {"name": "腾讯云", "url": "https://mirrors.cloud.tencent.com/pypi/simple"},
                {"name": "华为云", "url": "https://repo.huaweicloud.com/repository/pypi/simple"},
            ],
            "huggingface": [
                {"name": "原始", "url": "https://huggingface.co"},
                {"name": "镜像1", "url": "https://hf-mirror.com"},
            ]
        }
        
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        
        return default_config
    
    def create_ui(self):
        """创建UI组件 - 玻璃拟态风格"""
        # 主容器
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=16)
        
        # 标题
        title_label = ctk.CTkLabel(
            self.main_frame,
            text="Windows 镜像管理器",
            font=("Microsoft YaHei", 22, "bold"),
            text_color=COLOR_TEXT
        )
        title_label.pack(pady=(0, 20))
        
        # Git镜像模块
        self.create_mirror_module(
            "Git 镜像",
            "git",
            self.mirrors.get("git", [])
        )
        
        # Pip镜像模块
        self.create_mirror_module(
            "Pip 镜像",
            "pip",
            self.mirrors.get("pip", [])
        )
        
        # HuggingFace镜像模块
        self.create_mirror_module(
            "HuggingFace 镜像",
            "hf",
            self.mirrors.get("huggingface", [])
        )
        
        # 分隔线
        separator = ctk.CTkFrame(self.main_frame, height=1, fg_color=COLOR_BORDER)
        separator.pack(fill="x", pady=16)
        
        # 当前配置状态显示
        self.create_status_section()
        
        # 分隔线
        separator = ctk.CTkFrame(self.main_frame, height=1, fg_color=COLOR_BORDER)
        separator.pack(fill="x", pady=16)
        
        # 应用按钮
        self.create_apply_button()
        
        # 状态显示
        self.create_apply_status()
    
    def create_mirror_module(self, label: str, key: str, options: List[Dict]):
        """创建单个镜像模块 - 玻璃卡片"""
        # 模块容器 - 玻璃效果，圆角20，柔和阴影
        module_frame = ctk.CTkFrame(
            self.main_frame,
            fg_color=("#FFFFFF", "#2D2D3A"),
            corner_radius=20,
            border_width=0,
        )
        module_frame.pack(fill="x", pady=(0, 14))
        
        # 内部容器
        inner_frame = ctk.CTkFrame(module_frame, fg_color="transparent")
        inner_frame.pack(fill="x", padx=20, pady=(18, 10))
        
        # 标签
        ctk.CTkLabel(
            inner_frame,
            text=label,
            font=("Microsoft YaHei", 14, "bold"),
            text_color=COLOR_TEXT
        ).pack(side="left")
        
        # 下拉框 - 圆润
        option_names = [opt["name"] for opt in options]
        
        combo = ctk.CTkComboBox(
            inner_frame,
            values=option_names,
            width=200,
            fg_color=("white", "#3D3D4A"),
            border_color=COLOR_BORDER,
            button_color=COLOR_PRIMARY,
            button_hover_color="#3A7BC8",
            text_color=COLOR_TEXT,
            font=("Microsoft YaHei", 12),
            corner_radius=14,
            border_width=1
        )
        combo.pack(side="left", padx=15)
        combo.set(option_names[0] if option_names else "原始")
        
        # 保存combo引用
        setattr(self, f"{key}_combo", combo)
        
        # 测试按钮 - 渐变感
        test_btn = ctk.CTkButton(
            inner_frame,
            text="测试",
            width=80,
            height=36,
            fg_color=COLOR_PRIMARY,
            hover_color="#3A7BC8",
            text_color="white",
            font=("Microsoft YaHei", 12, "bold"),
            corner_radius=14,
            border_width=0,
            command=lambda k=key: self.test_mirror(k)
        )
        test_btn.pack(side="right")
        
        # 状态标签
        status_label = ctk.CTkLabel(
            module_frame,
            text="",
            font=("Microsoft YaHei", 11),
            text_color="#8899A6",
            anchor="w"
        )
        status_label.pack(fill="x", padx=20, pady=(0, 16))
        
        # 保存状态标签引用
        setattr(self, f"{key}_status", status_label)
        
        # 保存选项数据
        setattr(self, f"{key}_options", options)
    
    def create_status_section(self):
        """创建当前配置状态显示区 - 玻璃卡片"""
        status_frame = ctk.CTkFrame(
            self.main_frame,
            fg_color=("#FFFFFF", "#2D2D3A"),
            corner_radius=20,
            border_width=0
        )
        status_frame.pack(fill="x", pady=(0, 16))
        
        ctk.CTkLabel(
            status_frame,
            text="当前配置状态",
            font=("Microsoft YaHei", 14, "bold"),
            text_color=COLOR_TEXT
        ).pack(anchor="w", padx=20, pady=(18, 12))
        
        # 配置详情
        self.git_status_label = ctk.CTkLabel(
            status_frame,
            text="Git: 未配置",
            font=("Microsoft YaHei", 12),
            text_color="#8899A6",
            anchor="w"
        )
        self.git_status_label.pack(fill="x", padx=20, pady=4)
        
        self.pip_status_label = ctk.CTkLabel(
            status_frame,
            text="Pip: 未配置",
            font=("Microsoft YaHei", 12),
            text_color="#8899A6",
            anchor="w"
        )
        self.pip_status_label.pack(fill="x", padx=20, pady=4)
        
        self.hf_status_label = ctk.CTkLabel(
            status_frame,
            text="HuggingFace: 未配置",
            font=("Microsoft YaHei", 12),
            text_color="#8899A6",
            anchor="w"
        )
        self.hf_status_label.pack(fill="x", padx=20, pady=(4, 18))
    
    def create_apply_button(self):
        """创建应用按钮 - 玻璃拟态，居中大按钮"""
        self.apply_btn = ctk.CTkButton(
            self.main_frame,
            text="应用配置",
            width=280,
            height=52,
            fg_color=COLOR_PRIMARY,
            hover_color="#3A7BC8",
            text_color="white",
            font=("Microsoft YaHei", 17, "bold"),
            corner_radius=26,
            border_width=0,
            command=self.apply_config
        )
        self.apply_btn.pack(pady=(10, 0))
    
    def create_apply_status(self):
        """创建应用状态显示"""
        self.apply_status = ctk.CTkLabel(
            self.main_frame,
            text="",
            font=("Microsoft YaHei", 12),
            text_color=COLOR_PRIMARY
        )
        self.apply_status.pack(pady=(15, 0))
        
        # 进度条（默认隐藏）
        self.progress_bar = ctk.CTkProgressBar(
            self.main_frame,
            width=400,
            height=6,
            progress_color=COLOR_PRIMARY,
            corner_radius=3
        )
        self.progress_bar.set(0)
        self.progress_bar.pack(pady=(10, 0))
        self.progress_bar.pack_forget()  # 初始隐藏
    
    def test_mirror(self, mirror_type: str):
        """测试镜像连接"""
        if self.testing.get(mirror_type, False):
            return
        
        self.testing[mirror_type] = True
        
        # 获取当前选择的镜像
        combo = getattr(self, f"{mirror_type}_combo")
        status_label = getattr(self, f"{mirror_type}_status")
        options = getattr(self, f"{mirror_type}_options")
        
        selected_name = combo.get()
        selected_url = ""
        
        for opt in options:
            if opt["name"] == selected_name:
                selected_url = opt.get("url", "")
                break
        
        # 如果选择原始，清空配置
        if selected_name == "原始" or not selected_url:
            status_label.configure(text="状态：原始（无镜像）", text_color=COLOR_TEXT)
            self.testing[mirror_type] = False
            return
        
        # 显示测试中状态
        status_label.configure(text="状态：测试中...", text_color=COLOR_SECONDARY)
        
        # 禁用按钮
        combo.configure(state="disabled")
        
        # 启动测试线程
        thread = threading.Thread(
            target=self._test_mirror_thread,
            args=(mirror_type, selected_url, status_label, combo)
        )
        thread.daemon = True
        thread.start()
    
    def _test_mirror_thread(self, mirror_type: str, url: str, status_label, combo):
        """测试镜像连接（后台线程）"""
        start_time = time.time()
        
        try:
            # 发送HEAD请求测试连接
            req = urllib.request.Request(
                url,
                method="HEAD",
                headers={"User-Agent": "Windows-Mirror-Manager/1.0"}
            )
            
            with urllib.request.urlopen(req, timeout=10) as response:
                elapsed_ms = int((time.time() - start_time) * 1000)
                status_label.configure(
                    text=f"状态：连接成功 - {elapsed_ms}ms",
                    text_color=COLOR_SUCCESS
                )
        except urllib.error.URLError as e:
            status_label.configure(
                text=f"状态：连接失败 - {str(e.reason)}",
                text_color=COLOR_ERROR
            )
        except Exception as e:
            status_label.configure(
                text=f"状态：测试失败 - {str(e)}",
                text_color=COLOR_ERROR
            )
        finally:
            # 重新启用下拉框
            self.after(0, lambda: combo.configure(state="normal"))
            self.testing[mirror_type] = False
    
    def load_current_config(self):
        """加载当前配置状态 - 检测系统、用户、虚拟环境的配置"""
        # Git配置
        git_url = self._get_git_config()
        if git_url:
            self.git_status_label.configure(text=f"Git: {git_url}")
        else:
            self.git_status_label.configure(text="Git: 未配置")
        
        # Pip配置
        pip_mirror = self._get_pip_config()
        if pip_mirror:
            self.pip_status_label.configure(text=f"Pip: {pip_mirror}")
        else:
            self.pip_status_label.configure(text="Pip: 未配置")
        
        # HuggingFace配置
        hf_home = self._get_hf_config()
        if hf_home:
            self.hf_status_label.configure(text=f"HuggingFace: {hf_home}")
        else:
            self.hf_status_label.configure(text="HuggingFace: 未配置")
    
    def _get_git_config(self) -> Optional[str]:
        """获取Git当前配置的镜像URL"""
        try:
            # 读取全局git配置
            result = subprocess.run(
                ['git', 'config', '--global', 'url."https://mirrors.aliyun.com".insteadOf'],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0 and result.stdout.strip():
                return "阿里云"
            
            result = subprocess.run(
                ['git', 'config', '--global', 'url."https://mirrors.cloud.tencent.com".insteadOf'],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0 and result.stdout.strip():
                return "腾讯云"
            
            result = subprocess.run(
                ['git', 'config', '--global', 'url."https://repo.huaweicloud.com".insteadOf'],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0 and result.stdout.strip():
                return "华为云"
                
            result = subprocess.run(
                ['git', 'config', '--global', 'url."https://pypi.tuna.tsinghua.edu.cn".insteadOf'],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0 and result.stdout.strip():
                return "清华"
        except Exception:
            pass
        return None
    
    def _get_pip_config(self) -> Optional[str]:
        """获取Pip当前配置的镜像源"""
        # 检查用户级pip配置
        pip_conf = os.path.expanduser('~/.pip/pip.conf')
        if os.path.exists(pip_conf):
            try:
                with open(pip_conf, 'r') as f:
                    content = f.read()
                    if 'aliyun' in content.lower():
                        return "阿里云"
                    elif 'tuna' in content.lower() or 'tsinghua' in content.lower():
                        return "清华"
                    elif 'tencent' in content.lower():
                        return "腾讯云"
                    elif 'huawei' in content.lower():
                        return "华为云"
            except Exception:
                pass
        
        # 检查环境变量
        proxy = os.environ.get('PIP_PROXY') or os.environ.get('HTTPS_PROXY')
        if proxy:
            return f"代理: {proxy}"
        
        return None
    
    def _get_hf_config(self) -> Optional[str]:
        """获取HuggingFace当前配置"""
        hf_home = os.environ.get('HF_HOME') or os.environ.get('TRANSFORMERS_CACHE')
        if hf_home:
            if 'hf-mirror.com' in hf_home:
                return "镜像1"
            return hf_home
        return None
    
    def apply_config(self):
        """应用配置 - 写入全局配置、设置环境变量、清理用户级配置"""
        # 获取选择的镜像
        git_combo = getattr(self, "git_combo")
        pip_combo = getattr(self, "pip_combo")
        hf_combo = getattr(self, "hf_combo")
        
        git_selected = git_combo.get()
        pip_selected = pip_combo.get()
        hf_selected = hf_combo.get()
        
        # 更新状态
        self.apply_status.configure(text="正在应用配置...")
        self.apply_btn.configure(state="disabled")
        self.progress_bar.pack()
        self.progress_bar.set(0.1)
        
        # 在后台线程执行配置应用
        thread = threading.Thread(
            target=self._apply_config_thread,
            args=(git_selected, pip_selected, hf_selected)
        )
        thread.daemon = True
        thread.start()
    
    def _apply_config_thread(self, git: str, pip: str, hf: str):
        """应用配置的后台线程"""
        try:
            self.after(0, lambda: self.progress_bar.set(0.2))
            
            # 获取镜像URL
            git_url = self._get_mirror_url("git", git)
            pip_url = self._get_mirror_url("pip", pip)
            hf_url = self._get_mirror_url("huggingface", hf)
            
            # 1. 如果选择"原始"，清理所有配置
            if git == "原始":
                self._clear_git_config()
            elif git_url:
                self._set_git_config(git_url, git)
            
            self.after(0, lambda: self.progress_bar.set(0.4))
            
            if pip == "原始":
                self._clear_pip_config()
            elif pip_url:
                self._set_pip_config(pip_url)
            
            self.after(0, lambda: self.progress_bar.set(0.6))
            
            if hf == "原始":
                self._clear_hf_config()
            elif hf_url:
                self._set_hf_config(hf_url)
            
            self.after(0, lambda: self.progress_bar.set(0.8))
            
            # 完成
            self.after(0, lambda: self._finish_apply(git, pip, hf))
            
        except Exception as e:
            self.after(0, lambda: self._apply_error(str(e)))
    
    def _get_mirror_url(self, mirror_type: str, name: str) -> Optional[str]:
        """根据镜像名称获取URL"""
        options = getattr(self, f"{mirror_type}_options", [])
        for opt in options:
            if opt["name"] == name:
                return opt.get("url", "")
        return None
    
    def _set_git_config(self, url: str, name: str):
        """设置Git全局镜像"""
        # 写入系统级git配置
        try:
            # 清理用户级配置
            user_gitconfig = os.path.expanduser('~/.gitconfig')
            if os.path.exists(user_gitconfig):
                os.remove(user_gitconfig)
            
            # 设置全局url.insteadOf
            subprocess.run(
                ['git', 'config', '--global', f'url."{url}".insteadOf', 'https://github.com'],
                check=True, timeout=10
            )
            subprocess.run(
                ['git', 'config', '--global', f'url."{url}".insteadOf', 'https://github.com/'],
                check=True, timeout=10
            )
        except Exception as e:
            print(f"Git config error: {e}")
    
    def _clear_git_config(self):
        """清理Git所有镜像配置"""
        try:
            # 清理用户级配置
            subprocess.run(['git', 'config', '--global', '--unset', 'url."https://mirrors.aliyun.com".insteadOf'], timeout=10)
            subprocess.run(['git', 'config', '--global', '--unset', 'url."https://mirrors.cloud.tencent.com".insteadOf'], timeout=10)
            subprocess.run(['git', 'config', '--global', '--unset', 'url."https://repo.huaweicloud.com".insteadOf'], timeout=10)
            # 清理gitconfig文件
            user_gitconfig = os.path.expanduser('~/.gitconfig')
            if os.path.exists(user_gitconfig):
                os.remove(user_gitconfig)
        except Exception as e:
            print(f"Clear git config error: {e}")
    
    def _set_pip_config(self, url: str):
        """设置Pip全局镜像"""
        try:
            # 创建用户级pip配置目录
            pip_dir = os.path.expanduser('~/.pip')
            os.makedirs(pip_dir, exist_ok=True)
            
            # 清理旧的虚拟环境配置
            venv_pip_conf = os.path.join(os.environ.get('VIRTUAL_ENV', ''), 'pip.conf')
            if os.path.exists(venv_pip_conf):
                os.remove(venv_pip_conf)
            
            # 写入全局pip.conf
            pip_conf = os.path.join(pip_dir, 'pip.conf')
            with open(pip_conf, 'w', encoding='utf-8') as f:
                f.write('[global]\n')
                f.write(f'mirror = {url}\n')
                f.write('timeout = 60\n')
            
            # 设置环境变量（当前进程）
            os.environ['PIP_INDEX_URL'] = url
            
        except Exception as e:
            print(f"Pip config error: {e}")
    
    def _clear_pip_config(self):
        """清理Pip所有镜像配置"""
        try:
            # 删除用户级pip配置
            pip_conf = os.path.expanduser('~/.pip/pip.conf')
            if os.path.exists(pip_conf):
                os.remove(pip_conf)
            
            pip_ini = os.path.expanduser('~/pip.ini')
            if os.path.exists(pip_ini):
                os.remove(pip_ini)
            
            # 清理环境变量
            if 'PIP_INDEX_URL' in os.environ:
                del os.environ['PIP_INDEX_URL']
            if 'PIP_PROXY' in os.environ:
                del os.environ['PIP_PROXY']
                
        except Exception as e:
            print(f"Clear pip config error: {e}")
    
    def _set_hf_config(self, url: str):
        """设置HuggingFace全局配置"""
        try:
            # 设置环境变量
            os.environ['HF_HOME'] = url
            os.environ['TRANSFORMERS_CACHE'] = url + '/transformers'
            
            # 创建目录
            os.makedirs(url, exist_ok=True)
            
        except Exception as e:
            print(f"HF config error: {e}")
    
    def _clear_hf_config(self):
        """清理HuggingFace配置"""
        try:
            # 清理环境变量
            if 'HF_HOME' in os.environ:
                del os.environ['HF_HOME']
            if 'TRANSFORMERS_CACHE' in os.environ:
                del os.environ['TRANSFORMERS_CACHE']
            if 'HF_ENDPOINT' in os.environ:
                del os.environ['HF_ENDPOINT']
                
        except Exception as e:
            print(f"Clear HF config error: {e}")
    
    def _apply_error(self, error: str):
        """应用配置出错"""
        self.apply_status.configure(text=f"配置失败: {error}", text_color=COLOR_ERROR)
        self.apply_btn.configure(state="normal")
        self.progress_bar.set(0)
        self.progress_bar.pack_forget()
    
    def _finish_apply(self, git: str, pip: str, hf: str):
        """完成应用配置"""
        self.progress_bar.set(1.0)
        
        # 更新状态显示
        self.git_status_label.configure(text=f"Git: {git}")
        self.pip_status_label.configure(text=f"Pip: {pip}")
        self.hf_status_label.configure(text=f"HuggingFace: {hf}")
        
        self.apply_status.configure(
            text="配置已应用！",
            text_color=COLOR_SUCCESS
        )
        
        self.after(1500, lambda: self.apply_status.configure(text=""))
        
        self.apply_btn.configure(state="normal")
        self.progress_bar.set(0)
        self.progress_bar.pack_forget()


def main():
    """主函数"""
    app = MirrorManagerApp()
    app.mainloop()


if __name__ == "__main__":
    main()
