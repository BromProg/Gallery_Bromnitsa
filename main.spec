# -*- mode: python ; coding: utf-8 -*-


block_cipher = None


a = Analysis(['main.py'],
             pathex=['C:\\Users\\Rostislav\\Desktop\\Rostislav\\PyCharm_programms\\Bromnitsa\\Gallery_Bromnitsa'],
             binaries=[],
             datas=[('images\\favicon.ico', 'images'),
             ('images\\Default_image.png', 'images'),
             ('images\\Default_photo.png', 'images'),
             ('images\\Default_cover.png', 'images')],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)

exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='Bromnitsa',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=False, icon='C:\\Users\\Rostislav\\Desktop\\Rostislav\\PyCharm_programms\\Bromnitsa\\Gallery_Bromnitsa\\images\\favicon.ico')
