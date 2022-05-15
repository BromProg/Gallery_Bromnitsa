from math import ceil
from PIL import Image
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QInputDialog,\
    QFileDialog

from helpers import to_pixmap, ClickableLabel, DEFAULT_COVER, ICON
from ui_module import Ui_Album, Ui_AlbumSettings
from image_module import MyImage


class Album(QWidget, Ui_Album):
    def __init__(self, parent, tablename):
        super().__init__()
        self.setupUi(self)

        # Задаём атрибуты:
        self.im_labels, self.im_name_labels = [], []

        self.parent, self.theme = parent, parent.theme
        self.bd = parent.bd
        self.tablename = tablename
        cur = self.bd.cursor()
        images = cur.execute('''SELECT Im_id, path_to_im, Im_name
 FROM ''' + self.tablename).fetchall()
        self.images = [MyImage(int(im[0]), im[1], im[2], self) for im in images
                       if im[1] is not None and im[2] is not None]

        al = cur.execute('''SELECT Name, path_to_cover, N_col
 FROM ''' + self.tablename).fetchone()
        self.name = al[0]
        self.cur_images = self.images.copy()
        try:
            self.cover = Image.open(al[1]).resize((150, 150))
            self.in_cover = Image.open(al[1]).resize((200, 200))
            self.cover_path = al[1]
        except FileNotFoundError as er:
            self.cover = Image.open(DEFAULT_COVER).resize((150, 150))
            self.in_cover = Image.open(DEFAULT_COVER).resize((200, 200))
            self.cover_path = DEFAULT_COVER
        self.n_col = int(al[2])

        # Задаём параметры окну:
        self.alb_name_lab.setText(self.name)
        self.alb_name_lab.setAlignment(Qt.AlignCenter if len(self.name) <= 19
                                       else Qt.AlignLeft | Qt.AlignVCenter)
        self.cover_lab.setPixmap(to_pixmap(self.in_cover))
        self.setWindowIcon(QIcon(ICON))

        # Задаём стиль:
        self.set_style(self.theme)

        # Отображаем изображения:
        self.print_images(self.cur_images)

        # Подключаем к виджетам слоты:
        self.search_but.clicked.connect(self.search)
        self.download_but.clicked.connect(self.add_image)
        self.delete_but.clicked.connect(self.delete)
        self.settings_but.clicked.connect(self.open_settings)
        self.scroll.valueChanged.connect(self.reprint)

    def reprint(self, val=0):
        self.print_images(self.cur_images)

    def im_clicked(self, event):
        self.opened_image = event.item
        self.opened_image.tema = self.theme
        self.opened_image.set_style(self.theme)
        self.opened_image.show()

    def add_image(self):
        s = 'Картинка (*.png);;Картинка (*.jpg)'
        name, ok = QFileDialog.getOpenFileName(self, 'Выбрать фото', '', s)
        if ok:
            im = MyImage(0, name, name[name.rfind("/") + 1:name.rfind(".")],
                         self)
            cur = self.bd.cursor()
            cur.execute('''INSERT INTO {}(Path_to_im, Im_name)
 VALUES(?, ?)'''.format(self.tablename), (im.image_path, im.name))
            self.bd.commit()
            cur = self.bd.cursor()
            im.im_id = int(cur.execute('''SELECT Im_id
FROM ''' + self.tablename).fetchall()[-1][0])
            self.images.append(im)
            self.cur_images.append(im)
            self.print_images(self.cur_images)

    def delete(self):
        self.ok_or_no = QInputDialog(self)
        self.ok_or_no.setWindowTitle('Подтвердите удаление:')
        self.ok_or_no.show()

        label = self.ok_or_no.children()[1]
        label.setText("Вы уверены, что хотите удалить \
альбом '{}'?".format(self.name))
        label.setStyleSheet(self.theme.label_st)

        line_edit = self.ok_or_no.children()[0]
        line_edit.hide()

        ok_but = self.ok_or_no.children()[2].children()[1]
        ok_but.setText('Да')
        cancel_but = self.ok_or_no.children()[2].children()[2]
        cancel_but.setText('Нет')
        ok_but.setStyleSheet(self.theme.pushbut_st)
        cancel_but.setStyleSheet(self.theme.pushbut_st)
        ok_but.clicked.connect(self.delete_self)

    def delete_self(self):
        self.parent.albums.remove(self)
        if self in self.parent.cur_albums:
            self.parent.cur_albums.remove(self)
        self.parent.print_albums(self.parent.cur_albums)
        cur = self.bd.cursor()
        cur.execute('''DROP TABLE ''' + self.tablename)
        self.bd.commit()
        self.hide()

    def open_settings(self):
        self.settings = AlbumSettings(self)
        self.settings.show()

    def search(self):
        self.cur_images = [im for im in self.images
                           if self.search_ed.text().lower() in im.name.lower()]
        self.print_images(self.cur_images)

    def set_style(self, theme):
        self.setStyleSheet(theme.window_st)
        self.title_lab.setStyleSheet(theme.label_st)
        self.alb_name_lab.setStyleSheet(theme.label_st)
        self.search_but.setStyleSheet(theme.pushbut_st)
        self.download_but.setStyleSheet(theme.pushbut_st)
        self.delete_but.setStyleSheet(theme.pushbut_st)
        self.settings_but.setStyleSheet(theme.pushbut_st)
        self.search_ed.setStyleSheet(theme.edit_st)
        self.search_ed.setPalette(theme.window_pal)
        QApplication.setPalette(theme.window_pal)
        self.scroll.setStyleSheet(theme.scroll_st)
        self.print_images(self.cur_images)

    def print_images(self, images):
        # Убираем старые label:
        for al in self.im_labels:
            al.hide()
        for nam in self.im_name_labels:
            nam.hide()
        self.im_labels, self.im_name_labels = [], []

        # Задаём максимальное значение scroll исходя из количества альбомов:
        n = int(ceil(len(images) / self.n_col))
        self.scroll.setMaximum(n - 1 if len(images) / self.n_col >= 1 else 0)
        begin = self.scroll.value()

        # Отображаем изображения:
        x, y = 260, 63
        images = sorted(images, key=lambda x: x.name)
        for im_list in [images[i:i + self.n_col]
                        for i in range(0, len(images), self.n_col)][begin:]:
            for image in im_list:
                self.l1 = ClickableLabel(self, self.im_clicked, image)
                self.l1.setPixmap(to_pixmap(image.image))
                self.l1.setGeometry(x, y, 150, 150)
                self.l1.move(x, y)
                self.l1.show()
                self.im_labels.append(self.l1)

                self.l2 = QLabel(image.name, self)
                self.l2.setGeometry(x, y + 160, 150, 30)
                self.l2.move(x, y + 150)
                self.l2.setAlignment(Qt.AlignCenter if len(image.name) <= 18
                                     else Qt.AlignLeft | Qt.AlignVCenter)
                self.l2.setStyleSheet(self.theme.label_st +
                                      '; font-size: 15px')
                self.l2.show()
                self.im_name_labels.append(self.l2)
                x += 170
            x = 260
            y += 200  # Ниже


class AlbumSettings(QWidget, Ui_AlbumSettings):
    def __init__(self, parent):
        super().__init__()
        self.setupUi(self)

        # Задаём атрибуты:
        self.parent, self.theme = parent, parent.theme
        self.cur_name = parent.name
        self.cur_cover = parent.cover
        self.cur_in_cover = parent.in_cover
        self.cover_path = parent.cover_path

        # Задаём параметры окну:
        self.n_col_box.setValue(parent.n_col)
        nm = self.cur_name
        self.alb_name_lab.setText(nm if len(nm) <= 19 else nm[:16] + '...')
        self.cover_lab.setPixmap(to_pixmap(self.cur_in_cover))
        self.setWindowIcon(QIcon(ICON))

        # Задаём стиль:
        self.set_style(self.theme)

        # Подключаем к кнопкам слоты:
        self.save_but.clicked.connect(self.save)
        self.change_alb_name_but.clicked.connect(self.change_alb_name)
        self.change_cover_but.clicked.connect(self.change_cover)

    def set_style(self, theme):
        QApplication.setPalette(theme.window_pal)
        self.setStyleSheet(theme.window_st)
        self.title_lab.setStyleSheet(theme.label_st)
        self.alb_fone.setStyleSheet(theme.frame_st)
        self.col_fone.setStyleSheet(theme.frame_st)
        self.n_col_box.setStyleSheet(theme.spinbox_st)
        self.n_col_box.setPalette(theme.spinbox_pal)
        self.col_lab.setStyleSheet(theme.label_st)
        self.alb_name_lab.setStyleSheet(theme.label_st)
        self.change_alb_name_but.setStyleSheet(theme.pushbut_st)
        self.change_cover_but.setStyleSheet(theme.pushbut_st)
        self.save_but.setStyleSheet(theme.pushbut_st)

    def change_alb_name(self):
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
        canc_but = self.input_alb_name.children()[2].children()[2]
        canc_but.setText('Отмена')
        ok_but.setStyleSheet(self.theme.pushbut_st)
        canc_but.setStyleSheet(self.theme.pushbut_st)
        ok_but.clicked.connect(self.change_cur_name)

    def change_cur_name(self):
        self.cur_name = self.input_alb_name.children()[0].text()
        self.alb_name_lab.setText(self.cur_name)
        self.alb_name_lab.setAlignment(Qt.AlignCenter
                                       if len(self.cur_name) <= 19
                                       else Qt.AlignLeft | Qt.AlignVCenter)

    def change_cover(self):
        s = 'Картинка (*.png);;Картинка (*.jpg)'
        name, ok = QFileDialog.getOpenFileName(self, 'Выбрать фото', '', s)
        if ok:
            self.cur_cover = Image.open(name).resize((150, 150))
            self.cur_in_cover = Image.open(name).resize((200, 200))
            self.cover_path = name
            self.cover_lab.setPixmap(to_pixmap(self.cur_in_cover))

    def save(self):
        self.parent.n_col = self.n_col_box.value()
        self.parent.name = self.cur_name
        self.parent.cover = self.cur_cover
        self.parent.in_cover = self.cur_in_cover
        self.parent.cover_path = self.cover_path
        self.parent.alb_name_lab.setText(self.cur_name)
        self.parent.alb_name_lab.setAlignment(Qt.AlignCenter
                                               if len(self.cur_name) <= 19
                                               else Qt.AlignLeft |
                                               Qt.AlignVCenter)
        self.parent.cover_lab.setPixmap(to_pixmap(self.cur_in_cover))
        self.parent.print_images(self.parent.images)
        self.parent.parent.print_albums(self.parent.parent.albums)
        cur = self.parent.bd.cursor()
        cur.execute('''UPDATE {} SET Name = ?, Path_to_cover = ?,
 N_col = ?'''.format(self.parent.tablename),
                    (self.cur_name, self.cover_path,
                     self.n_col_box.value()))
        self.parent.bd.commit()
        self.hide()
