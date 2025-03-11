import shutil
import sys
import os
import platform
import pandas as pd
from PySide6.QtCore import QUrl, QThread, QObject, Signal, Qt, QTimer, QCoreApplication, QSize, QFile
from PySide6.QtGui import QDesktopServices, QFont, QColor, QIcon, QAction, QPalette, QGuiApplication, QMovie
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import (QApplication, QMainWindow, QTableWidgetItem, QTextBrowser, QLabel,
                               QHeaderView, QSpinBox, QCheckBox, QMenu, QSystemTrayIcon, QMessageBox, QPushButton,
                               QPlainTextEdit)
from src.ui_mainwindow import Ui_MainWindow
from datetime import datetime, timedelta
from src.get_calendar_data import data
import time
import uuid
from src import store_userid_version
from src import changeyaml
from win10toast_click import ToastNotifier
import qdarktheme

# Run the following command to generate the ui_form.py file
#     pyside6-uic form.ui -o ui_form.py, or
#     pyside2-uic form.ui -o ui_form.py

usersettings_filename = os.path.join(os.path.dirname(__file__), 'User/settings.yaml')
saved_data_filename = os.path.join(os.path.dirname(__file__), 'User/last_cal_data.parquet')
splash_filename = os.path.join(os.path.dirname(__file__), 'src/splashscreen.ui')
setting_filename = os.path.join(os.path.dirname(__file__), 'src/settings.yaml')
setting_ui_filename = os.path.join(os.path.dirname(__file__), 'src/settings.ui')
feedback_ui_filename = os.path.join(os.path.dirname(__file__), 'src/feedback.ui')
infowidget_ui_filename = os.path.join(os.path.dirname(__file__), 'src/info_widget.ui')


class StartWorker(QObject):
    online = Signal()
    offline = Signal()

    def __init__(self):
        super().__init__()

    def start(self):
        # online mode
        try:
            df = data()
            df.to_parquet(saved_data_filename)
            self.online.emit()

            if not changeyaml.pull(usersettings_filename)['saved_username']:
                from src import get_response_key
                key = get_response_key.get()
                if key == 'error':
                    pass

                else:
                    settings = changeyaml.pull(usersettings_filename)
                    os = "Windows 10" if platform.system() == "Windows" and int(platform.version().split('.')[2]) < 22000 else "Windows 11"
                    date = datetime.now().date().strftime("%m-%d-%Y")
                    response = store_userid_version.send(auth_key=key,
                                                         user_id=settings['user_id'],
                                                         app_version=settings['version'],
                                                         os=os,
                                                         date=date)
                    if response == 'error':
                        print('store user error')
                    else:
                        settings['saved_username'] = True
                        changeyaml.push(usersettings_filename, settings)
                        print('uuid sent')

        # offline mode
        except Exception as e:
            print(f"1 An exception occurred: {e}")
            self.offline.emit()


class EventCheckerWorker(QObject):
    finished = Signal(bool)

    def __init__(self):
        super().__init__()

    def start(self):
        df = data()  # Assuming data() is your function to get the new dataframe
        df_saved = pd.read_parquet(saved_data_filename)
        answer = False

        if df.equals(df_saved):
            print('data: no change')
        else:
            print("data: New Data")
            df.to_parquet(saved_data_filename)
            answer = True

        self.finished.emit(answer)


def create_user_folder():
    if not os.path.exists(usersettings_filename):
        os.makedirs(os.path.dirname(usersettings_filename), exist_ok=True)
        shutil.copy(setting_filename, usersettings_filename)
        settings = changeyaml.pull(usersettings_filename)
        user_id = str(uuid.uuid4())
        settings['user_id'] = user_id
        changeyaml.push(usersettings_filename, settings)


class Widget(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.table = self.ui.table

        self.start_thread = None
        self.start_worker = None
        self.splash_dialog = None
        self.splash_gif = None
        self.refresh_button_thread = None
        self.refresh_button_worker = None
        self.event_checker_worker = None
        self.event_checker_thread = None

        self.previous_notif_settings = None
        self.event_refresh_started = False
        self.background_running = False
        self.background_quit = False
        self.online = None
        self.df = None

        self.refresh_daily_timer = QTimer(self)
        self.notification_timer = QTimer(self)
        self.latest_event_timer = QTimer(self)

        self.ui.logo.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("http://www.tamuspe.org")))
        self.ui.refresh.clicked.connect(self.refresh_data)
        self.table.itemDoubleClicked.connect(self.item_double_clicked)
        self.table.setMouseTracking(True)
        self.ui.settings.clicked.connect(self.open_settings)

        self.notifier = ToastNotifier()
        self.start()

    def start(self):
        print(setting_ui_filename)
        create_user_folder()
        self.background_start()
        self.refresh_table_daily()
        self.start_notification_timer()
        self.keep_in_background()
        self.show()
        self.splash_screen()

    def splash_screen(self):
        loader = QUiLoader()
        self.splash_dialog = loader.load(splash_filename, self)
        self.splash_gif = self.splash_dialog.findChild(QLabel, 'label_2')
        self.splash_gif.setFixedSize(25, 25)

        # Load GIF
        movie = QMovie(os.path.join(os.path.dirname(__file__), 'src/loading.gif'))
        movie.setScaledSize(QSize().scaled(25, 25, Qt.KeepAspectRatio))
        self.splash_gif.setMovie(movie)
        movie.start()

        self.splash_dialog.show()

    def splash_ready(self):
        self.splash_gif.setFixedSize(50, 25)
        self.splash_gif.setText('Ready!')
        QTimer.singleShot(500, self.close_splash_dialog)

    def close_splash_dialog(self):
        self.splash_dialog.close()

    def background_start(self):
        self.start_worker = StartWorker()
        self.start_thread = QThread(self)
        self.start_worker.moveToThread(self.start_thread)
        self.start_worker.online.connect(self.online_mode)
        self.start_worker.offline.connect(self.offline_mode)
        self.start_thread.started.connect(self.start_worker.start)
        self.start_thread.start()

    def online_mode(self):
        print('online')
        self.online = True
        self.ui.offline_label.setText('')
        self.df = pd.read_parquet(saved_data_filename)
        self.update_table()
        self.latest_event_refresh_timer()
        self.start_thread.quit()
        self.splash_ready()

    def offline_mode(self):
        print('offline')
        self.online = False
        self.ui.offline_label.setText('Offline Mode')
        try:
            self.df = pd.read_parquet(saved_data_filename)
            self.update_table()
            self.latest_event_refresh_timer()
        except:
            pass
        finally:
            self.start_thread.quit()
            self.splash_ready()

    def update_data(self):
        # online mode
        try:
            self.df = data()
            self.df.to_parquet(saved_data_filename)
            self.update_table()
            self.ui.offline_label.setText('')
            self.online = True

            if not changeyaml.pull(usersettings_filename)['saved_username']:
                from src import get_response_key
                key = get_response_key.get()
                if key == 'error':
                    pass

                else:
                    settings = changeyaml.pull(usersettings_filename)
                    os = "Windows 10" if platform.system() == "Windows" and int(platform.version().split('.')[2]) < 22000 else "Windows 11"
                    date = datetime.now().date().strftime("%m-%d-%Y")
                    response = store_userid_version.send(auth_key=key,
                                                         user_id=settings['user_id'],
                                                         app_version=settings['version'],
                                                         os=os,
                                                         date=date)
                    if response == 'error':
                        print('store user error')
                    else:
                        settings['saved_username'] = True
                        changeyaml.push(usersettings_filename, settings)
                        print('uuid sent')

        # offline mode
        except Exception as e:
            print(f"2 An exception occurred: {e}")
            self.ui.offline_label.setText('Offline Mode')
            self.online = False

            try:
                self.df = pd.read_parquet(saved_data_filename)
                self.update_table()
            except:
                pass

    def update_table(self):
        df = self.df.loc[:, ['Title', 'Location', 'Date(s)', 'Time(s)', 'Description']]
        df_duration = self.df.loc[:, ['Duration', 'start_time', 'end_time']]
        cols = df.columns

        self.table.setCurrentCell(-1, -1)
        self.table.setColumnCount(len(cols))
        self.table.setRowCount(len(df))

        font = QFont()
        font.setPointSize(11)
        font.setBold(True)

        self.table.setHorizontalHeaderLabels(cols)
        self.table.horizontalHeader().setFont(font)

        # text_color = QColor(0, 81, 166)
        # header_style = "QHeaderView::section { color: %s; }" % text_color.name()
        # self.ui.table.horizontalHeader().setStyleSheet(header_style)

        # Iterate through the rows and columns
        for row in range(len(df)):
            for col in range(0, len(cols)):  # Start from the third column
                if col == 0:
                    item = QTableWidgetItem(str(df.iloc[row, col]))
                    self.table.setItem(row, col, item)

                elif col == 1:
                    text = str(df.iloc[row, col])
                    if text == 'None':
                        item = QTableWidgetItem('--')
                        item.setTextAlignment(Qt.AlignCenter)
                        self.table.setItem(row, col, item)

                    elif len(text) <= 22:
                        item = QTableWidgetItem(text)
                        item.setTextAlignment(Qt.AlignCenter)
                        self.table.setItem(row, col, item)

                    else:
                        font = QFont()
                        font.setPointSize(9)
                        font.setBold(True)
                        item = QTableWidgetItem('Location')
                        text_color = QColor(90, 164, 116)  # green
                        item.setForeground(text_color)
                        item.setFont(font)
                        item.setTextAlignment(Qt.AlignCenter)
                        item.setStatusTip("Double Click")
                        self.table.setItem(row, col, item)

                elif col == 3:
                    duration = (df_duration.iloc[row, 2] - df_duration.iloc[row, 1]).days
                    if duration > 0:
                        item = QTableWidgetItem(df_duration.iloc[row, 0])
                        item.setTextAlignment(Qt.AlignCenter)
                        self.table.setItem(row, col, item)

                    else:
                        item = QTableWidgetItem(str(df.iloc[row, col]))
                        item.setTextAlignment(Qt.AlignCenter)
                        self.table.setItem(row, col, item)

                elif col == 4:
                    text = str(df.iloc[row, col])
                    if text == 'None':
                        item = QTableWidgetItem("--")
                        item.setTextAlignment(Qt.AlignCenter)
                        self.table.setItem(row, col, item)

                    elif len(text) <= 22:
                        item = QTableWidgetItem(str(df.iloc[row, col]))
                        item.setTextAlignment(Qt.AlignCenter)
                        self.table.setItem(row, col, item)

                    else:
                        font = QFont()
                        font.setPointSize(9)
                        font.setBold(True)
                        item = QTableWidgetItem("Description")
                        # text_color = QColor(165, 43, 57)  # red
                        text_color = QColor(90, 164, 116)  # green
                        item.setForeground(text_color)
                        item.setFont(font)
                        item.setTextAlignment(Qt.AlignCenter)
                        item.setStatusTip("Double Click")
                        self.ui.table.setItem(row, col, item)

                else:
                    item = QTableWidgetItem(str(df.iloc[row, col]))
                    item.setTextAlignment(Qt.AlignCenter)
                    self.table.setItem(row, col, item)

        self.table.resizeColumnsToContents()
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)

        for col in range(self.table.horizontalHeader().count() - 1):
            current_size = self.table.horizontalHeader().sectionSize(col)
            self.table.horizontalHeader().resizeSection(col, current_size + 15)

        print('table updated')

    def event_checker(self, answer):
        if answer:
            self.df = pd.read_parquet(saved_data_filename)
            self.update_table()

        self.event_checker_thread.quit()

    def refresh_data(self):
        self.ui.refresh.setEnabled(False)  # make the refresh button greyed out
        self.refresh_button_thread = QThread()  # create thread
        self.refresh_button_worker = Worker()  # create worker
        self.refresh_button_worker.moveToThread(self.refresh_button_thread)  # move worker to thread
        self.refresh_button_thread.started.connect(self.refresh_button_worker.get_data)  # fetching from calendar
        self.refresh_button_worker.data_fetched.connect(self.handle_data_fetched)  # send fetched data to func
        self.refresh_button_worker.finished.connect(self.refresh_button_thread.quit)  # close the thread when it's done

        # Start the thread
        self.refresh_button_thread.start()

    def handle_data_fetched(self, fetched_data):
        if fetched_data is not None:
            self.df = fetched_data
            self.df.to_parquet(saved_data_filename)
            self.update_table()
            self.ui.refresh.setEnabled(True)
            self.ui.offline_label.setText('')
            self.ui.offline_notification.setText('')
            self.online = True

        else:
            self.refresh_button_thread.quit()
            self.refresh_button_thread.wait()
            self.ui.refresh.setEnabled(True)
            self.ui.offline_label.setText('Offline Mode')
            self.online = False

            try:
                self.df = pd.read_parquet(saved_data_filename)
                self.update_table()
            except:
                pass

    def item_double_clicked(self, item):
        if (self.table.item(item.row(), 1).text() == "Location" or
                self.table.item(item.row(), 4).text() == "Description"):
            self.open_info_widget(item.row())

    def open_info_widget(self, row):
        print('open info widget:', row + 1)
        loader = QUiLoader()
        info_dialog = loader.load(infowidget_ui_filename, self)
        info_textbox = info_dialog.findChild(QTextBrowser, 'info')
        location_textbox = info_dialog.findChild(QTextBrowser, 'location')
        date_label = info_dialog.findChild(QLabel, 'date')
        time_label = info_dialog.findChild(QLabel, 'time')

        df_duration = self.df.loc[row, ['start_time', 'end_time']]
        duration = (df_duration.iloc[1] - df_duration.iloc[0]).days
        if duration > 1:
            multi_day = [df_duration.iloc[0], df_duration.iloc[1]]
        else:
            multi_day = None

        title = self.df.loc[row, ['Title']].iloc[0]
        info = self.df.loc[row, ['Description']].iloc[0]
        location = self.df.loc[row, ['Location']].iloc[0]
        dates = self.table.item(row, 2).text()
        times = self.table.item(row, 3).text()

        if multi_day is not None:
            input_date1 = multi_day[0].strftime("%m/%d/%Y")
            day_of_week1 = multi_day[0].strftime("%A")

            date2 = multi_day[1] - timedelta(days=1)
            input_date2 = date2.strftime("%m/%d/%Y")
            day_of_week2 = date2.strftime("%A")

            formatted_date = (f"{day_of_week1}, {input_date1} - "
                              f"{day_of_week2}, {input_date2}")

        else:
            input_date = datetime.strptime(dates, "%m/%d/%Y")
            day_of_week = input_date.strftime("%A")
            formatted_date = f"{day_of_week}, {input_date.strftime('%m/%d/%Y')}"

        def fill_text_browser():
            if info:
                info_textbox.setText(info)
                location_textbox.setText(location)
                date_label.setText(formatted_date)
                time_label.setText(times)

            else:
                location_textbox.setText(location)
                date_label.setText(formatted_date)
                time_label.setText(times)
                info_dialog.resize(info_dialog.width(), 216)

        def adjust_dialog_size():
            # size of the info box
            info_textbox.document().adjustSize()
            info_box_size = info_textbox.document().size().height()
            if info_box_size > 300:
                add_height = info_box_size - 300
                info_dialog.resize(info_dialog.width(), info_dialog.height() + add_height)
            else:
                sub_height = 300 - info_box_size
                info_dialog.resize(info_dialog.width(), info_dialog.height() - sub_height)

        fill_text_browser()
        adjust_dialog_size()
        info_dialog.setWindowTitle(title)
        info_dialog.show()

    def refresh_table_daily(self):
        # Set the date and refresh the table every day
        today_date = datetime.now().strftime("%A, %m-%d-%Y")
        self.ui.date.setText(today_date)
        self.daily_table_refresh_timer()

    def daily_table_refresh_timer(self):

        def handle_timeout():
            # Set the timer to trigger every 24 hours
            self.refresh_daily_timer.setInterval(24 * 60 * 60 * 1000)  # 24 hours in milliseconds
            self.refresh_daily_timer.start()  # Restart the timer
            today_date = datetime.now().strftime("%A, %m-%d-%Y")
            self.ui.date.setText(today_date)
            self.refresh_data()

        self.refresh_daily_timer.timeout.connect(handle_timeout)
        now = datetime.now()
        next_midnight = datetime.combine(datetime.now().date() + timedelta(days=1), datetime.min.time())
        interval = (next_midnight - now).total_seconds() * 1000  # Convert seconds to milliseconds
        self.refresh_daily_timer.setInterval(interval)  # Set the timer to trigger every 24 hours
        self.refresh_daily_timer.setSingleShot(True)  # Adjust the remaining time to the beginning of the next midnight
        self.refresh_daily_timer.start()
        print('refresh_table_daily timer started')
        print('next day:', self.refresh_daily_timer.remainingTime() / 1000 / 60 / 60, 'hours')

    def latest_event_refresh_timer(self):

        def handle_timeout():
            new_now = datetime.now()
            new_next_event_datetime = None

            for new_index, new_row in self.df.iterrows():
                if new_row['End Time'] != '--':
                    new_date_string = f"{new_row['End Date']} {new_row['End Time']}"
                    new_date_time_obj = datetime.strptime(new_date_string, "%m/%d/%Y %I:%M %p")
                    if new_date_time_obj >= new_now:
                        new_next_event_datetime = new_date_time_obj
                        break

            new_interval = (new_next_event_datetime - new_now).total_seconds() * 1000  # Convert seconds to milliseconds
            self.latest_event_timer.setInterval(new_interval)
            self.latest_event_timer.start()  # Restart the timer
            self.refresh_data()
            print('next event:', self.latest_event_timer.remainingTime() / 1000 / 60 / 60, 'hours')

        self.latest_event_timer.timeout.connect(handle_timeout)

        now = datetime.now()
        next_event_datetime = None

        for index, row in self.df.iterrows():
            if row['End Time'] != '--':
                date_string = f"{row['End Date']} {row['End Time']}"
                date_time_obj = datetime.strptime(date_string, "%m/%d/%Y %I:%M %p")
                if date_time_obj >= now:
                    next_event_datetime = date_time_obj
                    break

        interval = (next_event_datetime - now).total_seconds() * 1000  # Convert seconds to milliseconds
        self.latest_event_timer.setInterval(interval)  # Set the timer to trigger every 24 hours
        self.latest_event_timer.setSingleShot(True)  # Adjust the remaining time to the beginning of the next midnight
        self.latest_event_timer.start()
        self.event_refresh_started = True
        print('latest_event_timer started')
        print('next event:', self.latest_event_timer.remainingTime() / 1000 / 60 / 60, 'hours')

    def start_notification_timer(self):
        if changeyaml.pull(usersettings_filename)['notifications']:
            if self.notification_timer.isActive():
                self.notification_timer.stop()
                self.notification_timer.timeout.disconnect()
                print('notif timer set to restart')

            self.set_notification_timer()

        else:
            if self.notification_timer.isActive():
                self.notification_timer.stop()
                print('stopped notification timer')

    def set_notification_timer(self):

        def handle_timeout():
            # Set the timer to trigger every minute
            self.notification_timer.setInterval(60 * 1000)  # 60 seconds in milliseconds
            self.notification_timer.start()  # Restart the timer
            self.send_notification()

        self.notification_timer.timeout.connect(handle_timeout)
        now = datetime.now()

        try:
            next_minute = datetime(now.year, now.month, now.day, now.hour, now.minute + 1)

        except:
            next_minute = datetime(now.year, now.month, now.day, now.hour + 1, 0)

        finally:
            interval = (next_minute - now).total_seconds() * 1000  # Convert seconds to milliseconds
            self.notification_timer.setInterval(interval)  # Set the timer to trigger every minute
            self.notification_timer.setSingleShot(True)  # Adjust the remaining time to the beginning of the next minute
            self.notification_timer.start()
            print('notif timer started')
            print('next minute:', self.notification_timer.remainingTime() / 1000, 'seconds')

    def send_notification(self, test=None):
        # send notification logic
        # print('time till next minute:', self.notification_timer.remainingTime() / 1000, 'seconds')
        # print('time till next day:', self.refresh_daily_timer.remainingTime() / 1000 / 60 / 60, 'hours')

        if not self.online:
            self.update_data()

        else:
            self.event_checker_worker = EventCheckerWorker()
            self.event_checker_thread = QThread(self)
            self.event_checker_worker.moveToThread(self.event_checker_thread)
            self.event_checker_worker.finished.connect(self.event_checker)
            self.event_checker_thread.started.connect(self.event_checker_worker.start)
            self.event_checker_thread.start()

        now = datetime.now()
        index = 0

        for index_, row in self.df.iterrows():
            if row['End Time'] != '--':
                date_string = f"{row['Start Date']} {row['Start Time']}"
                date_time_obj = datetime.strptime(date_string, "%m/%d/%Y %I:%M %p")
                if date_time_obj >= now:
                    index = index_
                    break

        start_time = self.df['start_time'].iloc[index]

        title = self.table.item(index, 0).text()
        location = self.table.item(index, 1).text()
        date = self.table.item(index, 2).text()
        event_time = self.table.item(index, 3).text()
        message = f"Where: {location}\nDate: {date}\nTime: {event_time}"

        timezone_info = start_time.tzinfo
        current_datetime = datetime.now(timezone_info)

        start_time = start_time.replace(second=0, microsecond=0)
        current_datetime = current_datetime.replace(second=0, microsecond=0)

        time_difference = start_time - current_datetime

        notification_hours = changeyaml.pull(usersettings_filename)['notification_hours']
        notification_days = changeyaml.pull(usersettings_filename)['notification_days']
        # glass
        if test:
            self.notifier.show_toast(title,
                                     message,
                                     icon_path=os.path.join(os.path.dirname(__file__), 'src/TAMUSPE_Square.ico'),
                                     duration=10,
                                     threaded=True,
                                     callback_on_click=self.notification_callback)

        if location != "--":

            if changeyaml.pull(usersettings_filename)['days']:
                print('next day notification:', time_difference - timedelta(days=notification_days))

                if time_difference == timedelta(days=notification_days):
                    self.notifier.show_toast(title,
                                             message,
                                             icon_path=os.path.join(os.path.dirname(__file__),
                                                                    'src/TAMUSPE_Square.ico'),
                                             duration=10,
                                             threaded=True,
                                             callback_on_click=self.notification_callback)

                    print(f'The start time is less than {notification_days} days away from the current time.')

            if changeyaml.pull(usersettings_filename)['hours']:
                print('next hour notification:', time_difference - timedelta(hours=notification_hours))

                if time_difference == timedelta(hours=notification_hours):
                    self.notifier.show_toast(title,
                                             message,
                                             icon_path=os.path.join(os.path.dirname(__file__),
                                                                    'src/TAMUSPE_Square.ico'),
                                             duration=10,
                                             threaded=True,
                                             callback_on_click=self.notification_callback)

                    print(f'The start time is less than {notification_hours} hours away from the current time.')

    def notification_callback(self):
        if self.isHidden():
            self.showNormal()  # Use showNormal() instead of show()
            self.activateWindow()
            self.raise_()
        if self.isMinimized():
            self.showNormal()
            self.activateWindow()
            self.raise_()
        else:
            self.raise_()

        self.table.setFocus()
        self.table.selectRow(0)

    def open_settings(self):
        tim = time.time()
        loader = QUiLoader()
        settings_dialog = loader.load(setting_ui_filename, self)
        notif_bool_cb = settings_dialog.findChild(QCheckBox, 'set_notification')
        background_bool_cb = settings_dialog.findChild(QCheckBox, 'set_background')
        days_cb = settings_dialog.findChild(QCheckBox, 'days_cb')
        hours_cb = settings_dialog.findChild(QCheckBox, 'hours_cb')
        notif_days_sb = settings_dialog.findChild(QSpinBox, 'days_spinbox')
        notif_hours_sb = settings_dialog.findChild(QSpinBox, 'hours_spinbox')
        notif_test = settings_dialog.findChild(QPushButton, 'test_notification')
        feedback_button = settings_dialog.findChild(QPushButton, 'feedback')

        def load_current_settings():
            cur_set = changeyaml.pull(usersettings_filename)
            self.previous_notif_settings = cur_set.copy()
            notif_bool_cb.setChecked(cur_set['notifications'])
            background_bool_cb.setChecked(cur_set['open_in_background'])
            notif_days_sb.setValue(cur_set['notification_days'])
            notif_hours_sb.setValue(cur_set['notification_hours'])
            days_cb.setChecked(cur_set['days'])
            hours_cb.setChecked(cur_set['hours'])
            return cur_set

        def accept(cur_set):
            print('open settings: accept')
            notif_bool = notif_bool_cb.isChecked()
            background_bool = background_bool_cb.isChecked()
            days = days_cb.isChecked()
            hours = hours_cb.isChecked()
            cur_set['notifications'] = notif_bool
            cur_set['open_in_background'] = background_bool
            cur_set['notification_days'] = notif_days_sb.value()
            cur_set['notification_hours'] = notif_hours_sb.value()
            cur_set['days'] = days
            cur_set['hours'] = hours

            changeyaml.push(usersettings_filename, cur_set)
            print("Current settings:", cur_set)

            if self.previous_notif_settings != cur_set:
                print('settings changed')
                self.start_notification_timer()

        def reject():
            print('open settings: reject')

        def notif_box_changed():
            if notif_bool_cb.isChecked():
                days_cb.setChecked(True)
                hours_cb.setChecked(True)
                days_cb.setEnabled(True)
                hours_cb.setEnabled(True)
                notif_days_sb.setEnabled(True)
                notif_hours_sb.setEnabled(True)
            else:
                days_cb.setChecked(False)
                hours_cb.setChecked(False)
                days_cb.setEnabled(False)
                hours_cb.setEnabled(False)
                notif_days_sb.setEnabled(False)
                notif_hours_sb.setEnabled(False)

        def days_cb_changed():
            if days_cb.isChecked():
                if notif_days_sb.value() == 0:
                    notif_days_sb.setValue(2)
            else:
                notif_days_sb.setValue(0)

        def hours_cb_changed():
            if hours_cb.isChecked():
                if notif_hours_sb.value() == 0:
                    notif_hours_sb.setValue(2)
            else:
                notif_hours_sb.setValue(0)

        def notif_days_sb_changed():
            if notif_days_sb.value() == 0:
                days_cb.setChecked(False)
            else:
                if not days_cb.isChecked():
                    days_cb.setChecked(True)

        def notif_hours_sb_changed():
            if notif_hours_sb.value() == 0:
                hours_cb.setChecked(False)
            else:
                if not hours_cb.isChecked():
                    hours_cb.setChecked(True)

        def test_notification():
            self.send_notification(test=True)

        def feedback_clicked():
            self.feedback_dialog()

        curent_settings = load_current_settings()
        notif_bool_cb.stateChanged.connect(notif_box_changed)
        days_cb.stateChanged.connect(days_cb_changed)
        hours_cb.stateChanged.connect(hours_cb_changed)
        notif_days_sb.textChanged.connect(notif_days_sb_changed)
        notif_hours_sb.textChanged.connect(notif_hours_sb_changed)
        notif_test.clicked.connect(test_notification)
        feedback_button.clicked.connect(feedback_clicked)
        settings_dialog.accepted.connect(lambda: accept(curent_settings))
        settings_dialog.rejected.connect(reject)
        settings_dialog.show()
        print(f'open settings time: {time.time() - tim :2f}')

    def feedback_dialog(self):
        loader = QUiLoader()
        feedback_dialog = loader.load(feedback_ui_filename, self)
        feedback_edit = feedback_dialog.findChild(QPlainTextEdit, 'plainTextEdit')
        status = feedback_dialog.findChild(QLabel, 'status')
        send_btn = feedback_dialog.findChild(QPushButton, 'send')
        close_btn = feedback_dialog.findChild(QPushButton, 'cancel')

        def send():
            print('feedback: send')
            user_id = changeyaml.pull(usersettings_filename)['user_id']
            name = f'{user_id}_{datetime.now().strftime("%Y-%m-%d_%I_%M_%S%p")}.txt'
            filename = os.path.join(os.path.dirname(__file__), name)
            text = feedback_edit.toPlainText()

            if text.strip() == "":
                print("The text is empty")
                status.setText('empty')

            else:
                print("text not empty.")

                from src import get_response_key
                key = get_response_key.get()
                if key == 'error':
                    status.setText('offline')

                else:
                    with open(filename, 'w') as file:
                        file.write(text)

                    from src import send_file
                    response = send_file.send(filename, name, key)
                    if response == 'error':
                        status.setText(response)
                        os.remove(filename)

                    else:
                        os.remove(filename)
                        feedback_dialog.close()

        def cancel():
            print('feedback: cancel')
            self.open_settings()
            feedback_dialog.close()

        send_btn.clicked.connect(send)
        close_btn.clicked.connect(cancel)
        feedback_dialog.show()

    def keep_in_background(self):
        print("Running in background")
        self.background_running = True

        tray_icon = QSystemTrayIcon(self)
        tray_icon.setIcon(QIcon(":/Images/images/TAMUSPE_Square.png"))  # Set your own icon path
        tray_icon.setToolTip("TAMU-SPE Events")  # Set your app tooltip here

        menu = QMenu(self)
        show_action = menu.addAction("Show")
        hide_action = menu.addAction("Hide")
        about_action = menu.addAction("About")
        website_action = menu.addAction("Visit Website")
        quit_action = menu.addAction("Quit")

        # Add a non-selectable action as a description
        menu.addSeparator()
        separator = QAction("Upcoming events:", self)
        separator.setEnabled(False)
        menu.addAction(separator)
        event1 = menu.addAction("nextevent1")
        event2 = menu.addAction("nextevent2")
        event3 = menu.addAction("nextevent3")

        def show_app():
            if self.isHidden():
                self.showNormal()  # Use showNormal() instead of show()
                self.raise_()
            if self.isMinimized():
                self.showNormal()
                self.raise_()
            else:
                self.raise_()

        def hide_app():
            self.hide()

        def exit_app():
            self.background_quit = True
            QCoreApplication.quit()

        def show_message():
            show_app()
            msg_box = QMessageBox()
            msg_box.about(self, "About", "Our mission as a student chapter at Texas A&M University is "
                                         "to maintain the success and raise the standards of our "
                                         "students, society, and department by executing a plan that "
                                         "seeks to fulfill SPE’s mission of developing technical "
                                         "knowledge and providing opportunities for students to enhance"
                                         " their technical and professional competence.")

            # Ensure the message box window becomes the active window
            msg_box.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.Window | Qt.WindowStaysOnTopHint)
            msg_box.showNormal()
            msg_box.activateWindow()
            msg_box.raise_()

        def update_top_events(reason):
            def handle_ampersand(text):
                # If the text contains an "&", replace it with "&&"
                return text.replace("&", "&&")

            event1_text = handle_ampersand(self.table.item(0, 0).text())
            event2_text = handle_ampersand(self.table.item(1, 0).text())
            event3_text = handle_ampersand(self.table.item(2, 0).text())

            event1.setText(event1_text)
            event2.setText(event2_text)
            event3.setText(event3_text)

            if reason == QSystemTrayIcon.Trigger:
                print("Left-clicked")

                if self.isHidden():
                    self.showNormal()

                if self.isMinimized():
                    self.showNormal()

                else:
                    self.showNormal()

            elif reason == QSystemTrayIcon.Context:
                print("Right-clicked")
                # Handle right-click event here

        def open_event(row):
            show_app()
            self.table.selectRow(row)
            col1 = self.table.item(row, 0).text()
            col4 = self.table.item(row, 4).text()

            if col1 == "Location" or col4 == "Description":
                self.open_info_widget(row)

        show_action.triggered.connect(show_app)
        hide_action.triggered.connect(hide_app)
        website_action.triggered.connect(lambda: QDesktopServices.openUrl(QUrl("http://www.tamuspe.org")))
        about_action.triggered.connect(show_message)
        event1.triggered.connect(lambda: open_event(0))
        event2.triggered.connect(lambda: open_event(1))
        event3.triggered.connect(lambda: open_event(2))
        tray_icon.activated.connect(update_top_events)
        quit_action.triggered.connect(exit_app)
        tray_icon.setContextMenu(menu)
        tray_icon.show()

    def closeEvent(self, event):
        if (self.background_running and not self.background_quit and
                changeyaml.pull(usersettings_filename)['open_in_background']):

            print('Hiding window')
            event.ignore()
            self.hide()

        else:
            print("Close event, Quitting")
            if self.refresh_button_thread is not None:
                print('refresh_button_thread running:', self.refresh_button_thread.isRunning())
                if self.refresh_button_thread.isRunning():
                    self.refresh_button_thread.quit()
                    self.refresh_button_thread.wait()
                    print('stopping refresh_button_thread')

            if self.refresh_daily_timer.isActive():
                self.refresh_daily_timer.stop()
                print('refresh_daily_timer active:', self.refresh_daily_timer.isActive())

            if self.notification_timer.isActive():
                self.notification_timer.stop()
                print('notification_timer active:', self.notification_timer.isActive())

            super().closeEvent(event)


class Worker(QObject):
    finished = Signal()
    data_fetched = Signal(object)

    def get_data(self):
        try:
            fetched_data = data()  # assuming 'data' function is long-running
            self.data_fetched.emit(fetched_data)
            self.finished.emit()

        except:
            self.data_fetched.emit(None)


def is_dark_mode():
    # Get the application's palette
    app_palette = QGuiApplication.palette()

    # Check the color of the window text and the window background
    window_text_color = app_palette.color(QPalette.ColorRole.WindowText)
    window_color = app_palette.color(QPalette.ColorRole.Window)

    # Calculate the luminance (a measure of the brightness)
    text_luminance = 0.299 * window_text_color.red() + 0.587 * window_text_color.green() + 0.114 * window_text_color.blue()
    window_luminance = 0.299 * window_color.red() + 0.587 * window_color.green() + 0.114 * window_color.blue()

    # A simple heuristic: if the text is brighter than the background, it's likely a dark mode
    return text_luminance > window_luminance


if __name__ == "__main__":
    tim = time.time()
    app = QApplication(sys.argv)
    qdarktheme.setup_theme("auto")
    print('start time 1:', time.time() - tim)
    window = Widget()
    print('start time 2:', time.time() - tim)
    window.show()
    print('total start time:', time.time() - tim)
    sys.exit(app.exec())
