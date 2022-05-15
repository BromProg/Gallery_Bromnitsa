import cv2
import numpy as np

from copy import deepcopy
from PIL import Image, ImageFilter
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QWidget, QInputDialog

from helpers import to_pixmap, DEFAULT_IMAGE, ICON
from ui_module import Ui_Image, Ui_Editor, Ui_ResizeDialog, Ui_SliceDialog


class MyImage(QWidget, Ui_Image):
    def __init__(self, im_id, path, name, parent):
        super().__init__()
        self.setupUi(self)

        # Задаём атрибуты:
        self.setWindowIcon(QIcon(ICON))
        self.parent, self.theme = parent, parent.theme
        self.bd = parent.bd
        self.tablename = parent.tablename
        self.im_id = im_id
        self.name = name
        try:
            self.in_image = Image.open(path)
            self.image = Image.open(path).resize((150, 150))
            self.image_path = path
        except FileNotFoundError as er:
            self.in_image = Image.open(DEFAULT_IMAGE)
            self.image = Image.open(DEFAULT_IMAGE).resize((150, 150))
            self.image_path = DEFAULT_IMAGE
        # Именно здесь, иначе QScrollArea не стилизуется.
        self.editor = Editor(self.in_image, self, do_all=False)

        # Задаём параметры окну:
        self.name_lab.setText(self.name)
        self.image_lab.setPixmap(to_pixmap(self.in_image))

        # Задаём стиль:
        self.set_style(self.theme)

        # Подключаем слоты к кнопкам:
        self.change_name_but.clicked.connect(self.change_name)
        self.delete_but.clicked.connect(self.delete)
        self.edit_but.clicked.connect(self.edit)

    def set_style(self, theme):
        self.setStyleSheet(theme.window_st)
        QApplication.setPalette(theme.window_pal)
        self.name_lab.setStyleSheet(theme.label_st)
        self.delete_but.setStyleSheet(theme.pushbut_st)
        self.edit_but.setStyleSheet(theme.pushbut_st)
        self.change_name_but.setStyleSheet(theme.pushbut_st)
        self.image_area.setStyleSheet(theme.scroll_st)

    def change_name(self):
        self.input_im_name = QInputDialog(self)
        self.input_im_name.setWindowTitle('Введите название изображения:')
        self.input_im_name.show()

        label = self.input_im_name.children()[1]
        label.setText("Какое дать название? (Будет изменено только внутри \
галереи).")
        label.setStyleSheet(self.theme.label_st)

        line_edit = self.input_im_name.children()[0]
        line_edit.setText("")
        line_edit.setStyleSheet(self.theme.edit_st)

        ok_but = self.input_im_name.children()[2].children()[1]
        ok_but.setText('Применить')
        cancel_but = self.input_im_name.children()[2].children()[2]
        cancel_but.setText('Отмена')
        ok_but.setStyleSheet(self.theme.pushbut_st)
        cancel_but.setStyleSheet(self.theme.pushbut_st)
        ok_but.clicked.connect(self.change_image_name)

    def change_image_name(self):
        self.name = self.input_im_name.children()[0].text()
        self.parent.print_images(self.parent.cur_images)
        self.name_lab.setText(self.name)
        cur = self.bd.cursor()
        cur.execute('''UPDATE {} SET Im_name = ?
 WHERE Im_id = ?'''.format(self.tablename), (self.name, self.im_id))
        self.bd.commit()

    def delete(self):
        self.ok_or_no = QInputDialog(self)
        self.ok_or_no.setWindowTitle('Подтвердите удаление:')
        self.ok_or_no.show()

        label = self.ok_or_no.children()[1]
        label.setText("Вы уверены, что хотите удалить \
изображение '{}'?".format(self.name))
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
        self.parent.images.remove(self)
        if self in self.parent.cur_images:
            self.parent.cur_images.remove(self)
        self.parent.print_images(self.parent.cur_images)
        cur = self.bd.cursor()
        cur.execute('''DELETE FROM {} WHERE
 Im_id = ?'''.format(self.tablename), (self.im_id, ))
        self.bd.commit()
        self.hide()

    def edit(self):
        self.editor.theme = self.theme
        self.editor.set_style(self.theme)
        self.editor.back()
        self.editor.show()


class Editor(QWidget, Ui_Editor):
    def __init__(self, image, parent, do_all=False):
        super().__init__()
        self.setupUi(self)

        # Задаём атрибуты:
        self.setWindowIcon(QIcon(ICON))
        self.parent, self.theme = parent, parent.theme
        self.im = deepcopy(image)
        self.cur_im = deepcopy(image)

        # Задаём параметры окну:
        if do_all:  # Нужно для ускорения загрузки Бромницы
            self.set_sliders_value(self.cur_im)
        self.image_lab.setPixmap(to_pixmap(self.cur_im))

        # Задаём стиль:
        self.set_style(self.theme)

        # Подключаем слоты к виджетам:
        self.apply_components.clicked.connect(self.change_component)
        self.apply_contrast.clicked.connect(self.change_contrast)
        self.back_but.clicked.connect(self.back)
        self.cartooner_but.clicked.connect(self.cartooner)
        self.blur_but.clicked.connect(self.blur)
        self.w_b_but.clicked.connect(self.w_b)
        self.invert_but.clicked.connect(self.invert)
        self.change_size_but.clicked.connect(self.change_size)
        self.slice_but.clicked.connect(self.slice)
        self.save_but.clicked.connect(self.save)

    def slice(self):
        self.dialog = SliceDialog(self.cur_im, self)
        self.dialog.show()

    def change_size(self):
        self.dialog = ResizeDialog(self.cur_im, self)
        self.dialog.show()

    def w_b(self):
        (x, y) = self.cur_im.size
        px = self.cur_im.load()
        for i in range(x):
            for j in range(y):
                if len(px[i, j]) == 4:
                    r, g, b, a = px[i, j]
                else:
                    r, g, b = px[i, j]
                av = (r + g + b) // 3
                px[i, j] = (av, av, av)
        self.image_lab.setPixmap(to_pixmap(self.cur_im))
        self.set_sliders_value(self.cur_im)
        self.contrast_dial.setValue(10)

    def invert(self):
        (x, y) = self.cur_im.size
        px = self.cur_im.load()
        for i in range(x):
            for j in range(y):
                if len(px[i, j]) == 4:
                    r, g, b, a = px[i, j]
                else:
                    r, g, b = px[i, j]
                px[i, j] = (255 - r, 255 - g, 255 - b)
        self.image_lab.setPixmap(to_pixmap(self.cur_im))
        self.set_sliders_value(self.cur_im)
        self.contrast_dial.setValue(10)

    def cartooner(self):
        try:
            px = self.cur_im.load()
            for i in range(self.cur_im.size[0]):
                for j in range(self.cur_im.size[1]):
                    px[i, j] = tuple(list(px[i, j])[0:3][::-1])
            img = np.array(self.cur_im)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            gray = cv2.medianBlur(gray, 5)
            edges = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
                                          cv2.THRESH_BINARY, 9, 9)
            color = cv2.bilateralFilter(img, 9, 250, 250)
            cartoon = cv2.bitwise_and(color, color, mask=edges)
            self.cur_im = Image.fromarray(cartoon)
            px = self.cur_im.load()
            for i in range(self.cur_im.size[0]):
                for j in range(self.cur_im.size[1]):
                    px[i, j] = px[i, j][::-1]
            self.image_lab.setPixmap(to_pixmap(self.cur_im))
            self.set_sliders_value(self.cur_im)
            self.contrast_dial.setValue(10)
        except Exception as ex:
            pass

    def blur(self):
        self.cur_im = self.cur_im.filter(ImageFilter.GaussianBlur(radius=5))
        self.image_lab.setPixmap(to_pixmap(self.cur_im))
        self.set_sliders_value(self.cur_im)
        self.contrast_dial.setValue(10)

    def set_style(self, theme):
        self.setStyleSheet(theme.window_st)
        QApplication.setPalette(theme.window_pal)
        self.title_lab.setStyleSheet(theme.label_st)
        self.b_lab.setStyleSheet(theme.label_st)
        self.r_lab.setStyleSheet(theme.label_st)
        self.g_lab.setStyleSheet(theme.label_st)
        self.save_but.setStyleSheet(theme.pushbut_st)
        self.back_but.setStyleSheet(theme.pushbut_st)
        self.invert_but.setStyleSheet(theme.pushbut_st)
        self.apply_contrast.setStyleSheet(theme.pushbut_st)
        self.apply_components.setStyleSheet(theme.pushbut_st)
        self.w_b_but.setStyleSheet(theme.pushbut_st)
        self.slice_but.setStyleSheet(theme.pushbut_st)
        self.blur_but.setStyleSheet(theme.pushbut_st)
        self.change_size_but.setStyleSheet(theme.pushbut_st)
        self.contrast_dial.setStyleSheet(theme.dial_st)
        self.red_sl.setStyleSheet(theme.slider_st)
        self.green_sl.setStyleSheet(theme.slider_st)
        self.blue_sl.setStyleSheet(theme.slider_st)
        self.image_area.setStyleSheet(theme.scroll_st)

    def set_sliders_value(self, im):
        (x, y) = im.size
        px, r_sum, g_sum, b_sum = im.load(), 0, 0, 0
        for i in range(x):
            for j in range(y):
                if len(px[i, j]) == 4:
                    r, g, b, a = px[i, j]
                else:
                    r, g, b = px[i, j]
                r_sum += r
                g_sum += g
                b_sum += b
        self.red_sl.setValue(r_sum // (x * y))
        self.green_sl.setValue(g_sum // (x * y))
        self.blue_sl.setValue(b_sum // (x * y))
        self.r_value, self.g_value = r_sum // (x * y), g_sum // (x * y)
        self.b_value = b_sum // (x * y)

    def change_component(self):
        r_coef = self.red_sl.value() / (self.r_value + 1)
        g_coef = self.green_sl.value() / (self.g_value + 1)
        b_coef = self.blue_sl.value() / (self.b_value + 1)
        (x, y) = self.cur_im.size
        px = self.cur_im.load()
        for i in range(x):
            for j in range(y):
                (r, g, b) = [i + 1 if i == 0 else i for i in px[i, j]][0:3]
                r = int(round(r * r_coef))
                g = int(round(g * g_coef))
                b = int(round(b * b_coef))
                px[i, j] = (r if r <= 255 else 255, g if g <= 255 else 255,
                            b if b <= 255 else 255)
        self.r_value = self.red_sl.value()
        self.g_value = self.green_sl.value()
        self.b_value = self.blue_sl.value()
        self.image_lab.setPixmap(to_pixmap(self.cur_im))

    def change_contrast(self):
        (x, y) = self.cur_im.size
        px = self.cur_im.load()
        for i in range(x):
            for j in range(y):
                px[i, j] = self.contr(px, i, j,
                                      gran=self.contrast_dial.value())
        self.set_sliders_value(self.cur_im)
        self.image_lab.setPixmap(to_pixmap(self.cur_im))

    def contr(self, pixels, i, j, delta=50, gran=123):
        sp, av = [], (pixels[i, j][0] + pixels[i, j][1] + pixels[i, j][2]) // 3
        for ind in range(3):
            sp.append(min(255, pixels[i, j][ind] + delta) if av > gran
                      else max(0, pixels[i, j][ind] - delta))
        return sp[0], sp[1], sp[2]

    def back(self):
        self.cur_im = deepcopy(self.im)
        self.image_lab.setPixmap(to_pixmap(self.cur_im))
        self.set_sliders_value(self.cur_im)
        self.contrast_dial.setValue(10)

    def save(self):
        self.input_im_name = QInputDialog(self)
        self.input_im_name.setWindowTitle('Введите название изображения:')
        self.input_im_name.show()

        label = self.input_im_name.children()[1]
        label.setText("Какое дать название? (Будет сохранено в той же папке).")
        label.setStyleSheet(self.theme.label_st)

        line_edit = self.input_im_name.children()[0]
        line_edit.setText("")
        line_edit.setStyleSheet(self.theme.edit_st)

        ok_but = self.input_im_name.children()[2].children()[1]
        ok_but.setText('Сохранить')
        cancel_but = self.input_im_name.children()[2].children()[2]
        cancel_but.setText('Отмена')
        ok_but.setStyleSheet(self.theme.pushbut_st)
        cancel_but.setStyleSheet(self.theme.pushbut_st)
        ok_but.clicked.connect(self.save_as)

    def save_as(self):
        n1 = self.parent.image_path[:self.parent.image_path.rfind('/') + 1]
        n2 = self.input_im_name.children()[0].text()
        n2 = ''.join([b for b in list(n2) if b not in r'>:«»/\?|*'])
        n3 = self.parent.image_path[self.parent.image_path.rfind('.'):]
        self.cur_im.save(n1 + n2 + n3)
        im = MyImage(0, n1 + n2 + n3, n2, self.parent.parent)
        cur = self.parent.bd.cursor()
        cur.execute('''INSERT INTO {}(Path_to_im, Im_name)
 VALUES(?, ?)'''.format(self.parent.tablename), (im.image_path, im.name))
        im.im_id = int(cur.execute('''SELECT Im_id FROM ''' +
                                   self.parent.tablename).fetchall()[-1][0])
        self.parent.parent.images.append(im)
        self.parent.parent.cur_images.append(im)
        self.parent.parent.print_images(self.parent.parent.cur_images)
        self.parent.bd.commit()


class ResizeDialog(QWidget, Ui_ResizeDialog):
    def __init__(self, image, parent):
        super().__init__()
        self.setupUi(self)

        # Задаём атрибуты:
        self.parent, self.theme = parent, parent.theme
        (self.x, self.y) = image.size

        # Задаём стиль:
        self.set_style(self.theme)

        # Задаём параметры окну:
        self.cur_size_lab.setText(str(self.x) + ' X ' + str(self.y))
        self.x_col_box.setValue(self.x)
        self.y_col_box.setValue(self.y)
        self.setWindowIcon(QIcon(ICON))

        # Подключаем слоты к виджетам:
        self.apply_but.clicked.connect(self.apply_size)

    def set_style(self, theme):
        self.setStyleSheet(theme.window_st)
        QApplication.setPalette(theme.window_pal)
        self.size_lab.setStyleSheet(theme.label_st)
        self.cur_size_lab.setStyleSheet(theme.label_st)
        self.x_lab.setStyleSheet(theme.label_st)
        self.y_lab.setStyleSheet(theme.label_st)
        self.x_col_box.setStyleSheet(theme.spinbox_st)
        self.x_col_box.setPalette(theme.spinbox_pal)
        self.y_col_box.setStyleSheet(theme.spinbox_st)
        self.y_col_box.setPalette(theme.spinbox_pal)
        self.apply_but.setStyleSheet(theme.pushbut_st)

    def apply_size(self):
        new = self.parent.cur_im.resize((self.x_col_box.value(),
                                         self.y_col_box.value()))
        self.parent.cur_im = new
        self.parent.image_lab.setPixmap(to_pixmap(new))
        self.hide()


class SliceDialog(QWidget, Ui_SliceDialog):
    def __init__(self, image, parent):
        super().__init__()
        self.setupUi(self)

        # Задаём атрибуты:
        self.parent, self.theme = parent, parent.theme
        (self.x, self.y) = image.size

        # Задаём стиль:
        self.set_style(self.theme)

        # Задаём параметры окну:
        self.cur_size_lab.setText(str(self.x) + ' X ' + str(self.y))
        self.x1_box.setMaximum(self.x - 2)
        self.y1_box.setMaximum(self.y - 2)
        self.x2_box.setMinimum(1)
        self.y2_box.setMinimum(1)
        self.x2_box.setMaximum(self.x - 1)
        self.y2_box.setMaximum(self.y - 1)
        self.x2_box.setValue(self.x - 1)
        self.y2_box.setValue(self.y - 1)
        self.setWindowIcon(QIcon(ICON))

        # Подключаем слоты к виджетам:
        self.x1_box.valueChanged.connect(self.correct_x_to_max)
        self.x2_box.valueChanged.connect(self.correct_x_to_min)
        self.y1_box.valueChanged.connect(self.correct_y_to_max)
        self.y2_box.valueChanged.connect(self.correct_y_to_min)
        self.apply_but.clicked.connect(self.apply_slice)

    def set_style(self, theme):
        self.setStyleSheet(theme.window_st)
        QApplication.setPalette(theme.window_pal)
        self.size_lab.setStyleSheet(theme.label_st)
        self.cur_size_lab.setStyleSheet(theme.label_st)
        self.begin_coords_lab.setStyleSheet(theme.label_st)
        self.end_coords_lab.setStyleSheet(theme.label_st)
        self.x1_box.setStyleSheet(theme.spinbox_st)
        self.x1_box.setPalette(theme.spinbox_pal)
        self.y1_box.setStyleSheet(theme.spinbox_st)
        self.y1_box.setPalette(theme.spinbox_pal)
        self.x2_box.setStyleSheet(theme.spinbox_st)
        self.x2_box.setPalette(theme.spinbox_pal)
        self.y2_box.setStyleSheet(theme.spinbox_st)
        self.y2_box.setPalette(theme.spinbox_pal)
        self.apply_but.setStyleSheet(theme.pushbut_st)

    def correct_x_to_max(self):
        self.x2_box.setMinimum(self.x1_box.value() + 1)

    def correct_x_to_min(self):
        self.x1_box.setMaximum(self.x2_box.value() - 1)

    def correct_y_to_max(self):
        self.y2_box.setMinimum(self.y1_box.value() + 1)

    def correct_y_to_min(self):
        self.y1_box.setMaximum(self.y2_box.value() - 1)

    def apply_slice(self):
        new = self.parent.cur_im.crop((self.x1_box.value(),
                                       self.y1_box.value(),
                                       self.x2_box.value(),
                                       self.y2_box.value()))
        self.parent.cur_im = new
        self.parent.image_lab.setPixmap(to_pixmap(new))
        self.hide()
