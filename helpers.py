from PyQt5 import QtGui
from PyQt5.QtWidgets import QLabel

DEFAULT_PHOTO = 'images/Default_photo.png'
DEFAULT_IMAGE = 'images/Default_image.png'
DEFAULT_COVER = 'images/Default_cover.png'
ICON = 'images/App_icon.png'
ALB_LABEL_FONT = '; font-size: 15px'


class ClickableLabel(QLabel):
    def __init__(self, parent, whenClicked, item):
        QLabel.__init__(self, parent)
        self.item = item
        self._whenClicked = whenClicked

    def mouseReleaseEvent(self, event):
        event.item = self.item
        self._whenClicked(event)


class Theme:
    def __init__(self, name):
        temy = {'СВЕТЛАЯ': (['background: #E8E7E7', '', '', '', '', '',
                             'QSlider::handle:vertical \
{height: 10px; background: #A798F2; margin: 0 -15px;}', '',
                             'background: #A798F2',
                             ''],
                            [(193, 182, 182), (54, 153, 228),
                             (255, 255, 255)]),
                'ТЁМНАЯ': (['background: rgb(18, 18, 18)',
                            'background: rgba(25, 25, 25, 0.5)',
                            'background: #211D2B; color: #D5CCBF',
                            'color: #494ECE', 'color: #D5CCBF',
                            'background: #25241F; color: #3ECAD4; \
border: #25241F',
                            'QSlider::groove:vertical {background: #0A154B; \
position: absolute; left: 16px; right: 16px;} QSlider::handle:vertical \
{height: 10px; background: #6D70CA; margin: 0 -15px;}',
                            'background: #25241F; color: #3ECAD4; \
border: #25241F',
                            'background: #160033',
                            'QScrollBar:vertical {background: #25241F; \
color: #3ECAD4} QScrollBar::handle:vertical {background-color: #3A3A3A;} \
QScrollBar::up-arrow:vertical, QScrollBar::down-arrow:vertical \
{ background: none; } QScrollBar::add-page:vertical, \
QScrollBar::sub-page:vertical {background: none;} \
QScrollBar:horizontal {background: #25241F; \
color: #3ECAD4} QScrollBar::handle:horizontal {background-color: #3A3A3A;} \
QScrollBar::left-arrow:horizontal, QScrollBar::right-arrow:horizontal \
{ background: none; } QScrollBar::add-page:horizontal, \
QScrollBar::sub-page:horizontal {background: none;} \
QScrollBar::add-line:horizontal, \
QScrollBar::sub-line:horizontal {background: none;}'],
                           [(91, 123, 121), (225, 209, 69), (36, 8, 8)]),
                'РЕТРО': (['background: rgb(166, 102, 58)',
                           'background: rgba(162, 95, 19, 0.5)',
                           'background: #57330F; color: #FF8000',
                           'color: #F2EAD8', 'color: #000000',
                           'background: #543200; color: #F5B46A; \
border: #543200',
                           'QSlider::groove:vertical {background: #351C00; \
position: absolute; left: 16px; right: 16px;} QSlider::handle:vertical \
{height: 10px; background: #FFAA01; margin: 0 -15px;}',
                           'background: #543200; color: #FFFFFF; \
border: #543200',
                           'background: #50330D',
                           'QScrollBar:vertical {background: #543200; \
color: #F5B46A} QScrollBar::handle:vertical {background-color: #804000;} \
QScrollBar::up-arrow:vertical, QScrollBar::down-arrow:vertical \
{ background: none; } QScrollBar::add-page:vertical, \
QScrollBar::sub-page:vertical {background: none;} \
QScrollBar:horizontal {background: #543200; \
color: #F5B46A} QScrollBar::handle:horizontal {background-color: #804000;} \
QScrollBar::left-arrow:horizontal, QScrollBar::right-arrow:horizontal \
{ background: none; } QScrollBar::add-page:horizontal, \
QScrollBar::sub-page:horizontal {background: none;} \
QScrollBar::add-line:horizontal, \
QScrollBar::sub-line:horizontal {background: none;}'],
                          [(131, 98, 60), (86, 228, 25), (57, 40, 1)]),
                'НЕОНОВАЯ': (['background: rgb(50, 53, 49)',
                              'background: rgba(61, 75, 57, 0.5)',
                              'background: #3C3C3B; color: #04FD0D',
                              'color: #0BFAFA', 'color: #0BFAFA',
                              'background: #2B2B2B; color: #F68B00; \
border: #2B2B2B',
                              'QSlider::groove:vertical {background: #FF9A00; \
position: absolute; left: 18px; right: 18px;} QSlider::handle:vertical \
{height: 10px; background: #F7FF00; margin: 0 -15px;}',
                              'background: #353335; color: #FF00FF; \
border: #353335',
                              'background: #AE0F0F',
                              'QScrollBar:vertical {background: #2B2B2B; \
color: #F68B00} QScrollBar::handle:vertical {background-color: #5A5A5A;} \
QScrollBar::up-arrow:vertical, QScrollBar::down-arrow:vertical \
{background: none;} QScrollBar::add-page:vertical, \
QScrollBar::sub-page:vertical {background: none;} \
QScrollBar:horizontal {background: #2B2B2B; \
color: #F68B00} QScrollBar::handle:horizontal {background-color: #5A5A5A;} \
QScrollBar::left-arrow:horizontal, QScrollBar::right-arrow:horizontal \
{background: none;} QScrollBar::add-page:horizontal, \
QScrollBar::sub-page:horizontal {background: none;} \
QScrollBar::add-line:horizontal, \
QScrollBar::sub-line:horizontal {background: none;}'],
                             [(255, 20, 20), (255, 239, 0), (54, 0, 54)])}
        tema = temy[name.upper()]
        self.name = name
        # Задаём stylesheet:
        # 0 - окно, 1 - фон, 2 - кнопка, 3 - радиокнопка, 4 - надпись
        # 5 - ввод, 6 - ползунок, 7 - ввод числа, 8 - регулятор, 9 - scroll
        self.window_st, self.frame_st = tema[0][0], tema[0][1]
        self.pushbut_st, self.radiobut_st = tema[0][2], tema[0][3]
        self.label_st, self.edit_st = tema[0][4], tema[0][5]
        self.slider_st = tema[0][6]
        self.spinbox_st = 'QSpinBox {' + tema[0][7] + '} QSpinBox::up-button \
{} QSpinBox::down-button {}'
        self.dial_st = tema[0][8]
        self.scroll_st = tema[0][9] + ' QScrollBar::sub-line:vertical \
{border-image: url(./images/up_arrow_disabled.png);} \
QScrollBar::add-line:vertical {border-image: \
url(./images/down_arrow_disabled.png);}'
        # Задаём palette:
        # 0 - ввод числа, 1 - фон выделенного, 2 - цвет выделенного
        self.spinbox_pal = QtGui.QPalette()
        self.spinbox_pal.setColor(QtGui.QPalette.Button,
                                  QtGui.QColor(*tema[1][0]))
        self.window_pal = QtGui.QPalette()
        self.window_pal.setColor(QtGui.QPalette.Highlight,
                                 QtGui.QColor(*tema[1][1]))
        self.window_pal.setColor(QtGui.QPalette.HighlightedText,
                                 QtGui.QColor(*tema[1][2]))


def to_pixmap(foto):
    '''Конвертирует PIL изображение в QPixmap'''
    foto = foto.convert("RGBA")
    qim = QtGui.QImage(foto.tobytes("raw", "RGBA"), foto.size[0],
                       foto.size[1], QtGui.QImage.Format_RGBA8888)
    return QtGui.QPixmap.fromImage(qim)


def excepthook(exc_type, exc_value, exc_tb):
    tb = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    print("Oбнаружeна ошибка:", tb)
    QtWidgets.QApplication.quit()
