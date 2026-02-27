# -*- coding: utf-8 -*-
"""Windows 镜像管理器 - 玻璃 UI 版本"""
import os
import sys
import json
import subprocess
import threading
import time
import urllib.request
import urllib.error
import winreg
import ctypes
import math
import random
from typing import Dict, List, Optional

from PyQt6.QtWidgets import (
    QApplication, QWidget, QPushButton, QComboBox, QMessageBox,
    QVBoxLayout, QHBoxLayout, QLabel, QFrame
)
from PyQt6.QtCore import Qt, QRectF, QTimer, QPointF, pyqtSignal
from PyQt6.QtGui import (
    QPainter, QColor, QLinearGradient, QPen, 
    QPainterPath, QFont, QCursor, QPixmap, QPolygonF
)


# ============ 配色方案 ============
GLASS_BG_TOP = QColor(42, 58, 68, 167)
GLASS_BG_MID = QColor(36, 50, 59, 177)
GLASS_BG_BOTTOM = QColor(30, 42, 50, 187)


# ============ CrackCloseButton ============
class CrackCloseButton(QPushButton):
    """玻璃裂纹关闭按钮 - 点击后锤子敲击"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(40, 40)
        self._is_hover = False
        
        # 颤抖动画
        self._shake_offset = 0
        self._shake_timer = QTimer(self)
        self._shake_timer.timeout.connect(self._animate_shake)
        
        # 锤子敲击动画
        self._hammer_rotation = 0
        self._hammer_animating = False
        self._hammer_timer = QTimer(self)
        self._hammer_timer.timeout.connect(self._animate_hammer)
        
        # 锤子光标
        self._hammer_cursor = self._create_hammer_cursor(0)
        
        # 固定裂纹形状
        random.seed(42)
        self._crack_lines = self._generate_cracks()
    
    def _generate_cracks(self):
        cracks = []
        angles = [15, 50, 95, 140, 185, 220, 265, 310]
        for angle in angles:
            cracks.append({
                'angle': angle + random.randint(-5, 5),
                'length': 10 + random.randint(0, 8),
                'start_offset': random.uniform(0, 3),
                'branch': random.random() > 0.4,
                'branch_angle': random.randint(20, 40),
                'branch_offset': random.randint(-15, 15)
            })
        for _ in range(4):
            cracks.append({
                'angle': random.randint(0, 360),
                'length': 5 + random.randint(0, 5),
                'start_offset': random.uniform(2, 5),
                'branch': False,
                'branch_angle': 0,
                'branch_offset': 0
            })
        return cracks
    
    def _create_hammer_cursor(self, rotation):
        """创建带旋转的锤子光标"""
        pixmap = QPixmap(40, 40)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 中心点旋转
        painter.translate(20, 20)
        painter.rotate(rotation)
        
        # 锤头
        painter.setBrush(QColor(120, 120, 130))
        painter.setPen(QPen(QColor(80, 80, 90), 1))
        painter.drawRect(-10, -15, 20, 12)
        
        # 锤柄
        painter.setBrush(QColor(139, 90, 43))
        painter.drawRect(-3, -3, 6, 20)
        
        painter.end()
        return QCursor(pixmap, 20, 20)
    
    def _animate_shake(self):
        self._shake_offset = random.uniform(-1.5, 1.5)
        self.update()
    
    def _animate_hammer(self):
        """锤子敲击动画"""
        self._hammer_rotation += 12
        if self._hammer_rotation >= 45:
            self._hammer_timer.stop()
            # 敲击完成，触发破碎
            self.clicked.emit()
            # 重置
            self._hammer_rotation = 0
            self._hammer_animating = False
            self.setCursor(self._hammer_cursor)
            return
        
        # 更新光标
        self.setCursor(self._create_hammer_cursor(self._hammer_rotation))
        self.update()
    
    def enterEvent(self, event):
        self._is_hover = True
        self.setCursor(self._hammer_cursor)
        self._shake_timer.start(50)
    
    def leaveEvent(self, event):
        self._is_hover = False
        self.setCursor(Qt.CursorShape.ArrowCursor)
        self._shake_timer.stop()
        self._shake_offset = 0
        self.update()
    
    def mousePressEvent(self, event):
        # 开始锤子旋转动画
        self._hammer_rotation = 0
        self._hammer_animating = True
        self._hammer_timer.start(20)
        # 隐藏裂纹，只显示锤子
        event.accept()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        rect = self.rect()
        cx = rect.center().x() + self._shake_offset
        cy = rect.center().y() + self._shake_offset
        
        # 如果锤子正在动画，不画裂纹
        if self._hammer_animating:
            return
        
        crack_color = QColor(220, 235, 255, 180) if not self._is_hover else QColor(255, 255, 255, 240)
        
        # 中心撞击点
        painter.setBrush(crack_color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPointF(cx, cy), 1.5, 1.5)
        
        # 画裂纹
        for crack in self._crack_lines:
            angle = crack['angle']
            length = crack['length']
            start_off = crack.get('start_offset', 3)
            rad = math.radians(angle)
            
            if self._is_hover:
                rad += math.radians(random.uniform(-2, 2))
            
            x1 = cx + start_off * math.cos(rad)
            y1 = cy + start_off * math.sin(rad)
            x2 = cx + length * math.cos(rad)
            y2 = cy + length * math.sin(rad)
            
            segments = 3
            for s in range(segments):
                t1 = s / segments
                t2 = (s + 1) / segments
                sx = x1 + (x2 - x1) * t1
                sy = y1 + (y2 - y1) * t1
                ex = x1 + (x2 - x1) * t2
                ey = y1 + (y2 - y1) * t2
                
                width = 1.4 - s * 0.5
                alpha = 255 - s * 50
                
                color = QColor(crack_color)
                color.setAlpha(alpha)
                painter.setPen(QPen(color, width))
                painter.drawLine(QPointF(sx, sy), QPointF(ex, ey))
            
            if crack['branch']:
                branch_angle = angle + crack.get('branch_angle', 25) + crack.get('branch_offset', 0)
                if self._is_hover:
                    branch_angle += random.uniform(-5, 5)
                branch_rad = math.radians(branch_angle)
                bx = x2 + 4 * math.cos(branch_rad)
                by = y2 + 4 * math.sin(branch_rad)
                
                branch_color = QColor(crack_color)
                branch_color.setAlpha(130)
                painter.setPen(QPen(branch_color, 0.6))
                painter.drawLine(QPointF(x2, y2), QPointF(bx, by))


# ============ GlassShatterEffect ============
class GlassShatterEffect(QWidget):
    """玻璃破碎效果"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self._fragments = []
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._animate)
        self._callback = None
    
    def start_shatter(self, rect, hide_callback=None, callback=None):
        """开始破碎效果"""
        self.setGeometry(rect)
        self._callback = callback
        self._fragments = []
        
        # 立即隐藏内容
        if hide_callback:
            hide_callback()
        
        # 创建碎片并开始动画
        self._create_fragments()
        self.show()
        self._timer.start(20)
    
    def _animate(self):
        for frag in self._fragments:
            frag['y'] += frag['vy']
            frag['vy'] += 0.6
            frag['rotation'] += frag['rot_speed']
            frag['alpha'] -= 3
        
        self._fragments = [f for f in self._fragments if f['alpha'] > 0]
        
        if not self._fragments:
            self._timer.stop()
            self.hide()
            if self._callback:
                self._callback()
        
        self.update()
    
    def _create_fragments(self):
        w, h = self.width(), self.height()
        for _ in range(35):
            cx = random.randint(0, w)
            cy = random.randint(0, h)
            size = random.randint(25, 70)
            
            points = []
            num_points = random.randint(4, 7)
            for i in range(num_points):
                angle = 2 * math.pi * i / num_points + random.uniform(-0.3, 0.3)
                r = size * random.uniform(0.5, 1.0)
                points.append(QPointF(cx + r * math.cos(angle), cy + r * math.sin(angle)))
            
            self._fragments.append({
                'polygon': QPolygonF(points),
                'x': 0, 'y': 0,
                'vy': random.uniform(3, 8),
                'rotation': 0,
                'rot_speed': random.uniform(-8, 8),
                'alpha': 220,
                'color': QColor(50, 70, 100)
            })
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        for frag in self._fragments:
            painter.save()
            painter.translate(frag['x'], frag['y'])
            painter.rotate(frag['rotation'])
            color = QColor(frag['color'])
            color.setAlpha(frag['alpha'])
            painter.setBrush(color)
            painter.setPen(QPen(QColor(255, 255, 255, frag['alpha'] // 2), 1))
            painter.drawPolygon(frag['polygon'])
            painter.restore()


# ============ GlassButton ============
class GlassButton(QPushButton):
    """玻璃按钮 - 带渐变发光动画"""
    
    def __init__(self, text, primary=False, parent=None):
        super().__init__(text, parent)
        self.setFixedHeight(46)
        self.setMinimumWidth(70)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._primary = primary
        
        # 发光强度 (0-200)
        self._glow = 0
        self._target_glow = 0
        # 状态
        self._is_hover = False
        self._is_pressed = False
        self._is_busy = False
        
        # 确保按钮可以接收事件
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        
        # 允许绘制超出边界
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        
        # 渐变定时器
        self._glow_timer = QTimer(self)
        self._glow_timer.timeout.connect(self._animate_glow)
        self._glow_callback = None
    
    def set_glow_callback(self, callback):
        """设置发光变化回调"""
        self._glow_callback = callback
    
    def _animate_glow(self):
        step = 5
        if self._glow < self._target_glow:
            self._glow = min(self._glow + step, self._target_glow)
        elif self._glow > self._target_glow:
            self._glow = max(self._glow - step, self._target_glow)
        else:
            self._glow_timer.stop()
            return
        # 调用回调
        if self._glow_callback:
            self._glow_callback()
        self.update()
    
    def _set_glow_target(self, target):
        self._target_glow = target
        if not self._glow_timer.isActive():
            self._glow_timer.start(20)
    
    def enterEvent(self, event):
        self._is_hover = True
        self._set_glow_target(80)
    
    def leaveEvent(self, event):
        self._is_hover = False
        if not self._is_busy:
            self._set_glow_target(0)
    
    def mousePressEvent(self, event):
        self._is_pressed = True
        self._is_busy = True
        self._set_glow_target(180)
        super().mousePressEvent(event)
    
    def mouseReleaseEvent(self, event):
        self._is_pressed = False
        super().mouseReleaseEvent(event)
    
    def set_busy(self, busy):
        self._is_busy = busy
        if not busy and not self._is_hover:
            self._set_glow_target(0)
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        rect = self.rect()
        r = 12
        
        # ===== 1. 阴影 =====
        if not self._is_pressed:
            for i in range(3):
                alpha = 35 - i * 10
                if alpha <= 0:
                    break
                shadow_rect = QRectF(
                    rect.x() + 3 + i * 2, rect.y() + 4 + i * 2,
                    rect.width() - 6 - i * 2, rect.height() - 6 - i * 2
                )
                shadow = QPainterPath()
                shadow.addRoundedRect(shadow_rect, r, r)
                painter.fillPath(shadow, QColor(0, 0, 0, alpha))
        
        # ===== 2. 按钮主体 =====
        body = QRectF(rect).adjusted(0, 0, 0, -2 if not self._is_pressed else 0)
        gradient = QLinearGradient(0, 0, 0, body.height())
        
        # 根据状态和发光强度计算颜色
        glow_factor = self._glow / 200
        
        if self._primary:
            if self._is_pressed or self._is_busy:
                r1 = int(90 + 80 * glow_factor)
                g1 = int(180 + 70 * glow_factor)
                b1 = int(240 + 50 * glow_factor)
            elif self._is_hover:
                r1 = int(80 + 60 * glow_factor)
                g1 = int(165 + 65 * glow_factor)
                b1 = int(225 + 55 * glow_factor)
            else:
                r1 = int(70 + 50 * glow_factor)
                g1 = int(150 + 60 * glow_factor)
                b1 = int(210 + 45 * glow_factor)
            gradient.setColorAt(0, QColor(min(255, r1), min(255, g1), min(255, b1)))
            gradient.setColorAt(0.3, QColor(min(255, r1-15), min(255, g1-15), min(255, b1-10)))
            gradient.setColorAt(1, QColor(45, 110, 165))
        else:
            if self._is_pressed or self._is_busy:
                r1 = int(80 + 60 * glow_factor)
                g1 = int(100 + 70 * glow_factor)
                b1 = int(150 + 60 * glow_factor)
            elif self._is_hover:
                r1 = int(70 + 50 * glow_factor)
                g1 = int(90 + 60 * glow_factor)
                b1 = int(135 + 55 * glow_factor)
            else:
                r1 = int(60 + 40 * glow_factor)
                g1 = int(75 + 50 * glow_factor)
                b1 = int(110 + 50 * glow_factor)
            gradient.setColorAt(0, QColor(min(255, r1), min(255, g1), min(255, b1)))
            gradient.setColorAt(0.3, QColor(min(255, r1-10), min(255, g1-10), min(255, b1-15)))
            gradient.setColorAt(1, QColor(40, 50, 75))
        
        painter.setBrush(gradient)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(body, r, r)
        
        # ===== 3. 高光 =====
        h_alpha = min(200, 100 + int(self._glow * 0.5))
        highlight = QRectF(body.x() + 3, body.y() + 2, body.width() - 6, body.height() * 0.4)
        h_grad = QLinearGradient(0, highlight.y(), 0, highlight.bottom())
        h_grad.setColorAt(0, QColor(255, 255, 255, h_alpha))
        h_grad.setColorAt(0.5, QColor(255, 255, 255, 50))
        h_grad.setColorAt(1, QColor(255, 255, 255, 0))
        painter.setBrush(h_grad)
        painter.drawRoundedRect(highlight, r-2, r-2)
        
        # ===== 4. 边框 =====
        border_alpha = min(200, 80 + int(self._glow * 0.6))
        painter.setPen(QPen(QColor(255, 255, 255, border_alpha), 1.5))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(body, r, r)
        
        painter.setPen(QPen(QColor(0, 0, 0, 40), 1))
        painter.drawRoundedRect(body.adjusted(1.5, 1.5, -1.5, -1.5), r-1, r-1)
        
        # ===== 5. 底部厚度 =====
        thickness = QRectF(body.x() + 8, body.bottom() - 5, body.width() - 16, 3)
        t_grad = QLinearGradient(0, thickness.y(), 0, thickness.bottom())
        t_grad.setColorAt(0, QColor(255, 255, 255, 0))
        t_grad.setColorAt(1, QColor(255, 255, 255, 50))
        painter.setBrush(t_grad)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(thickness, 1, 1)
        
        # ===== 6. 文字 =====
        painter.setPen(QColor(255, 255, 255))
        painter.setFont(QFont("Microsoft YaHei", 11, QFont.Weight.Bold))
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, self.text())


# ============ GlassComboBox ============
class GlassComboBox(QComboBox):
    """玻璃下拉框 - 带发光动画"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(46)
        self.setMinimumWidth(180)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # 显式设置字体
        font = QFont("Microsoft YaHei", 13)
        self.setFont(font)
        
        # 发光
        self._glow = 0
        self._target_glow = 0
        self._is_hover = False
        
        self._glow_timer = QTimer(self)
        self._glow_timer.timeout.connect(self._animate_glow)
        self._glow_callback = None
        
        # 样式表
        self.setStyleSheet("""
            QComboBox {
                background: transparent;
                border: none;
                color: white;
                font-size: 13px;
                font-family: 'Microsoft YaHei';
                padding-left: 16px;
                padding-right: 35px;
            }
            QComboBox::drop-down { border: none; width: 35px; }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid rgba(255,255,255,200);
                margin-right: 12px;
            }
            QComboBox QAbstractItemView {
                background-color: rgba(35, 45, 65, 250);
                border: 1px solid rgba(255, 255, 255, 50);
                border-radius: 12px;
                selection-background-color: rgba(70, 110, 170, 200);
                color: white;
                outline: none;
                padding: 6px;
                font-size: 13px;
                font-family: 'Microsoft YaHei';
            }
            QComboBox QAbstractItemView::item {
                height: 34px;
                border-radius: 8px;
                padding-left: 12px;
            }
            QComboBox QAbstractItemView::item:hover {
                background-color: rgba(60, 90, 140, 180);
            }
        """)
    
    def set_glow_callback(self, callback):
        """设置发光变化回调"""
        self._glow_callback = callback
    
    def _animate_glow(self):
        step = 5
        if self._glow < self._target_glow:
            self._glow = min(self._glow + step, self._target_glow)
        elif self._glow > self._target_glow:
            self._glow = max(self._glow - step, self._target_glow)
        else:
            self._glow_timer.stop()
            return
        # 调用回调
        if self._glow_callback:
            self._glow_callback()
        self.update()
    
    def _set_glow_target(self, target):
        self._target_glow = target
        if not self._glow_timer.isActive():
            self._glow_timer.start(20)
    
    def enterEvent(self, event):
        self._is_hover = True
        self._set_glow_target(80)
    
    def leaveEvent(self, event):
        self._is_hover = False
        self._set_glow_target(0)
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        rect = self.rect()
        r = 12
        
        # 阴影
        shadow = QPainterPath()
        shadow.addRoundedRect(QRectF(rect).adjusted(1, 2, -1, 0), r, r)
        painter.fillPath(shadow, QColor(0, 0, 0, 30))
        
        # 背景
        body = QRectF(rect).adjusted(1, 1, -1, -1)
        gradient = QLinearGradient(0, 0, 0, rect.height())
        
        glow_factor = self._glow / 200
        r1 = int(50 + 35 * glow_factor)
        g1 = int(60 + 45 * glow_factor)
        b1 = int(90 + 50 * glow_factor)
        gradient.setColorAt(0, QColor(r1, g1, b1))
        gradient.setColorAt(1, QColor(35, 45, 70))
        
        painter.setBrush(gradient)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(body, r, r)
        
        # 高光
        highlight = QRectF(body.x() + 3, body.y() + 2, body.width() - 6, body.height() * 0.3)
        h_grad = QLinearGradient(0, highlight.y(), 0, highlight.bottom())
        h_alpha = min(150, 60 + int(self._glow * 0.4))
        h_grad.setColorAt(0, QColor(255, 255, 255, h_alpha))
        h_grad.setColorAt(1, QColor(255, 255, 255, 0))
        painter.setBrush(h_grad)
        painter.drawRoundedRect(highlight, r-2, r-2)
        
        # 边框
        border_alpha = min(150, 50 + int(self._glow * 0.5))
        painter.setPen(QPen(QColor(255, 255, 255, border_alpha), 1))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(body, r, r)
        
        super().paintEvent(event)


# ============ MirrorCard ============
class MirrorCard(QFrame):
    """镜像卡片"""
    
    def __init__(self, title, mirror_options, parent=None):
        super().__init__(parent)
        self.setFixedHeight(90)
        self.mirror_options = mirror_options
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(8)
        
        title_layout = QHBoxLayout()
        
        label = QLabel(title)
        label.setStyleSheet("color: rgba(255,255,255,230); font-size: 14px; font-weight: bold; font-family: 'Microsoft YaHei';")
        title_layout.addWidget(label)
        title_layout.addStretch()
        
        self.combo = GlassComboBox()
        # 动态添加镜像选项
        names = [o["name"] for o in mirror_options]
        self.combo.addItems(names)
        self.combo.set_glow_callback(self.update)
        title_layout.addWidget(self.combo)
        
        self.test_btn = GlassButton("测试")
        self.test_btn.setFixedWidth(72)
        self.test_btn.set_glow_callback(self.update)
        title_layout.addWidget(self.test_btn)
        
        layout.addLayout(title_layout)
        
        self.status = QLabel("状态：未测试")
        self.status.setStyleSheet("color: rgba(255,255,255,140); font-size: 11px;")
        layout.addWidget(self.status)
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        rect = self.rect()
        r = 14
        
        # 凹陷背景
        path = QPainterPath()
        path.addRoundedRect(QRectF(rect), r, r)
        
        gradient = QLinearGradient(0, 0, 0, rect.height())
        gradient.setColorAt(0, QColor(0, 0, 0, 40))
        gradient.setColorAt(0.5, QColor(20, 25, 35, 50))
        gradient.setColorAt(1, QColor(0, 0, 0, 50))
        
        painter.fillPath(path, gradient)
        
        # 边框
        painter.setPen(QPen(QColor(255, 255, 255, 20), 1))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(QRectF(rect), r, r)
        
        # 在背景之后画子控件的发光效果
        self._draw_child_glows(painter)
    
    def _draw_child_glows(self, painter):
        """绘制子控件的发光效果"""
        # 按钮发光
        if hasattr(self, 'test_btn') and self.test_btn._glow > 0:
            btn = self.test_btn
            glow = btn._glow
            btn_rect = btn.geometry()
            
            for layer in range(5):
                expand = (5 - layer) * 5
                alpha = int(glow * 0.12 * (layer + 1) / 5)
                glow_rect = btn_rect.adjusted(-expand, -expand, expand, expand)
                
                if btn._primary:
                    glow_color = QColor(100, 180, 255, alpha)
                else:
                    glow_color = QColor(140, 170, 210, alpha)
                
                painter.setBrush(glow_color)
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawRoundedRect(QRectF(glow_rect), 15 + expand * 1.5, 15 + expand * 1.5)
        
        # 下拉框发光
        if hasattr(self, 'combo') and self.combo._glow > 0:
            combo = self.combo
            glow = combo._glow
            combo_rect = combo.geometry()
            
            for layer in range(5):
                expand = (5 - layer) * 4
                alpha = int(glow * 0.10 * (layer + 1) / 5)
                glow_rect = combo_rect.adjusted(-expand, -expand, expand, expand)
                
                painter.setBrush(QColor(130, 165, 200, alpha))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawRoundedRect(QRectF(glow_rect), 15 + expand * 1.5, 15 + expand * 1.5)


# ============ MirrorManagerApp ============
class MirrorManagerApp(QWidget):
    """玻璃窗口镜像管理器"""
    
    # 信号：用于跨线程通信（从工作线程发回主线程）
    test_done_signal = pyqtSignal(object, object, str, bool)  # card, btn, text, success
    apply_done_signal = pyqtSignal(str, str, str)  # git, pip, hf
    apply_failed_signal = pyqtSignal(str)  # error_msg
    status_update_signal = pyqtSignal(str)  # status text
    
    # 类常量
    MARGIN = 50
    CORNER_RADIUS = 24
    
    def __init__(self, mirrors: Dict):
        super().__init__()
        self.mirrors = mirrors
        self.testing = {"git": False, "pip": False, "hf": False}
        
        # 窗口设置
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.NoDropShadowWindowHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAutoFillBackground(False)
        self.setStyleSheet("background: transparent;")
        self.setGeometry(300, 100, 580, 610)
        
        self._drag_pos = None
        self._content_visible = True
        
        self._init_ui()
        
        # 连接信号 - 用于跨线程通信
        self.test_done_signal.connect(self._on_test_done)
        self.apply_done_signal.connect(self._on_apply_done)
        self.apply_failed_signal.connect(self._on_apply_failed)
        self.status_update_signal.connect(self._on_status_update)
        
        # 延迟加载配置 - 确保在事件循环启动后执行
        # 否则 Qt UI 更新不会正确渲染
        QTimer.singleShot(0, self._load_current_config)
    def _get_glass_rect(self):
        return self.rect().adjusted(self.MARGIN, self.MARGIN, -self.MARGIN, -self.MARGIN)
    
    def _init_ui(self):
        glass = self._get_glass_rect()
        
        container = QWidget(self)
        container.setGeometry(glass.x() + 20, glass.y() + 20, 
                             glass.width() - 40, glass.height() - 40)
        container.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        container.setAutoFillBackground(False)
        container.setStyleSheet("background: transparent;")
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(14)
        
        # 标题栏
        title_bar = QHBoxLayout()
        
        title = QLabel("镜像管理器")
        title.setStyleSheet("color: white; font-size: 22px; font-weight: bold; font-family: 'Microsoft YaHei';")
        title_bar.addWidget(title)
        title_bar.addStretch()
        
        # 裂纹关闭按钮
        self.close_btn = CrackCloseButton()
        self.close_btn.clicked.connect(self._on_close_clicked)
        title_bar.addWidget(self.close_btn)
        
        self._shatter_effect = None
        
        layout.addLayout(title_bar)
        
        # 分隔线
        line1 = QFrame()
        line1.setFixedHeight(1)
        line1.setStyleSheet("background: rgba(255,255,255,50);")
        layout.addWidget(line1)
        
        # 镜像卡片 - 使用真实数据
        self.git_card = MirrorCard("Git 镜像", self.mirrors.get("git", []))
        layout.addWidget(self.git_card)
        
        self.pip_card = MirrorCard("Pip 镜像", self.mirrors.get("pip", []))
        layout.addWidget(self.pip_card)
        
        self.hf_card = MirrorCard("HuggingFace", self.mirrors.get("hf", []))
        layout.addWidget(self.hf_card)
        
        line2 = QFrame()
        line2.setFixedHeight(1)
        line2.setStyleSheet("background: rgba(255,255,255,40);")
        layout.addWidget(line2)
        
        self.apply_btn = GlassButton("应 用 配 置", primary=True)
        self.apply_btn.setFixedHeight(50)
        layout.addWidget(self.apply_btn)
        
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #50DCA0; font-size: 12px;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)
        
        # 信号连接 - 真实业务逻辑
        self.git_card.test_btn.clicked.connect(lambda: self._test_mirror("git"))
        self.pip_card.test_btn.clicked.connect(lambda: self._test_mirror("pip"))
        self.hf_card.test_btn.clicked.connect(lambda: self._test_mirror("hf"))
        self.apply_btn.clicked.connect(self._apply_config)
    
    # ========== 配置检测 ==========
    
    def _load_current_config(self):
        """加载当前配置状态"""
        # Git
        git_url = self._get_git_url()
        if git_url:
            name = self._find_mirror_name("git", git_url)
            self.git_card.status.setText(f"Git: {name}")
            self.git_card.status.setStyleSheet("color: #50DCA0; font-size: 11px;")
            self._set_combo_value(self.git_card.combo, name)
        
        # Pip
        pip_url = self._get_pip_url()
        if pip_url:
            name = self._find_mirror_name("pip", pip_url)
            self.pip_card.status.setText(f"Pip: {name}")
            self.pip_card.status.setStyleSheet("color: #50DCA0; font-size: 11px;")
            self._set_combo_value(self.pip_card.combo, name)
        
        # HuggingFace
        hf_url = self._get_hf_url()
        if hf_url:
            name = self._find_mirror_name("hf", hf_url)
            self.hf_card.status.setText(f"HuggingFace: {name}")
            self.hf_card.status.setStyleSheet("color: #50DCA0; font-size: 11px;")
            self._set_combo_value(self.hf_card.combo, name)
    
    def _set_combo_value(self, combo, value):
        """设置下拉框值"""
        index = combo.findText(value)
        if index >= 0:
            combo.setCurrentIndex(index)
    
    def _get_git_url(self) -> Optional[str]:
        """获取 Git 当前配置的镜像 URL"""
        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
            result = subprocess.run(
                ['git', 'config', '--global', '--get-regexp', r'url\..*\.insteadOf'],
                capture_output=True,
                text=True,
                timeout=5,
                startupinfo=startupinfo,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            if result.returncode == 0 and result.stdout.strip():
                last_url = None
                for line in result.stdout.strip().split('\n'):
                    if line.startswith('url."'):
                        start = line.find('url."') + 5
                        if start >= 5:
                            end = line.find('"', start)
                            if end > start:
                                url = line[start:end]
                                last_url = url.rstrip('/')
                
                return last_url
        except Exception:
            pass
        return None
    
    def _get_pip_url(self) -> Optional[str]:
        """获取 Pip 当前配置的镜像 URL"""
        # 优先从环境变量读取
        url = os.environ.get('PIP_INDEX_URL')
        if url:
            return url.rstrip('/')
        
        # 从注册表读取（用户环境变量）
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                'Environment',
                0,
                winreg.KEY_READ
            )
            try:
                url, _ = winreg.QueryValueEx(key, 'PIP_INDEX_URL')
                return url.rstrip('/')
            except FileNotFoundError:
                pass
            finally:
                winreg.CloseKey(key)
        except Exception:
            pass
        
        # 最后检查配置文件（向后兼容）
        config_files = [
            os.path.join(os.environ.get('APPDATA', ''), 'pip', 'pip.ini'),
            os.path.expanduser('~/.pip/pip.conf'),
        ]
        
        for config_file in config_files:
            if os.path.exists(config_file):
                try:
                    with open(config_file, 'r', encoding='utf-8') as f:
                        for line in f:
                            line = line.strip()
                            if line.startswith('index-url') or line.startswith('mirror'):
                                if '=' in line:
                                    url = line.split('=', 1)[1].strip()
                                    return url.rstrip('/')
                except Exception:
                    pass
        
        return None
    
    def _get_hf_url(self) -> Optional[str]:
        """获取 HuggingFace 当前配置的镜像 URL"""
        
        # 先从当前进程环境变量读取
        url = os.environ.get('HF_ENDPOINT') or os.environ.get('HF_HUB_ENDPOINT')
        if url:
            return url
        
        # 如果进程环境变量没有，从注册表读取（用户环境变量）
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                'Environment',
                0,
                winreg.KEY_READ
            )
            try:
                url, _ = winreg.QueryValueEx(key, 'HF_ENDPOINT')
                return url
            except FileNotFoundError:
                pass
            try:
                url, _ = winreg.QueryValueEx(key, 'HF_HUB_ENDPOINT')
                return url
            except FileNotFoundError:
                pass
            finally:
                winreg.CloseKey(key)
        except Exception:
            pass
        
        return None
    
    def _find_mirror_name(self, mtype: str, url: str) -> str:
        """从 JSON 配置中查找镜像名称"""
        url = url.rstrip('/')
        for opt in self.mirrors.get(mtype, []):
            if opt.get("url", "").rstrip('/') == url:
                return opt["name"]
        # 找不到匹配，返回 URL 域名
        return url.split('/')[-1] or url
    
    # ========== 测试镜像 ==========
    
    def _test_mirror(self, mtype: str):
        """测试镜像连接"""
        if self.testing.get(mtype):
            return
        self.testing[mtype] = True
        
        card = getattr(self, f"{mtype}_card")
        btn = card.test_btn
        options = self.mirrors.get(mtype, [])
        
        name = card.combo.currentText()
        url = next((o["url"] for o in options if o["name"] == name), "")
        
        # 原始或无 URL
        if not url or name == "原始":
            btn.set_busy(False)
            card.status.setText("状态：原始（无镜像）")
            card.status.setStyleSheet("color: rgba(255,255,255,140); font-size: 11px;")
            self.testing[mtype] = False
            return
        
        # 测试中
        btn.set_busy(True)
        card.status.setText("状态：测试中...")
        card.status.setStyleSheet("color: #80B0E0; font-size: 11px;")
        
        # 后台测试
        thread = threading.Thread(
            target=self._test_thread,
            args=(card, btn, url, name, mtype)
        )
        thread.daemon = True
        thread.start()
    
    def _test_thread(self, card, btn, url, name, mtype):
        """测试线程"""
        start = time.time()
        try:
            req = urllib.request.Request(
                url,
                method="HEAD",
                headers={"User-Agent": "MirrorManager/1.0"}
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                ms = int((time.time() - start) * 1000)
                # 使用信号而非QTimer - 线程安全
                self.test_done_signal.emit(card, btn, f"{name} - {ms}ms", True)
        except Exception as e:
            self.test_done_signal.emit(card, btn, f"连接失败 - {str(e)}", False)
    
    def _on_test_done(self, card, btn, text, success):
        """测试完成（信号槽 - 在主线程执行）"""
        btn.set_busy(False)
        if success:
            card.status.setText(f"状态：{text}")
            card.status.setStyleSheet("color: #50DCA0; font-size: 11px;")
        else:
            card.status.setText(f"状态：{text}")
            card.status.setStyleSheet("color: #E74C3C; font-size: 11px;")
        
        mtype = "git" if card == self.git_card else ("pip" if card == self.pip_card else "hf")
        self.testing[mtype] = False
    
    # ========== 应用配置 ==========
    
    def _apply_config(self):
        """应用配置"""
        git = self.git_card.combo.currentText()
        pip = self.pip_card.combo.currentText()
        hf = self.hf_card.combo.currentText()
        
        self.apply_btn.set_busy(True)
        self.status_label.setText("正在应用...")
        
        thread = threading.Thread(
            target=self._apply_thread,
            args=(git, pip, hf)
        )
        thread.daemon = True
        thread.start()
    
    def _apply_thread(self, git: str, pip: str, hf: str):
        """应用配置线程"""
        try:
            self.status_update_signal.emit("正在清理旧配置...")
            
            self._clear_git_config()
            self._clear_pip_config()
            self._clear_hf_config()
            
            self.status_update_signal.emit("正在配置 Git...")
            
            # Git
            git_url = self._get_mirror_url("git", git)
            if git_url:
                self._set_git_config(git_url)
            
            self.status_update_signal.emit("正在配置 Pip...")
            
            # Pip
            pip_url = self._get_mirror_url("pip", pip)
            if pip_url:
                self._set_pip_config(pip_url)
            
            self.status_update_signal.emit("正在配置 HuggingFace...")
            
            # HuggingFace
            hf_url = self._get_mirror_url("hf", hf)
            if hf_url:
                self._set_hf_config(hf_url)
            
            # 检测系统级配置
            system_warnings = []
            if self._detect_system_pip_config():
                system_warnings.append("Pip")
            if self._detect_system_hf_config():
                system_warnings.append("HuggingFace")
            
            # 如果有系统级配置但无管理员权限，记录警告
            if system_warnings and not self._is_admin():
                # 环境变量优先级最高，可以覆盖系统级配置
                # 只在状态中提示，不阻止操作
                warning_msg = f"检测到系统级配置 ({', '.join(system_warnings)})，环境变量将优先生效"
                print(warning_msg)
            
            # 完成
            self.apply_done_signal.emit(git, pip, hf)
        except Exception as e:
            self.apply_failed_signal.emit(str(e))
    
    def _get_mirror_url(self, mtype: str, name: str) -> Optional[str]:
        """获取镜像 URL"""
        for opt in self.mirrors.get(mtype, []):
            if opt["name"] == name:
                return opt.get("url", "")
        return ""
    
    def _is_admin(self) -> bool:
        """检测是否有管理员权限"""
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except Exception:
            return False
    
    def _detect_system_pip_config(self) -> bool:
        """检测是否有系统级 Pip 配置"""
        system_config = os.path.join(os.environ.get('PROGRAMDATA', ''), 'pip', 'pip.ini')
        return os.path.exists(system_config)
    
    def _detect_system_hf_config(self) -> bool:
        """检测是否有系统级 HF 配置"""
        try:
            key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r'SYSTEM\CurrentControlSet\Control\Session Manager\Environment',
                0,
                winreg.KEY_READ
            )
            try:
                winreg.QueryValueEx(key, 'HF_ENDPOINT')
                winreg.CloseKey(key)
                return True
            except FileNotFoundError:
                winreg.CloseKey(key)
                return False
        except Exception:
            return False
    
    def _set_git_config(self, url: str):
        """设置 Git 镜像"""
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        
        subprocess.run(
            ['git', 'config', '--global', f'url."{url}".insteadOf', 'https://github.com'],
            capture_output=True,
            timeout=10,
            startupinfo=startupinfo,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        subprocess.run(
            ['git', 'config', '--global', f'url."{url}".insteadOf', 'https://github.com/'],
            capture_output=True,
            timeout=10,
            startupinfo=startupinfo,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
    
    def _clear_git_config(self):
        """清理 Git 配置"""
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        
        result = subprocess.run(
            ['git', 'config', '--global', '--list'],
            capture_output=True,
            text=True,
            timeout=10,
            startupinfo=startupinfo,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        
        if result.returncode == 0:
            for line in result.stdout.strip().split('\n'):
                if line.startswith('url.'):
                    parts = line.split('=', 1)
                    if len(parts) >= 1:
                        key = parts[0]
                        subprocess.run(
                            ['git', 'config', '--global', '--unset-all', key],
                            capture_output=True,
                            timeout=10,
                            startupinfo=startupinfo,
                            creationflags=subprocess.CREATE_NO_WINDOW
                        )
    
    def _set_pip_config(self, url: str):
        """设置 Pip 镜像 - 使用环境变量 PIP_INDEX_URL"""
        # 设置当前进程环境变量（立即生效）
        os.environ['PIP_INDEX_URL'] = url
        
        # 写入用户环境变量（重启持久）
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                'Environment',
                0,
                winreg.KEY_SET_VALUE
            )
            winreg.SetValueEx(key, 'PIP_INDEX_URL', 0, winreg.REG_SZ, url)
            winreg.CloseKey(key)
            
            # 通知系统环境变量已更改
            ctypes.windll.user32.SendMessageTimeoutW(
                0xFFFF,  # HWND_BROADCAST
                0x001A,  # WM_SETTINGCHANGE
                0,
                'Environment',
                0,
                5000,
                None
            )
        except Exception as e:
            print(f"写入 Pip 环境变量失败: {e}")
    
    def _clear_pip_config(self):
        """清理 Pip 配置 - 清理所有可能的位置"""
        # 清理环境变量
        os.environ.pop('PIP_INDEX_URL', None)
        
        # 清理注册表中的环境变量
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                'Environment',
                0,
                winreg.KEY_SET_VALUE
            )
            try:
                winreg.DeleteValue(key, 'PIP_INDEX_URL')
            except FileNotFoundError:
                pass
            winreg.CloseKey(key)
        except Exception:
            pass
        
        # 清理所有可能的配置文件
        config_files = [
            os.path.expanduser('~/.pip/pip.conf'),  # 遗留文件
            os.path.join(os.environ.get('APPDATA', ''), 'pip', 'pip.ini'),  # 用户级
            os.path.join(os.environ.get('LOCALAPPDATA', ''), 'pip', 'pip.ini'),
        ]
        
        for config_file in config_files:
            if os.path.exists(config_file):
                try:
                    os.remove(config_file)
                except Exception as e:
                    print(f"清理失败 {config_file}: {e}")
    
    def _set_hf_config(self, url: str):
        """设置 HuggingFace 配置 - 写入系统环境变量"""
        # 设置当前进程环境变量（立即生效）
        os.environ['HF_ENDPOINT'] = url
        os.environ['HF_HUB_ENDPOINT'] = url
        
        # 写入用户环境变量（重启持久）
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                'Environment',
                0,
                winreg.KEY_SET_VALUE
            )
            winreg.SetValueEx(key, 'HF_ENDPOINT', 0, winreg.REG_SZ, url)
            winreg.SetValueEx(key, 'HF_HUB_ENDPOINT', 0, winreg.REG_SZ, url)
            winreg.CloseKey(key)
            
            # 通知系统环境变量已更改
            ctypes.windll.user32.SendMessageTimeoutW(
                0xFFFF,  # HWND_BROADCAST
                0x001A,  # WM_SETTINGCHANGE
                0,
                'Environment',
                0,
                5000,
                None
            )
        except Exception as e:
            print(f"写入系统环境变量失败: {e}")
    
    def _clear_hf_config(self):
        """清理 HuggingFace 配置"""
        os.environ.pop('HF_ENDPOINT', None)
        os.environ.pop('HF_HUB_ENDPOINT', None)
        
        # 删除用户环境变量
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                'Environment',
                0,
                winreg.KEY_SET_VALUE
            )
            try:
                winreg.DeleteValue(key, 'HF_ENDPOINT')
            except FileNotFoundError:
                pass
            try:
                winreg.DeleteValue(key, 'HF_HUB_ENDPOINT')
            except FileNotFoundError:
                pass
            winreg.CloseKey(key)
            
            # 通知系统环境变量已更改
            ctypes.windll.user32.SendMessageTimeoutW(
                0xFFFF,
                0x001A,
                0,
                'Environment',
                0,
                5000,
                None
            )
        except Exception as e:
            print(f"删除系统环境变量失败: {e}")
    
    def _on_apply_done(self, git: str, pip: str, hf: str):
        """应用完成（信号槽 - 在主线程执行）"""
        self.apply_btn.set_busy(False)
        
        self.status_label.setText("✓ 配置已应用！")
        
        self.git_card.status.setText(f"Git: {git}")
        self.git_card.status.setStyleSheet("color: #50DCA0; font-size: 11px;")
        
        self.pip_card.status.setText(f"Pip: {pip}")
        self.pip_card.status.setStyleSheet("color: #50DCA0; font-size: 11px;")
        
        self.hf_card.status.setText(f"HF: {hf}")
        self.hf_card.status.setStyleSheet("color: #50DCA0; font-size: 11px;")
        
        QTimer.singleShot(2000, lambda: self.status_label.setText(""))
    
    def _on_apply_failed(self, error_msg):
        """应用失败（信号槽 - 在主线程执行）"""
        self.apply_btn.set_busy(False)
        self.status_label.setText(f"失败：{error_msg}")
        self.status_label.setStyleSheet("color: #E74C3C; font-size: 12px;")
    
    def _on_status_update(self, text):
        """状态更新（信号槽 - 在主线程执行）"""
        self.status_label.setText(text)
    
    def _apply_failed(self, error_msg):
        """应用失败"""
        self.apply_btn.set_busy(False)
        self.status_label.setText(f"失败：{error_msg}")
        self.status_label.setStyleSheet("color: #E74C3C; font-size: 12px;")
    
    # ========== 窗口事件 ==========
    
    def paintEvent(self, event):
        # 如果内容已隐藏，不画玻璃
        if not self._content_visible:
            return
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 假玻璃窗口的矩形
        glass = self._get_glass_rect()
        r = self.CORNER_RADIUS
        
        # ===== 1. 阴影（整体向右下偏移，左上无阴影） =====
        for i in range(6):
            alpha = 30 - i * 5
            if alpha <= 0:
                break
            
            # 阴影整体向右下偏移
            offset = i * 2
            shadow_rect = QRectF(
                glass.x() + offset + 4,
                glass.y() + offset + 4,
                glass.width(),
                glass.height()
            )
            shadow_path = QPainterPath()
            shadow_path.addRoundedRect(shadow_rect, r, r)
            painter.fillPath(shadow_path, QColor(0, 0, 0, alpha))
        
        # ===== 2. 假玻璃主体 =====
        glass_path = QPainterPath()
        glass_path.addRoundedRect(QRectF(glass), r, r)
        
        # 渐变背景
        gradient = QLinearGradient(0, glass.y(), 0, glass.bottom())
        gradient.setColorAt(0, GLASS_BG_TOP)
        gradient.setColorAt(0.5, GLASS_BG_MID)
        gradient.setColorAt(1, GLASS_BG_BOTTOM)
        
        painter.fillPath(glass_path, gradient)
        
        # ===== 3. 左上角高光（光源方向） =====
        # 顶部横向高光条
        highlight = QRectF(glass.x() + 6, glass.y() + 5, glass.width() - 12, 35)
        h_grad = QLinearGradient(0, highlight.y(), 0, highlight.bottom())
        h_grad.setColorAt(0, QColor(255, 255, 255, 60))
        h_grad.setColorAt(1, QColor(255, 255, 255, 0))
        
        h_path = QPainterPath()
        h_path.addRoundedRect(highlight, r-4, r-4)
        painter.fillPath(h_path, h_grad)
        
        # 左上角边缘高光（向内缩进，不贴边）
        corner_highlight = QPainterPath()
        corner_highlight.moveTo(glass.x() + r + 2, glass.y() + 4)
        corner_highlight.lineTo(glass.x() + 4, glass.y() + 4)
        corner_highlight.lineTo(glass.x() + 4, glass.y() + r + 2)
        corner_highlight.arcTo(glass.x() + 4, glass.y() + 4, (r-4)*2, (r-4)*2, 180, -90)
        painter.fillPath(corner_highlight, QColor(255, 255, 255, 25))
        
        # ===== 4. 边框 =====
        painter.setPen(QPen(QColor(255, 255, 255, 70), 1.5))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(QRectF(glass), r, r)
        
        # 内边框
        painter.setPen(QPen(QColor(0, 0, 0, 40), 1))
        painter.drawRoundedRect(QRectF(glass).adjusted(1.5, 1.5, -1.5, -1.5), r-1, r-1)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
    
    def mouseMoveEvent(self, event):
        if self._drag_pos:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
    
    def mouseReleaseEvent(self, event):
        self._drag_pos = None
    
    def _on_close_clicked(self):
        """点击裂纹关闭按钮 - 触发破碎效果"""
        self._shatter_effect = GlassShatterEffect()
        self._shatter_effect.start_shatter(
            self.geometry(),
            hide_callback=self._hide_content,
            callback=self.close
        )
    
    def _hide_content(self):
        """隐藏窗口内所有内容"""
        # 隐藏玻璃背景
        self._content_visible = False
        # 隐藏所有子控件
        for child in self.findChildren(QWidget):
            if child != self._shatter_effect:
                child.hide()
        # 重绘
        self.update()


# ============ main ============
def main():
    """主函数"""
    # 先创建 QApplication（MessageBox 需要它）
    app = QApplication(sys.argv)
    
    # 确定配置文件路径
    if getattr(sys, 'frozen', False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    
    config_path = os.path.join(base_dir, "mirrors.json")
    
    # 检查配置文件
    if not os.path.exists(config_path):
        msg = QMessageBox()
        msg.setWindowTitle("错误")
        msg.setText(f"找不到配置文件 mirrors.json！\n\n路径：{config_path}\n\n请将 mirrors.json 放在程序同目录下。")
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.exec()
        sys.exit(1)
    
    # 读取配置
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            mirrors = json.load(f)
    except Exception as e:
        msg = QMessageBox()
        msg.setWindowTitle("错误")
        msg.setText(f"读取配置文件失败！\n\n{str(e)}")
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.exec()
        sys.exit(1)
    
    # 设置字体
    default_font = QFont("Microsoft YaHei", 13)
    app.setFont(default_font)
    
    window = MirrorManagerApp(mirrors)
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
