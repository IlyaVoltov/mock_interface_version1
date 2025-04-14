import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import numpy as np
from datetime import datetime

class IndustrialUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Промышленный мониторинг - Уровнемеры v2.0")
        self.root.geometry("1000x700")
        self.root.minsize(800, 600)
        
        # Настройка стилей
        self.setup_styles()
        
        # Главный контейнер
        self.main_frame = ttk.Frame(root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Верхняя панель
        self.create_header()
        
        # Центральная область
        self.create_main_content()
        
        # Нижняя навигация
        self.create_navigation()
        
        # Статус бар
        self.create_status_bar()
        
        # Инициализация данных
        self.simulation_data = []
        self.is_paused = False
        self.update_interval = 1000  # 1 секунда
        self.simulate_data()
        
    def setup_styles(self):
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Цветовая схема
        self.style.configure('.', background='#f0f0f0')
        self.style.configure('TFrame', background='#f0f0f0')
        self.style.configure('TLabel', background='#f0f0f0', font=('Segoe UI', 9))
        self.style.configure('Header.TLabel', font=('Segoe UI', 11, 'bold'))
        self.style.configure('Value.TLabel', font=('Segoe UI', 9, 'bold'))
        self.style.configure('TButton', font=('Segoe UI', 9))
        self.style.configure('Red.TButton', foreground='red')
        self.style.configure('Green.TButton', foreground='green')
        self.style.map('TButton',
                      foreground=[('pressed', 'white'), ('active', 'white')],
                      background=[('pressed', '#0052cc'), ('active', '#0066ff')])
        
    def create_header(self):
        header_frame = ttk.Frame(self.main_frame, style='Header.TFrame')
        header_frame.pack(fill=tk.X, padx=10, pady=(10, 5))
        
        # Логотип и название
        logo_frame = ttk.Frame(header_frame)
        logo_frame.pack(side=tk.LEFT)
        
        ttk.Label(logo_frame, text="ПРОМЫШЛЕННЫЙ МОНИТОРИНГ", 
                 style='Header.TLabel').pack(anchor=tk.W)
        ttk.Label(logo_frame, text="Уровнемер SMART-L 210", 
                 style='Header.TLabel').pack(anchor=tk.W)
        
        # Статус и кнопки
        control_frame = ttk.Frame(header_frame)
        control_frame.pack(side=tk.RIGHT)
        
        # Индикатор состояния
        self.status_indicator = tk.Canvas(control_frame, width=20, height=20, bg='green', 
                                        bd=0, highlightthickness=0)
        self.status_indicator.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Label(control_frame, text="Online", style='Header.TLabel').pack(side=tk.LEFT, padx=(0, 15))
        
        # Кнопки управления
        buttons = [("⚙ Настройки", self.show_settings), 
                  ("📁 Архив", self.show_archive),
                  ("🔄 Обновить", self.refresh_data)]
        
        for text, cmd in buttons:
            ttk.Button(control_frame, text=text, command=cmd).pack(side=tk.LEFT, padx=2)
    
    def create_main_content(self):
        content_frame = ttk.Frame(self.main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Левая панель - показания и управление
        self.create_control_panel(content_frame)
        
        # Правая панель - графики
        self.create_graph_panel(content_frame)
    
    def create_control_panel(self, parent):
        control_frame = ttk.Frame(parent, width=250)
        control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        control_frame.pack_propagate(False)
        
        # Блок текущих показаний
        readings_frame = ttk.LabelFrame(control_frame, text="ТЕКУЩИЕ ПОКАЗАНИЯ", 
                                      style='Header.TLabel')
        readings_frame.pack(fill=tk.X, pady=(0, 10))
        
        readings = [
            ("Модель", "SMART-L 210"),
            ("Версия ПО", "2.1.4"),
            ("Уровень", "3.2 м (60%)"),
            ("Сигнал", "12.5 мА"),
            ("Дистанция", "4.0 м"),
            ("Температура", "45°C"),
            ("Состояние", "Норма")
        ]
        
        for name, value in readings:
            frame = ttk.Frame(readings_frame)
            frame.pack(fill=tk.X, pady=2)
            ttk.Label(frame, text=f"{name}:", width=12, anchor=tk.E).pack(side=tk.LEFT)
            ttk.Label(frame, text=value, style='Value.TLabel').pack(side=tk.LEFT)
        
        # Блок управления
        control_buttons_frame = ttk.LabelFrame(control_frame, text="УПРАВЛЕНИЕ")
        control_buttons_frame.pack(fill=tk.X, pady=5)
        
        buttons = [
            ("Калибровка", self.calibrate),
            ("Тест", self.run_test),
            ("Сброс", self.reset_device)
        ]
        
        for text, cmd in buttons:
            ttk.Button(control_buttons_frame, text=text, command=cmd).pack(fill=tk.X, pady=2)
        
        # Блок настроек графика
        graph_settings_frame = ttk.LabelFrame(control_frame, text="НАСТРОЙКИ ГРАФИКА")
        graph_settings_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(graph_settings_frame, text="Интервал обновления:").pack(anchor=tk.W)
        self.update_speed = ttk.Combobox(graph_settings_frame, 
                                       values=["1 сек", "5 сек", "10 сек", "30 сек", "1 мин"])
        self.update_speed.current(0)
        self.update_speed.pack(fill=tk.X, pady=2)
        self.update_speed.bind("<<ComboboxSelected>>", self.change_update_speed)
        
        ttk.Button(graph_settings_frame, text="Пауза", command=self.toggle_pause,
                  style='Red.TButton').pack(fill=tk.X, pady=2)
    
    def create_graph_panel(self, parent):
        graph_frame = ttk.Frame(parent)
        graph_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Вкладки для разных графиков
        self.notebook = ttk.Notebook(graph_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Вкладка с эхо-кривой
        echo_tab = ttk.Frame(self.notebook)
        self.notebook.add(echo_tab, text="Эхо-кривая")
        
        # Создаем график
        self.fig, self.ax = plt.subplots(figsize=(8, 4), dpi=100)
        self.fig.subplots_adjust(bottom=0.15)
        self.canvas = FigureCanvasTkAgg(self.fig, master=echo_tab)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Панель инструментов для графика
        toolbar = NavigationToolbar2Tk(self.canvas, echo_tab)
        toolbar.update()
        self.canvas._tkcanvas.pack(fill=tk.BOTH, expand=True)
        
        # Вкладка с трендами
        trends_tab = ttk.Frame(self.notebook)
        self.notebook.add(trends_tab, text="Тренды")
        
        # Инициализация данных для графика
        self.x_data = []
        self.y_data = []
        self.update_graph()
    
    def create_navigation(self):
        nav_frame = ttk.Frame(self.main_frame)
        nav_frame.pack(fill=tk.X, padx=10, pady=(5, 0))
        
        tabs = [
            ("Главная", self.show_main),
            ("Настройки", self.show_settings),
            ("Эхо-кривые", self.show_echo),
            ("Диагностика", self.show_diagnostics),
            ("Архив", self.show_archive),
            ("Сервис", self.show_service)
        ]
        
        for text, cmd in tabs:
            ttk.Button(nav_frame, text=text, command=cmd).pack(side=tk.LEFT, padx=2)
    
    def create_status_bar(self):
        status_frame = ttk.Frame(self.main_frame, relief=tk.SUNKEN)
        status_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        self.status_text = tk.StringVar()
        self.status_text.set("Готов к работе")
        
        ttk.Label(status_frame, textvariable=self.status_text, 
                 anchor=tk.W).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Label(status_frame, text=datetime.now().strftime("%d.%m.%Y %H:%M:%S"), 
                 anchor=tk.E).pack(side=tk.RIGHT)
    
    def simulate_data(self):
        if not self.is_paused:
            now = datetime.now()
            self.x_data.append(now)
            
            # Генерация случайных данных с небольшим изменением
            if len(self.y_data) == 0:
                new_value = 5.0
            else:
                last_value = self.y_data[-1]
                new_value = last_value + np.random.uniform(-0.5, 0.5)
                new_value = max(0, min(10, new_value))  # Ограничение 0-10
            
            self.y_data.append(new_value)
            
            # Ограничение количества точек на графике
            if len(self.x_data) > 50:
                self.x_data = self.x_data[-50:]
                self.y_data = self.y_data[-50:]
            
            self.update_graph()
        
        self.root.after(self.update_interval, self.simulate_data)
    
    def update_graph(self):
        if not hasattr(self, 'ax'):
            return
            
        self.ax.clear()
        
        if len(self.x_data) > 0:
            # Преобразуем даты в числовой формат для matplotlib
            dates = plt.dates.date2num(self.x_data)
            self.ax.plot_date(dates, self.y_data, '-', color='#1f77b4')
            
            # Форматирование оси X (дата/время)
            self.ax.xaxis.set_major_formatter(plt.dates.DateFormatter('%H:%M:%S'))
            self.fig.autofmt_xdate()
        
        self.ax.set_ylim(0, 10)
        self.ax.set_xlabel('Время')
        self.ax.set_ylabel('Уровень (м)')
        self.ax.grid(True, linestyle='--', alpha=0.6)
        self.ax.set_title('Эхо-кривая в реальном времени', pad=10)
        
        self.canvas.draw()
    
    def toggle_pause(self):
        self.is_paused = not self.is_paused
        if self.is_paused:
            self.status_text.set("График приостановлен")
        else:
            self.status_text.set("График обновляется")
    
    def change_update_speed(self, event):
        speeds = {
            "1 сек": 1000,
            "5 сек": 5000,
            "10 сек": 10000,
            "30 сек": 30000,
            "1 мин": 60000
        }
        self.update_interval = speeds[self.update_speed.get()]
        self.status_text.set(f"Интервал обновления изменен на {self.update_speed.get()}")
    
    # Методы для кнопок навигации
    def show_main(self):
        self.notebook.select(0)
        self.status_text.set("Главная страница")
    
    def show_settings(self):
        self.notebook.select(0)
        self.status_text.set("Настройки: открытие диалогового окна")
        messagebox.showinfo("Настройки", "Здесь будут настройки прибора")
    
    def show_echo(self):
        self.notebook.select(0)
        self.status_text.set("Просмотр эхо-кривых")
    
    def show_diagnostics(self):
        self.notebook.select(1)
        self.status_text.set("Диагностика прибора")
    
    def show_archive(self):
        self.status_text.set("Архив данных: открытие диалогового окна")
        messagebox.showinfo("Архив", "Здесь будет доступ к архивным данным")
    
    def show_service(self):
        self.status_text.set("Сервисное меню: требуется пароль")
        messagebox.showinfo("Сервис", "Доступ только для авторизованного персонала")
    
    def calibrate(self):
        self.status_text.set("Запуск процедуры калибровки")
        messagebox.showinfo("Калибровка", "Процедура калибровки начата")
    
    def run_test(self):
        self.status_text.set("Выполнение теста устройства")
        messagebox.showinfo("Тест", "Тестирование устройства...")
    
    def reset_device(self):
        if messagebox.askyesno("Сброс", "Вы уверены, что хотите сбросить настройки?"):
            self.status_text.set("Сброс настроек устройства")
            messagebox.showinfo("Сброс", "Настройки сброшены к заводским")
    
    def refresh_data(self):
        self.status_text.set("Обновление данных...")
        self.root.after(1000, lambda: self.status_text.set("Данные обновлены"))

if __name__ == "__main__":
    root = tk.Tk()
    app = IndustrialUI(root)
    root.mainloop()
