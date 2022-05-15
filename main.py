import sys
import sqlite3 as sq

from os import replace
from math import ceil
from PIL import Image
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QWidget,\
    QInputDialog, QFileDialog

from helpers import to_pixmap, excepthook, ClickableLabel, Theme,\
    DEFAULT_PHOTO, DEFAULT_COVER, ICON, ALB_LABEL_FONT
from ui_module import Ui_Login, Ui_MainWindow, Ui_AlbumsSettings,\
    Ui_ThemeSettings, Ui_UserSettings
from album_module import Album


class LoginWindow(QWidget, Ui_Login):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        im = Image.open(ICON).resize((170, 170))
        self.icon_lab.setPixmap(to_pixmap(im))
        self.setWindowIcon(QIcon(ICON))

        self.bd = sq.connect('db/gallery.sqlite')
        cur = self.bd.cursor()
        cur.execute('''CREATE TABLE IF NOT EXISTS Users
              (Login TEXT, Password TEXT, Path_to_bd TEXT)''')
        self.users = cur.execute('''SELECT * FROM Users''').fetchall()
        if not self.users:
            self.new_account_check.setChecked(True)
            self.login_or_reg()
        self.bd.commit()

        self.login_but.clicked.connect(self.open_bromnitsa)
        self.new_account_check.stateChanged.connect(self.login_or_reg)

    def login_or_reg(self):
        if self.new_account_check.isChecked():
            self.login_but.setText('Зарегистрироваться')
        else:
            self.login_but.setText('Войти')

    def open_bromnitsa(self):
        login, password = self.login_ed.text(), self.password_ed.text()
        cur = self.bd.cursor()
        logins = cur.execute('''SELECT Login FROM Users''').fetchall()
        logins = [l[-1] for l in logins]
        if self.users and not self.new_account_check.isChecked():
            if login not in logins:
                self.dialog_lab.setText('Пользователь не найден.')
                return
            if self.users[logins.index(login)][1] != password:
                self.dialog_lab.setText('Неверный пароль.')
                return
            path = self.users[logins.index(login)][2]
        elif self.new_account_check.isChecked():  # Регистрация
            if login in logins:
                self.dialog_lab.setText('Такой пользователь уже есть.')
                return
            if len(password) < 6:
                self.dialog_lab.setText('Короткий пароль.')
                return
            path = 'db/' + login + "_bd.sqlite"
            cur = self.bd.cursor()
            cur.execute('''INSERT INTO Users(Login,
Password, Path_to_bd) VALUES(?, ?, ?)''', (login, password, path))
            self.bd.commit()
        else:
            self.dialog_lab.setText('Пользователь не найден.')
            return
        self.bd.close()
        self.gallery = MainWindow(login, path)
        self.gallery.show()
        self.hide()


class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, login, path_to_bd):
        super().__init__()
        self.setupUi(self)

        # Открываем БД:
        self.path_to_bd = path_to_bd
        self.login = login
        self.bd = sq.connect(self.path_to_bd)
        cur = self.bd.cursor()
        cur.execute('''CREATE TABLE IF NOT EXISTS Settings(Name TEXT,
 Path_to_photo TEXT, Theme TEXT, N_col INT)''')
        self.settings = cur.execute('''SELECT * FROM Settings''').fetchone()
        if not self.settings:
            cur.execute('''INSERT INTO Settings(Name, Path_to_photo, Theme,
 N_col) VALUES('Пользователь', ?, 'Светлая', 6)''', (DEFAULT_PHOTO, ))
        self.settings = cur.execute('''SELECT * FROM Settings''').fetchone()
        self.bd.commit()

        # Настройки окна и всей программы:
        self.nik = self.settings[0]
        self.theme = Theme(self.settings[2])
        try:
            self.photo = Image.open(self.settings[1]).resize((200, 200))
            self.photo_path = self.settings[1]
        except FileNotFoundError as er:
            self.photo = Image.open(DEFAULT_PHOTO).resize((200, 200))
            self.photo_path = DEFAULT_PHOTO
        self.n_col = self.settings[3]

        # Сохранённые альбомы и их настройки:
        self.alb_labels, self.alb_name_labels, self.albums = [], [], []
        cur = self.bd.cursor()
        for tuple_ in cur.execute('''SELECT name from sqlite_master
 where type= "table"''').fetchall():
            if tuple_ not in [('Settings', ), ('sqlite_sequence', )]:
                self.albums.append(Album(self, tuple_[0]))
        self.cur_albums = self.albums.copy()

        # Задаём параметры окну:
        self.nik_lab.setText(self.nik)
        self.nik_lab.setAlignment(Qt.AlignCenter if len(self.nik) <= 17
                                  else Qt.AlignLeft | Qt.AlignVCenter)
        self.photo_lab.setPixmap(to_pixmap(self.photo))
        self.set_style(self.theme)
        self.setWindowIcon(QIcon(ICON))

        # Отображаем альбомы:
        self.print_albums(self.albums)

        # Подключаем к виджетам слоты:
        self.add_album_but.clicked.connect(self.add_album)
        self.settings_but.clicked.connect(self.open_settings)
        self.search_but.clicked.connect(self.search)
        self.scroll.valueChanged.connect(self.reprint)

    def reprint(self, val=0):
        self.print_albums(self.cur_albums)

    def alb_clicked(self, event):
        self.alb = event.item
        self.alb.theme = self.theme
        self.alb.set_style(self.theme)
        self.alb.show()

    def add_album(self):
        self.input_alb_name = QInputDialog(self)
        self.input_alb_name.setWindowTitle('Введите название альбома')
        self.input_alb_name.show()

        label = self.input_alb_name.children()[1]
        label.setText("Какое дать название?")
        label.setStyleSheet(self.theme.label_st)

        line_edit = self.input_alb_name.children()[0]
        line_edit.setText("")
        line_edit.setStyleSheet(self.theme.edit_st)

        ok_but = self.input_alb_name.children()[2].children()[1]
        ok_but.setText('Применить')
        cancel_but = self.input_alb_name.children()[2].children()[2]
        cancel_but.setText('Отмена')
        ok_but.setStyleSheet(self.theme.pushbut_st)
        cancel_but.setStyleSheet(self.theme.pushbut_st)
        ok_but.clicked.connect(self.make_alb)

    def make_alb(self):
        name = self.input_alb_name.children()[0].text()
        cur = self.bd.cursor()
        tables = [el[0] for el in cur.execute('''SELECT name from
 sqlite_master where type= "table"''').fetchall()]
        begin_tab_name = ''.join([b if b.isalnum() else '_'
                                  for b in list(name)])
        temp_tab_name, i = begin_tab_name, 1
        while temp_tab_name in tables:
            temp_tab_name = begin_tab_name + str(i)
            i += 1
        cur.execute('''CREATE TABLE {} (Im_id
 INTEGER PRIMARY KEY AUTOINCREMENT, path_to_im TEXT, Im_name TEXT, Name TEXT,
 path_to_cover TEXT, N_col INT)'''.format(temp_tab_name))
        cur.execute('''INSERT INTO {}(Name, path_to_cover, N_col)
 VALUES(?, ?, ?)'''.format(temp_tab_name), (name, DEFAULT_COVER, 6))
        self.bd.commit()
        al = Album(self, temp_tab_name)
        self.albums.append(al)
        self.cur_albums.append(al)
        self.print_albums(self.cur_albums)

    def open_settings(self):
        self.settings = AlbumsSettings(self)
        self.settings.show()

    def search(self):
        self.cur_albums = [al for al in self.albums
                           if self.search_ed.text().lower() in al.name.lower()]
        self.print_albums(self.cur_albums)

    def set_style(self, theme):
        self.setStyleSheet(theme.window_st)
        self.add_album_but.setStyleSheet(theme.pushbut_st)
        self.settings_but.setStyleSheet(theme.pushbut_st)
        self.search_but.setStyleSheet(theme.pushbut_st)
        self.nik_lab.setStyleSheet(theme.label_st)
        self.search_ed.setStyleSheet(theme.edit_st)
        self.search_ed.setPalette(theme.window_pal)
        QApplication.setPalette(theme.window_pal)
        self.scroll.setStyleSheet(theme.scroll_st)
        self.print_albums(self.cur_albums)

    def print_albums(self, albums):
        # Убираем старые label:
        for al in self.alb_labels:
            al.hide()
        for nam in self.alb_name_labels:
            nam.hide()
        self.alb_labels, self.alb_name_labels = [], []

        # Задаём максимальное значение scroll исходя из количества альбомов:
        n = int(ceil(len(albums) / self.n_col))
        self.scroll.setMaximum(n - 1 if len(albums) / self.n_col >= 1 else 0)
        begin = self.scroll.value()

        # Отображаем альбомы:
        x, y = 260, 63
        albums = sorted(albums, key=lambda x: x.name)
        for al_list in [albums[i:i + self.n_col]
                        for i in range(0, len(albums), self.n_col)][begin:]:
            for album in al_list:
                self.l1 = ClickableLabel(self, self.alb_clicked, album)
                self.l1.setPixmap(to_pixmap(album.cover))
                self.l1.setGeometry(x, y, 150, 150)
                self.l1.move(x, y)
                self.l1.show()
                self.alb_labels.append(self.l1)

                self.l2 = QLabel(album.name, self)
                self.l2.setGeometry(x, y + 160, 150, 30)
                self.l2.move(x, y + 150)
                self.l2.setAlignment(Qt.AlignCenter if len(album.name) <= 18
                                     else Qt.AlignLeft | Qt.AlignVCenter)
                self.l2.setStyleSheet(self.theme.label_st + ALB_LABEL_FONT)
                self.l2.show()
                self.alb_name_labels.append(self.l2)
                x += 170
            x = 260
            y += 200


class AlbumsSettings(QWidget, Ui_AlbumsSettings):
    def __init__(self, parent):
        super().__init__()
        self.setupUi(self)

        # Задаём атрибуты:
        self.theme, self.parent = parent.theme, parent

        # Задаём параметры окну:
        self.n_col_box.setValue(parent.n_col)
        self.setWindowIcon(QIcon(ICON))

        # Задаём стиль:
        self.set_style(self.theme)

        # Подключаем к кнопкам слоты:
        self.save_but.clicked.connect(self.save)
        self.to_themes_but.clicked.connect(self.to_themes)
        self.to_user_but.clicked.connect(self.to_user)

    def set_style(self, theme):
        self.setStyleSheet(theme.window_st)
        QApplication.setPalette(theme.window_pal)
        self.fone.setStyleSheet(theme.frame_st)
        self.title_lab.setStyleSheet(theme.label_st)
        self.to_user_but.setStyleSheet(theme.pushbut_st)
        self.to_themes_but.setStyleSheet(theme.pushbut_st)
        self.to_alb_view_but.setStyleSheet(theme.pushbut_st)
        self.col_lab.setStyleSheet(theme.label_st)
        self.n_col_box.setStyleSheet(theme.spinbox_st)
        self.n_col_box.setPalette(theme.spinbox_pal)
        self.save_but.setStyleSheet(theme.pushbut_st)

    def save(self):
        self.parent.n_col = self.n_col_box.value()
        self.parent.print_albums(self.parent.cur_albums)
        cur = self.parent.bd.cursor()
        cur.execute('''UPDATE Settings SET N_col = ''' +
                    str(self.parent.n_col))
        self.parent.bd.commit()
        self.hide()

    def to_themes(self):
        self.settings = ThemeSettings(self.parent)
        self.settings.show()
        self.hide()

    def to_user(self):
        self.settings = UserSettings(self.parent)
        self.settings.show()
        self.hide()


class ThemeSettings(QWidget, Ui_ThemeSettings):
    def __init__(self, parent):
        super().__init__()
        self.setupUi(self)

        # Задаём атрибуты:
        self.theme, self.parent = parent.theme, parent
        self.cur_theme = self.theme

        # Задаём параметры окну:
        for but in self.buttonGroup.buttons():
            but.setChecked(True if but.text() == self.theme.name else False)
        self.setWindowIcon(QIcon(ICON))

        # Задаём стиль:
        self.set_style(self.theme)

        # Подключаем к кнопкам слоты:
        self.to_alb_view_but.clicked.connect(self.to_alb_view)
        self.to_user_but.clicked.connect(self.to_user)
        self.save_but.clicked.connect(self.save)
        self.buttonGroup.buttonClicked.connect(self.change_theme)

    def set_style(self, theme):
        self.setStyleSheet(theme.window_st)
        QApplication.setPalette(theme.window_pal)
        self.fone.setStyleSheet(theme.frame_st)
        self.title_lab.setStyleSheet(theme.label_st)
        self.to_user_but.setStyleSheet(theme.pushbut_st)
        self.to_themes_but.setStyleSheet(theme.pushbut_st)
        self.to_alb_view_but.setStyleSheet(theme.pushbut_st)
        self.second_title_lab.setStyleSheet(theme.label_st)
        self.light_radio.setStyleSheet(theme.radiobut_st)
        self.dark_radio.setStyleSheet(theme.radiobut_st)
        self.retro_radio.setStyleSheet(theme.radiobut_st)
        self.neon_radio.setStyleSheet(theme.radiobut_st)
        self.save_but.setStyleSheet(theme.pushbut_st)
        self.set_style_to_view(theme)

    def set_style_to_view(self, theme):
        self.window_view.setStyleSheet(theme.window_st)
        self.fone_view.setStyleSheet(theme.frame_st)
        self.label_view.setStyleSheet(theme.label_st)
        self.input_view.setStyleSheet(theme.edit_st)
        self.input_view.setPalette(theme.window_pal)
        self.pushbut_view.setStyleSheet(theme.pushbut_st)
        self.radio_view.setStyleSheet(theme.radiobut_st)
        self.dial_view.setStyleSheet(theme.dial_st)
        self.slider_view.setStyleSheet(theme.slider_st)

    def to_alb_view(self):
        self.settings = AlbumsSettings(self.parent)
        self.settings.show()
        self.hide()

    def to_user(self):
        self.settings = UserSettings(self.parent)
        self.settings.show()
        self.hide()

    def save(self):
        self.parent.theme = self.cur_theme
        self.parent.set_style(self.cur_theme)
        self.parent.print_albums(self.parent.cur_albums)
        for al in self.parent.albums:
            al.theme = self.cur_theme
            al.set_style(self.cur_theme)
            al.print_images(al.cur_images)
            for im in al.images:
                im.theme = self.cur_theme
                im.set_style(self.cur_theme)
                im.editor.theme = self.cur_theme
                im.editor.set_style(self.cur_theme)
        cur = self.parent.bd.cursor()
        cur.execute('''UPDATE Settings SET Theme = ''' + "'" +
                    self.cur_theme.name + "'")
        self.parent.bd.commit()
        self.hide()

    def change_theme(self, button):
        self.cur_theme = Theme(button.text())
        self.set_style_to_view(self.cur_theme)


class UserSettings(QWidget, Ui_UserSettings):
    def __init__(self, parent):
        super().__init__()
        self.setupUi(self)

        # Задаём атрибуты:
        self.theme, self.parent = parent.theme, parent
        self.cur_nik = parent.nik
        self.cur_photo = parent.photo
        self.cur_photo_name = parent.photo_path
        self.new_path = parent.path_to_bd

        self.user_bd = sq.connect("gallery.sqlite")
        cur = self.user_bd.cursor()
        self.password = cur.execute('''SELECT Password FROM Users
 WHERE Login = ?''', (parent.login, )).fetchone()[0]
        self.login = parent.login

        # Задаём параметры окну:
        self.nik_lab.setText(self.cur_nik)
        self.nik_lab.setAlignment(Qt.AlignCenter if len(self.cur_nik) <= 17
                                  else Qt.AlignLeft | Qt.AlignVCenter)
        self.photo_lab.setPixmap(to_pixmap(self.cur_photo))
        self.path_ed.setText(self.new_path)
        self.login_ed.setText(self.login)
        self.password_ed.setText('*' * len(self.password))
        self.setWindowIcon(QIcon(ICON))

        # Задаём стиль:
        self.set_style(self.theme)

        # Подключаем к кнопкам слоты:
        self.to_alb_view_but.clicked.connect(self.to_alb_view)
        self.to_themes_but.clicked.connect(self.to_themes)
        self.change_nik_but.clicked.connect(self.change_nik)
        self.change_photo_but.clicked.connect(self.change_photo)
        self.log_pas_change_group.buttonClicked.connect(self.change_log_pas)
        self.change_path_but.clicked.connect(self.change_path)
        self.save_but.clicked.connect(self.save)

    def set_style(self, theme):
        self.setStyleSheet(theme.window_st)
        QApplication.setPalette(theme.window_pal)
        self.frame.setStyleSheet(theme.frame_st)
        self.title_lab.setStyleSheet(theme.label_st)
        self.to_user_but.setStyleSheet(theme.pushbut_st)
        self.to_themes_but.setStyleSheet(theme.pushbut_st)
        self.to_alb_view_but.setStyleSheet(theme.pushbut_st)
        self.change_photo_but.setStyleSheet(theme.pushbut_st)
        self.change_nik_but.setStyleSheet(theme.pushbut_st)
        self.change_path_but.setStyleSheet(theme.pushbut_st)
        self.change_login_but.setStyleSheet(theme.pushbut_st)
        self.change_password_but.setStyleSheet(theme.pushbut_st)
        self.nik_lab.setStyleSheet(theme.label_st)
        self.path_lab.setStyleSheet(theme.label_st)
        self.login_lab.setStyleSheet(theme.label_st)
        self.password_lab.setStyleSheet(theme.label_st)
        self.path_ed.setStyleSheet(theme.edit_st)
        self.login_ed.setStyleSheet(theme.edit_st)
        self.password_ed.setStyleSheet(theme.edit_st)
        self.save_but.setStyleSheet(theme.pushbut_st)

    def to_alb_view(self):
        self.settings = AlbumsSettings(self.parent)
        self.settings.show()
        self.hide()

    def to_themes(self):
        self.settings = ThemeSettings(self.parent)
        self.settings.show()
        self.hide()

    def change_nik(self):
        self.input_nik = QInputDialog(self)
        self.input_nik.setWindowTitle('Введите новый ник:')
        self.input_nik.show()

        label = self.input_nik.children()[1]
        label.setText("Каким именем будете называться?")
        label.setStyleSheet(self.theme.label_st)

        line_edit = self.input_nik.children()[0]
        line_edit.setText("")
        line_edit.setStyleSheet(self.theme.edit_st)

        ok_but = self.input_nik.children()[2].children()[1]
        ok_but.setText('Применить')
        cancel_but = self.input_nik.children()[2].children()[2]
        cancel_but.setText('Отмена')
        ok_but.setStyleSheet(self.theme.pushbut_st)
        cancel_but.setStyleSheet(self.theme.pushbut_st)
        ok_but.clicked.connect(self.change_cur_nik)

    def change_cur_nik(self):
        self.cur_nik = self.input_nik.children()[0].text()
        self.nik_lab.setText(self.cur_nik)
        self.nik_lab.setAlignment(Qt.AlignCenter if len(self.cur_nik) <= 17
                                  else Qt.AlignLeft | Qt.AlignVCenter)

    def change_photo(self):
        s = 'Картинка (*.png);;Картинка (*.jpg)'
        name, ok = QFileDialog.getOpenFileName(self, 'Выбрать фото', '', s)
        if ok:
            self.cur_photo = Image.open(name).resize((200, 200))
            self.cur_photo_name = name
            self.photo_lab.setPixmap(to_pixmap(self.cur_photo))

    def change_log_pas(self, button, mess=''):
        self.send_button = button
        text = button.text().split()[1]
        self.input_val = QInputDialog(self)
        self.input_val.setWindowTitle('Смена ' + ('пароля:' if text == 'пароль'
                                      else 'логина:'))
        self.input_val.show()

        label = self.input_val.children()[1]
        label.setText(mess + "Введите новый " + ('пароль.' if text == 'пароль'
                      else 'логин.'))
        label.setStyleSheet(self.theme.label_st)

        line_edit = self.input_val.children()[0]
        line_edit.setText("")
        line_edit.setStyleSheet(self.theme.edit_st)

        ok_but = self.input_val.children()[2].children()[1]
        ok_but.setText('Сменить')
        cancel_but = self.input_val.children()[2].children()[2]
        cancel_but.setText('Отмена')
        ok_but.setStyleSheet(self.theme.pushbut_st)
        cancel_but.setStyleSheet(self.theme.pushbut_st)
        ok_but.clicked.connect(self.change_cur_password
                               if text == 'пароль' else self.change_cur_login)

    def change_cur_password(self):
        password = self.input_val.children()[0].text()
        if len(password) < 6:
            self.input_val.hide()
            self.change_log_pas(self.send_button, 'Короткий пароль. ')
            return
        self.password = password
        self.password_ed.setText('*' * len(self.password))

    def change_cur_login(self):
        log = self.input_val.children()[0].text()
        cur = self.user_bd.cursor()
        if log in [el[0] for el in cur.execute('''SELECT Login FROM
 Users WHERE NOT Login = ?''', (self.login, ))] and log != self.login:
            print(log, self.login)
            self.input_val.hide()
            self.change_log_pas(self.send_button, 'Такой пользователь \
уже есть. ')
            return
        if not log:
            self.input_val.hide()
            self.change_log_pas(self.send_button, 'Вы не ввели логин. ')
        self.login = log
        self.login_ed.setText(self.login)

    def change_path(self):
        name = self.new_path[self.new_path.rfind('/') + 1:]\
            if '/' in self.new_path else self.new_path
        path = QFileDialog.getExistingDirectory(self, "Выбрать папку", ".")
        self.new_path = path + '/' + name if path else self.new_path
        self.path_ed.setText(self.new_path)

    def save(self):
        self.parent.photo = self.cur_photo
        self.parent.nik = self.cur_nik
        self.parent.nik_lab.setText(self.cur_nik)
        self.parent.nik_lab.setAlignment(Qt.AlignCenter
                                          if len(self.cur_nik) <= 17
                                          else Qt.AlignLeft |
                                          Qt.AlignVCenter)
        self.parent.photo_lab.setPixmap(to_pixmap(self.cur_photo))
        cur = self.parent.bd.cursor()
        cur.execute('''UPDATE Settings SET Name = '{}',
 Path_to_photo = '{}' '''.format(self.cur_nik, self.cur_photo_name))
        self.parent.bd.commit()
        cur = self.user_bd.cursor()
        cur.execute('''UPDATE Users SET Password = ?, Login = ?
 WHERE Login = ?''', (self.password, self.login, self.parent.login))
        self.parent.login = self.login
        if self.parent.path_to_bd != self.new_path:
            self.parent.bd.close()
            replace(self.parent.path_to_bd, self.new_path)
            self.parent.bd = sq.connect(self.new_path)
            for al in self.parent.albums:
                al.bd = self.parent.bd
                for im in al.images:
                    im.bd = self.parent.bd
            self.parent.path_to_bd = self.new_path
            cur.execute('''UPDATE Users SET Path_to_bd = ?
 WHERE Login = ?''', (self.new_path, self.login))
        self.user_bd.commit()
        self.user_bd.close()
        self.hide()


if __name__ == '__main__':
    sys.excepthook = excepthook
    app = QApplication(sys.argv)
    ex = LoginWindow()
    ex.show()
    sys.exit(app.exec())
