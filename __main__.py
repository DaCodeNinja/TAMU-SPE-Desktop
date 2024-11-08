import sys
import os
import pandas as pd
from PySide6.QtCore import QUrl, QThread, QObject, Signal, Qt, QTimer, QCoreApplication, QSize
from PySide6.QtGui import QDesktopServices, QFont, QColor, QIcon, QAction, QPalette, QGuiApplication
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import (QApplication, QMainWindow, QTableWidgetItem, QTextBrowser, QLabel,
                               QHeaderView, QSpinBox, QCheckBox, QMenu, QSystemTrayIcon, QMessageBox, QPushButton,
                               QPlainTextEdit, QStyleFactory)
from ui.ui_mainwindow import Ui_MainWindow
from datetime import datetime, timedelta
from src.get_data import data
import time
import uuid
import src.changeyaml as changeyaml
import pync


# import os
# os.environ["QT_LOGGING_RULES"] = "*.debug=false"

# Important:
# You need to run the following command to generate the ui_form.py file
#     pyside6-uic form.ui -o ui_form.py, or
#     pyside2-uic form.ui -o ui_form.py

class Worker(QObject):
    """
    This right here is a little helper function. You can use it to run tasks in parallel. In this app,
    I used it to fetch data, make updates, refresh, and anything else really. Our user won't even notice.
    """
    finished = Signal()
    data_fetched = Signal(object)

    def get_data(self):
        try:
            fetched_data = data()  # assuming 'data' function is long-running
            self.data_fetched.emit(fetched_data)
            self.finished.emit()

        except:
            self.data_fetched.emit(None)


class Widget(QMainWindow):
    """
    This is the heart. All the code flows through here. This is the main window and executable.
    """
    def __init__(self):
        """
        Boilerplate. Unlocks the real magic of QT in python.
        """
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        """ Grab the table element from the UI code we just "setup" , setup some filepaths"""
        self.table = self.ui.table
        self.df = None
        self.settings_filename = os.path.join(os.path.dirname(__file__), 'src/settings.yaml')
        self.infowidget_filename = os.path.join(os.path.dirname(__file__), 'ui/info_widget.ui')
        self.settings_dialog_filename = os.path.join(os.path.dirname(__file__), 'ui/settings.ui')
        self.feedback_dialog_filename = os.path.join(os.path.dirname(__file__), 'ui/feedback.ui')

        """ 
        Gotta setup some pointers for the multi-tasking (threading) to work properly
        """
        self.refresh_button_thread = None
        self.refresh_button_worker = None

        self.refresh_daily_timer = QTimer(self)
        self.notification_timer = QTimer(self)

        self.previous_notif_settings = None
        self.background_running = False
        self.background_quit = False

        self.ui.logo.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("http://www.tamuspe.org")))
        self.ui.refresh.clicked.connect(self.refresh_data)
        self.table.itemDoubleClicked.connect(self.item_double_clicked)
        self.ui.settings.clicked.connect(self.open_settings)

        self.app_start()
        self.update_data()
        self.refresh_table_daily()
        self.keep_in_background()

    def app_start(self):
        if changeyaml.pull(self.settings_filename)['first_open']:
            settings = changeyaml.pull(self.settings_filename)
            user_id = str(uuid.uuid4())
            settings['user_id'] = user_id
            settings['first_open'] = False
            changeyaml.push(self.settings_filename, settings)

        if is_dark_mode():
            print("System is in dark mode")
        else:
            print("System is in light mode")
            icon = QIcon()
            icon.addFile(":/Images/images/icons8-refresh-24.png")
            self.ui.refresh.setIcon(icon)
            self.ui.refresh.setIconSize(QSize(16, 16))

            icon1 = QIcon()
            icon1.addFile(":/Images/images/blk-settings-50.png")
            self.ui.settings.setIcon(icon1)
            self.ui.settings.setIconSize(QSize(16, 16))

    def update_data(self):
        try:
            self.df = data()
            self.df.to_parquet('last_saved_data.parquet')
            self.start_notification_timer()
            self.update_table()

            if not changeyaml.pull(self.settings_filename)['saved_username']:

                import src.get_key as get_key
                key = get_key.get()
                if key == 'error':
                    pass

                else:
                    settings = changeyaml.pull(self.settings_filename)
                    import store_userid_version
                    response = store_userid_version.send(key, settings['user_id'], settings['version'])
                    if response == 'error':
                        pass
                    else:
                        settings['saved_username'] = True
                        changeyaml.push(self.settings_filename, settings)
                        print('uuid sent')

        except Exception as e:
            print(f"An exception occurred: {e}")
            self.ui.date.setText(e)
            self.ui.offline_label.setText('Offline Mode / Error')
            if changeyaml.pull(self.settings_filename)['notifications']:
                self.ui.offline_notification.setText('Notifications Disabled')

            try:
                self.df = pd.read_parquet('last_saved_data.parquet')
                self.update_table()
            except:
                pass

    def update_table(self):
        df = self.df.loc[:, ['Title', 'Location', 'Date(s)', 'Time Span', 'Description']]
        df_duration = self.df.loc[:, ['Duration', 'start_time', 'end_time']]
        cols = df.columns

        self.table.setCurrentCell(-1, -1)
        self.table.setColumnCount(len(cols))
        self.table.setRowCount(len(df))

        font = QFont()
        font.setPointSize(14)
        font.setBold(True)

        self.table.setHorizontalHeaderLabels(cols[:-1])
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
                        header_item = QTableWidgetItem("")
                        self.table.setHorizontalHeaderItem(col, header_item)
                        font = QFont()
                        font.setPointSize(14)
                        font.setBold(True)
                        item = QTableWidgetItem('Double-Click for Info')
                        # text_color = QColor(90, 164, 116)  # green // nah i like the polished look better
                        # item.setForeground(text_color)

                        item.setFont(font)
                        item.setTextAlignment(Qt.AlignCenter)
                        self.table.setItem(row, col, item)
                        self.table.column

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
                        header_item = QTableWidgetItem("")
                        self.table.setHorizontalHeaderItem(col, header_item)

                        font = QFont()
                        font.setPointSize(14)
                        # font.setBold(True)
                        item = QTableWidgetItem("Double-Click for Info")
                        # text_color = QColor(165, 43, 57)  # red
                        # text_color = QColor(90, 164, 116)  # green
                        # item.setForeground(text_color)
                        item.setFont(font)
                        item.setTextAlignment(Qt.AlignCenter)
                        self.ui.table.setItem(row, col, item)

                else:
                    item = QTableWidgetItem(str(df.iloc[row, col]))
                    item.setTextAlignment(Qt.AlignCenter)
                    self.table.setItem(row, col, item)

        self.table.resizeColumnsToContents()
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        print('table updated')

    def item_double_clicked(self, item):
        if (self.table.item(item.row(), 4).text() == "Double-Click for Info" or
                self.table.item(item.row(), 1).text() == "Double-Click for Info"):

            df_duration = self.df.loc[item.row(), ['start_time', 'end_time']]
            duration = (df_duration.iloc[1] - df_duration.iloc[0]).days
            if duration > 1:
                multi_day = [df_duration.iloc[0], df_duration.iloc[1]]
            else:
                multi_day = None

            title = self.df.loc[item.row(), ['Title']].iloc[0]
            info = self.df.loc[item.row(), ['Description']].iloc[0]
            location = self.df.loc[item.row(), ['Location']].iloc[0]
            dates = self.table.item(item.row(), 2).text()
            times = self.table.item(item.row(), 3).text()

            self.open_info_widget(title, info, location, dates, times, item.row(), multi_day)

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
            self.ui.refresh.setEnabled(True)
            self.update_table()
            self.ui.offline_label.setText('')
            self.ui.offline_notification.setText('')
            self.df.to_parquet('last_saved_data.parquet')

        else:
            self.refresh_button_thread.quit()
            self.refresh_button_thread.wait()
            self.ui.refresh.setEnabled(True)

    def refresh_table_daily(self):
        # Set the date and refresh the table every day
        today_date = datetime.now().strftime("%A, %m-%d-%Y")
        self.ui.date.setText(today_date)

        if changeyaml.pull(self.settings_filename)['refresh_table_daily']:
            if self.refresh_daily_timer.isActive():
                self.refresh_daily_timer.stop()
                self.refresh_daily_timer.timeout.disconnect()
                print('refresh_table_daily timer set to restart')

            self.table_refresh_timer()

        else:
            if self.refresh_daily_timer.isActive():
                self.refresh_daily_timer.stop()
                print('stopped refresh_table_daily timer')

    def table_refresh_timer(self):

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

    def start_notification_timer(self):
        if changeyaml.pull(self.settings_filename)['notifications']:
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

        start_time = self.df['start_time'].iloc[0]

        title = self.table.item(0, 0).text()
        location = self.table.item(0, 1).text()
        date = self.table.item(0, 2).text()
        event_time = self.table.item(0, 3).text()
        message = f"Where: {location}\nDate: {date}\nTime: {event_time}"

        timezone_info = start_time.tzinfo
        current_datetime = datetime.now(timezone_info)

        time_difference = start_time - current_datetime

        notification_hours = changeyaml.pull(self.settings_filename)['notification_hours']
        notification_days = changeyaml.pull(self.settings_filename)['notification_days']

        if test:
            pync.notify(title=title, subtitle='Registration Required',
                        message=message, open='https://www.tamuspe.org/calendar')

        if location != "--":

            if changeyaml.pull(self.settings_filename)['days']:
                print('next day notification:', time_difference - timedelta(days=notification_days))
                if notification_days == 1:
                    subtitle = 'Starts in: 1 Day, Registration Required'
                else:
                    subtitle = f'Starts in: {notification_days} Days, Registration Required'

                if time_difference == timedelta(days=notification_days):
                    pync.notify(title=title, subtitle=subtitle,
                                message=message, open='https://www.tamuspe.org/calendar')

                    print(f'The start time is less than {notification_days} days away from the current time.')

            if changeyaml.pull(self.settings_filename)['hours']:
                print('next hour notification:', time_difference - timedelta(hours=notification_hours))
                if notification_hours == 1:
                    subtitle = 'Starts in: 1 Hour'
                else:
                    subtitle = f'Starts in: {notification_hours} Hours'

                if time_difference == timedelta(hours=notification_hours):
                    pync.notify(title=title, subtitle=subtitle,
                                message=message, open='https://www.tamuspe.org/calendar')

                    print(f'The start time is less than {notification_hours} hours away from the current time.')

    def open_info_widget(self, title, info, location, dates, times, row, multi_day):
        print('open info widget:', row + 1)
        loader = QUiLoader()
        info_dialog = loader.load(self.infowidget_filename, self)
        info_textbox = info_dialog.findChild(QTextBrowser, 'info')
        location_textbox = info_dialog.findChild(QTextBrowser, 'location')
        date_label = info_dialog.findChild(QLabel, 'date')
        time_label = info_dialog.findChild(QLabel, 'time')

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

    def open_settings(self):
        tim = time.time()
        loader = QUiLoader()
        settings_dialog = loader.load(self.settings_dialog_filename, self)
        notif_bool_cb = settings_dialog.findChild(QCheckBox, 'set_notification')
        background_bool_cb = settings_dialog.findChild(QCheckBox, 'set_background')
        days_cb = settings_dialog.findChild(QCheckBox, 'days_cb')
        hours_cb = settings_dialog.findChild(QCheckBox, 'hours_cb')
        notif_days_sb = settings_dialog.findChild(QSpinBox, 'days_spinbox')
        notif_hours_sb = settings_dialog.findChild(QSpinBox, 'hours_spinbox')
        notif_test = settings_dialog.findChild(QPushButton, 'test_notification')
        feedback_button = settings_dialog.findChild(QPushButton, 'feedback')

        def load_current_settings():
            cur_set = changeyaml.pull(self.settings_filename)
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

            changeyaml.push(self.settings_filename, cur_set)
            print(cur_set)

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
        feedback_dialog = loader.load(self.feedback_dialog_filename, self)
        feedback_edit = feedback_dialog.findChild(QPlainTextEdit, 'plainTextEdit')
        status = feedback_dialog.findChild(QLabel, 'status')
        send_btn = feedback_dialog.findChild(QPushButton, 'send')
        close_btn = feedback_dialog.findChild(QPushButton, 'cancel')

        def send():
            print('feedback: send')
            user_id = changeyaml.pull(self.settings_filename)['user_id']
            filename = f'{user_id}_{datetime.now().strftime("%Y-%m-%d_%I:%M:%S%p")}.txt'
            text = feedback_edit.toPlainText()

            if text.strip() == "":
                print("The text is empty")
                status.setText('empty')

            else:
                print("text not empty.")

                import src.get_key as get_key
                key = get_key.get()
                if key == 'error':
                    os.remove(filename)
                    status.setText('empty')

                else:
                    with open(filename, 'w') as file:
                        file.write(text)

                    import src.send_file as send_file
                    response = send_file.send(filename, key)
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

        menu = QMenu()
        open_action = menu.addAction("Open")
        about_action = menu.addAction("About")
        website_action = menu.addAction("Visit Website")
        quit_action = menu.addAction("Quit")

        # Add a non-selectable action as a description
        menu.addSeparator()
        separator = QAction("Upcoming events:", self)
        separator.setEnabled(False)
        menu.addAction(separator)
        event1 = menu.addAction("event1")
        event2 = menu.addAction("event2")
        event3 = menu.addAction("event3")

        def show_app():
            if self.isHidden():
                self.showNormal()  # Use showNormal() instead of show()
                self.raise_()
            if self.isMinimized():
                self.showNormal()
                self.raise_()
            else:
                self.raise_()

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

        def update_top_events():
            def handle_ampersand(text):
                # If the text contains an "&", replace it with "&&"
                return text.replace("&", "&&")

            event1_text = handle_ampersand(self.table.item(0, 0).text())
            event2_text = handle_ampersand(self.table.item(1, 0).text())
            event3_text = handle_ampersand(self.table.item(2, 0).text())

            event1.setText(event1_text)
            event2.setText(event2_text)
            event3.setText(event3_text)

        def open_event(row):
            show_app()
            self.table.selectRow(row)
            col1 = self.table.item(row, 0).text()
            col5 = self.table.item(row, 4).text()

            if col5 == "Double-Click for Info" or col1 == "Double-Click for Info":
                title = self.df.loc[row, ['Title']][0]
                info = self.df.loc[row, ['Description']][0]
                location = self.df.loc[row, ['Location']][0]
                dates = self.table.item(row, 2).text()
                times = self.table.item(row, 3).text()
                self.open_info_widget(title, info, location, dates, times, row)

        open_action.triggered.connect(show_app)
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
        if self.background_running and not self.background_quit:
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


def enforce_dark_mode(app_):
    app.setStyle(QStyleFactory.create("Fusion"))  # Set the Fusion style

    # Now adjust the color palette for a dark theme
    dark_palette = QPalette()

    # Use darker shades for various palette roles
    dark_palette.setColor(QPalette.Window, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.Window, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.WindowText, Qt.white)
    dark_palette.setColor(QPalette.Base, QColor(25, 25, 25))
    dark_palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ToolTipBase, Qt.white)
    dark_palette.setColor(QPalette.ToolTipText, Qt.white)
    dark_palette.setColor(QPalette.Text, Qt.white)
    dark_palette.setColor(QPalette.Button, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ButtonText, Qt.white)
    dark_palette.setColor(QPalette.BrightText, Qt.red)
    dark_palette.setColor(QPalette.Link, QColor(42, 130, 218))
    dark_palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    dark_palette.setColor(QPalette.HighlightedText, Qt.black)

    app.setPalette(dark_palette)
    app.setStyleSheet("QToolTip { color: #ffffff; background-color: #2a82da; border: 1px solid white; }")


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
    app = QApplication(sys.argv)
    window = Widget()
    window.show()
    sys.exit(app.exec())
