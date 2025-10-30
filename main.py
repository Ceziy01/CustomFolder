from PyQt6.QtWidgets import QApplication, QLabel, QMainWindow, QVBoxLayout, QWidget, QSlider, QPushButton, QHBoxLayout, QGridLayout, QScrollArea
from PyQt6.QtCore import Qt, QBuffer, QIODevice, QRect, QPoint
from PyQt6.QtGui import QPixmap, QPainter, QFont, QColor
from PIL import Image, ImageEnhance
import numpy as np
import colorsys, io, os, ctypes, sys, subprocess, win32api

def shiftHueNP(image, shift):
    image = image.convert('RGBA')
    arr = np.array(image).astype('float32') / 255.0
    rgb = arr[..., :3]
    alpha = arr[..., 3:]
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    h, s, v = np.vectorize(colorsys.rgb_to_hsv)(r, g, b)
    h = (h + shift) % 1.0
    r, g, b = np.vectorize(colorsys.hsv_to_rgb)(h, s, v)
    new_rgb = np.stack([r, g, b], axis=-1)
    new_arr = np.concatenate([new_rgb, alpha], axis=-1)
    new_arr = (new_arr * 255).astype('uint8')
    return Image.fromarray(new_arr, mode='RGBA')

def emojiToPil(emoji, size=100):
    extra = size // 2
    canvas_size = size + extra
    pix = QPixmap(canvas_size, canvas_size)
    pix.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pix)
    font = QFont("Segoe UI Emoji", size)
    painter.setFont(font)
    painter.setPen(QColor(0,0,0))
    painter.drawText(QRect(0, 0, canvas_size, canvas_size), Qt.AlignmentFlag.AlignCenter, emoji)
    painter.end()
    buffer = QBuffer()
    buffer.open(QIODevice.OpenModeFlag.ReadWrite)
    pix.save(buffer, "PNG")
    img = Image.open(io.BytesIO(buffer.data()))
    bbox = img.getbbox()
    if bbox:
        img = img.crop(bbox)
    return img

def addEmojiCenter(img, emoji, size_ratio=0.2):
    if not emoji:
        return img
    size = int(min(img.width, img.height) * size_ratio)
    emoji_img = emojiToPil(emoji, size=size)
    pos = ((img.width - emoji_img.width)//2, int((img.height - emoji_img.height)*1.3)//2)
    img.paste(emoji_img, pos, emoji_img)
    return img

if getattr(sys, "frozen", False):
    exe_dir = os.path.dirname(sys.executable)
else:
    exe_dir = os.path.dirname(os.path.abspath(__file__))

class ColorAdjuster(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Custom folder")
        self.resize(400, 200)
        self.original = None
        self.current_img = None
        self.selected_emoji = ""

        self.image_label = QLabel(alignment=Qt.AlignmentFlag.AlignCenter)
        self.image_label.setFixedSize(100, 100)
        self.img_div = QVBoxLayout()
        self.img_div.setContentsMargins(50, 50, 50, 50)
        self.img_div.addWidget(self.image_label)

        self.hue_slider = self.makeSlider(-50, 50, 0, "Hue")
        self.sat_slider = self.makeSlider(0, 200, 100, "Saturation")
        self.bri_slider = self.makeSlider(0, 200, 100, "Brightness")

        self.reset_button = QPushButton("Сбросить")
        self.reset_button.clicked.connect(self.resetSliders)
        self.save_button = QPushButton("Установить как иконку")
        self.save_button.clicked.connect(self.setIcon)

        self.emoji_button = QPushButton("Выбрать эмодзи")
        self.emoji_button.clicked.connect(self.toggleEmojiPopup)

        self.createEmojiPopup()

        sliders_layout = QVBoxLayout()
        sliders_layout.addWidget(self.reset_button)
        sliders_layout.addWidget(self.save_button)
        sliders_layout.addWidget(self.emoji_button)
        sliders_layout.addWidget(self.hue_slider['label'])
        sliders_layout.addWidget(self.hue_slider['slider'])
        sliders_layout.addWidget(self.sat_slider['label'])
        sliders_layout.addWidget(self.sat_slider['slider'])
        sliders_layout.addWidget(self.bri_slider['label'])
        sliders_layout.addWidget(self.bri_slider['slider'])
        sliders_layout.addStretch()

        main_layout = QHBoxLayout()
        main_layout.addLayout(self.img_div, stretch=3)
        main_layout.addLayout(sliders_layout, stretch=1)
        container_main = QWidget()
        container_main.setLayout(main_layout)
        self.setCentralWidget(container_main)

        self.original = Image.open(os.path.join(exe_dir, "folder.png")).convert("RGBA")
        max_w, max_h = 800, 600
        self.original.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)
        self.updateImage()
        self.loadData()
        
    def closeEvent(self, event):
        print("закрыто")
        dir = sys.argv[1]
        ini = f"{dir}/desktop.ini"
        icon = f"{dir}/icon.ico"
        if os.path.exists(ini): subprocess.run(["attrib","+H",ini],check=True, shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
        if os.path.exists(icon): subprocess.run(["attrib","+H",icon],check=True, shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
        
    def loadData(self):
        ini = sys.argv[1]+"/desktop.ini"
        if os.path.exists(ini): 
            win32api.SetFileAttributes(ini, 0)
            with open(ini, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith(";") or line.startswith("#") or line.startswith("["):
                        continue
                    if "=" in line:
                        k, v = line.split("=", 1)
                        if k.strip().lower() == "hue":
                            self.hue_slider["slider"].setValue(int(v.strip()))
                        if k.strip().lower() == "emoji":
                            self.selected_emoji = chr(int(v.strip()))
        self.updateImage()

    def createEmojiPopup(self):
        self.emoji_popup = QWidget(self, Qt.WindowType.Popup)
        self.emoji_popup.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.emoji_popup.setFixedSize(345, 200)

        scroll = QScrollArea(self.emoji_popup)
        scroll.setWidgetResizable(True)
        scroll.setGeometry(0,0, self.emoji_popup.width(), self.emoji_popup.height())

        container = QWidget()
        scroll.setWidget(container)
        layout = QVBoxLayout()
        container.setLayout(layout)

        sections = {
            "Smileys": ["😀", "😃", "😄", "😁", "😆", "😅", "😂", "🤣", "🥲", "🥹", "☺️", "😊", "😇", "🙂", "🙃", "😉", "😌", "😍", "🥰", "😘", " 😗", "😙", "😚", "😋", "😛", "😝", "😜", "🤪", "🤨", "🧐", "🤓", "😎", "🥸", "🤩", "🥳", "🙂‍↕️", "😏", "😒", "🙂‍↔️", "😞", "😔", "😟", "😕", "🙁", "☹️", "😣", "😖", "😫", "😩", "🥺", "😢", "😭", "😮‍💨", "😤", "😠", "😡", "🤬", "🤯", "😳", "🥵", "🥶", "😱", "😨", "😰", "😥", "😓", "🫣", "🤗", "🫡", "🤔", "🫢", "🤭", "🤫", "🤥", "😶", "😶‍🌫️", "😐", "😑", "😬", "🫨", "🫠", "🙄", "😯", "😦", "😧", "😮", "😲", "🥱", "😴", "🤤", "😪", "😵", "😵‍💫", "🫥", "🤐", "🥴", "🤢", "🤮", "🤧", "😷", "🤒", "🤕", "🤑", "🤠", "😈", "👿", "👹", "👺", "🤡", "💩", "👻", "💀", "☠️", "👽", "👾", "🤖", "🎃", "😺", "😸", "😹", "😻", "😼", "😽", "🙀", "😿", "😾"],
            "Clothing and Accessories": ["🧳", "🌂", "☂️", "🧵", "🪡", "🪢", "🪭", "🧶", "👓", "🕶", "🥽", "🥼", "🦺", "👔", "👕", "👖", "🧣", "🧤", "🧥", "🧦", "👗", "👘", "🥻", "🩴", "🩱", "🩲", "🩳", "👙", "👚", "👛", "👜", "👝", "🎒", "👞", "👟", "🥾", "🥿", "👠", "👡", "🩰", "👢", "👑", "👒", "🎩", "🎓", "🧢", "⛑", "🪖", "💄", "💍"],
            "Animals and Nature": ["🐶", "🐱", "🐭", "🐹", "🐰", "🦊", "🐻", "🐼", "🐻‍❄️", "🐨", "🐯", "🦁", "🐮", "🐷", "🐽", "🐸", "🐵", "🙈", "🙉", "🙊", "🐒", "🐔", "🐧", "🐦", "🐦‍⬛", "🐤", "🐣", "🐥", "🦆", "🦅", "🦉", "🦇", "🐺", "🐗", "🐴", "🦄", "🐝", "🪱", "🐛", "🦋", "🐌", "🐞", "🐜", "🪰", "🪲", "🪳", "🦟", "🦗", "🕷", "🕸", "🦂", "🐢", "🐍", "🦎", "🦖", "🦕", "🐙", "🦑", "🦐", "🦞", "🦀", "🪼", "🪸", "🐡", "🐠", "🐟", "🐬", "🐳", "🐋", "🦈", "🐊", "🐅", "🐆", "🦓", "🫏", "🦍", "🦧", "🦣", "🐘", "🦛", "🦏", "🐪", "🐫", "🦒", "🦘", "🦬", "🐃", "🐂", "🐄", "🐎", "🐖", "🐏", "🐑", "🦙", "🐐", "🦌", "🫎", "🐕", "🐩", "🦮", "🐕‍🦺", "🐈", "🐈‍⬛", "🪽", "🪶", "🐓", "🦃", "🦤", "🦚", "🦜", "🦢", "🪿", "🦩", "🕊", "🐇", "🦝", "🦨", "🦡", "🦫", "🦦", "🦥", "🐁", "🐀", "🐿", "🦔", "🐾", "🐉", "🐲", "🐦‍🔥", "🌵", "🎄", "🌲", "🌳", "🪾", "🌴", "🪹", "🪺", "🪵", "🌱", "🌿", "☘️", "🍀", "🎍", "🪴", "🎋", "🍃", "🍂", "🍁", "🍄", "🍄‍🟫", "🐚", "🪨", "🌾", "💐", "🌷", "🪷", "🌹", "🥀", "🌺", "🌸", "🪻", "🌼   🌼", "🌻", "🌞", "🌝", "🌛", "🌜", "🌚", "🌕", "🌖", "🌗", "🌘", "🌑", "🌒", "🌓", "🌔", "🌙", "🌎", "🌍", "🌏", "🪐", "💫", "⭐️", "🌟", "✨", "⚡️", "☄️", "💥", "🔥", "🌪", "🌈", "☀️", "🌤", "⛅️", "🌥", "☁️", "🌦", "🌧", "⛈", "🌩", "🌨", "❄️", "☃️", "⛄️", "🌬", "💨", "💧", "💦", "🫧", "☔️", "☂️", "🌊"],
            "Food and Drinks": ["🍏", "🍎", "🍐", "🍊", "🍋", "🍋‍🟩", "🍌", "🍉", "🍇", "🍓", "🫐", "🍈", "🍒", "🍑", "🥭", "🍍", "🥥", "🥝", "🍅", "🍆", "🥑", "🥦", "🫛", "🥬", "🫜", "🥒", "🌶", "🫑", "🌽", "🥕", "🫒", "🧄", "🧅", "🫚", "🥔", "🍠", "🫘", "🥐", "🥯", "🍞", "🥖", "🥨", "🧀", "🥚", "🍳", "🧈", "🥞", "🧇", "🥓", "🥩", "🍗", "🍖", "🦴", "🌭", "🍔", "🍟", "🍕", "🫓", "🥪", "🥙", "🧆", "🌮", "🌯", "🫔", "🥗", "🥘", "🫕", "🥫", "🍝", "🍜", "🍲", "🍛", "🍣", "🍱", "🥟", "🦪", "🍤", "🍙", "🍚", "🍘", "🍥", "🥠", "🥮", "🍢", "🍡", "🍧", "🍨", "🍦", "🥧", "🧁", "🍰", "🎂", "🍮", "🍭", "🍬", "🍫", "🍿", "🍩", "🍪", "🌰", "🥜", "🍯", "🥛", "🍼", "🫖", "☕️", "🍵", "🧃", "🥤", "🧋", "🫙", "🍶", "🍺", "🍻", "🥂", "🍷", "🫗", "🥃", "🍸", "🍹", "🧉", "🍾", "🧊", "🥄", "🍴", "🍽", "🥣", "🥡", "🥢"],
            "Activity and Sports": ["⚽️", "🏀", "🏈", "⚾️", "🥎", "🎾", "🏐", "🏉", "🥏", "🎱", "🪀", "🏓", "🏸", "🏒", "🏑", "🥍", "🏏", "🪃", "🥅", "⛳️", "🪁", "🏹", "🎣", "🤿", "🥊", "🥋", "🎽", "🛹", "🛼", "🛷", "⛸", "🥌", "🎿", "⛷", "🏂", "🪂", "🏋️‍♀️", "🏋️", "🏋️‍♂️", "🤼‍♀️", "🤼", "🤼‍♂️", "🤸‍♀️", "🤸", "🤸‍♂️", "⛹️‍♀️", "⛹️", "⛹️‍♂️", "🤺", "🤾‍♀️", "🤾", "🤾‍♂️", "🏌️‍♀️", "🏌️", "🏌️‍♂️", "🏇", "🧘‍♀️", "🧘", "🧘‍♂️", "🏄‍♀️", "🏄", "🏄‍♂️", "🏊‍♀️", "🏊", "🏊‍♂️", "🤽‍♀️", "🤽", "🤽‍♂️", "🚣‍♀️", "🚣", "🚣‍♂️", "🧗‍♀️", "🧗", "🧗‍♂️", "🚵‍♀️", "🚵", "🚵‍♂️", "🚴‍♀️", "🚴", "🚴‍♂️", "🏆", "🥇", "🥈", "🥉", "🏅", "🎖", "🏵", "🎗", "🎫", "🎟", "🎪", "🤹", "🤹‍♂️", "🤹‍♀️", "🎭", "🩰", "🎨", "🎬", "🎤", "🎧", "🎼", "🎹", "🥁", "🪘", "🪇", "🎷", "🎺", "🪗", "🎸", "🪕", "🎻", "🪈", "🎲", "♟", "🎯", "🎳", "🎮", "🎰"],
            "Objects": ["⌚️", "📱", "📲", "💻", "⌨️", "🖥", "🖨", "🖱", "🖲", "🕹", "🗜", "💽", "💾", "💿", "📀", "📼", "📷", "📸", "📹", "🎥", "📽", "🎞", "📞", "☎️", "📟", "📠", "📺", "📻", "🎙", "🎚", "🎛", "🧭", "⏱", "⏲", "⏰", "🕰", "⌛️", "⏳", "📡", "🔋", "🪫", "🔌", "💡", "🔦", "🕯", "🪔", "🧯", "🛢", "🛍️", "💸", "💵", "💴", "💶", "💷", "🪙", "💰", "💳", "💎", "⚖️", "🪮", "🪜", "🧰", "🪛", "🔧", "🔨", "⚒", "🛠", "⛏", "🪚", "🔩", "⚙️", "🪤", "🧱", "⛓", "⛓️‍💥", "🧲", "🔫", "💣", "🧨", "🪓", "🔪", "🗡", "⚔️", "🛡", "🚬", "⚰️", "🪦", "⚱️", "🏺", "🔮", "📿", "🧿", "🪬", "💈", "⚗️", "🔭", "🔬", "🕳", "🩹", "🩺", "🩻", "🩼", "💊", "💉", "🩸", " 🧬", "🦠", "🧫", "🧪", "🌡", "🧹", "🪠", "🧺", "🧻", "🚽", "🚰", "🚿", "🛁", "🛀", "🧼", "🪥", "🪒", "🧽", "🪣", "🧴", "🛎", "🔑", "🗝", "🚪", "🪑", "🛋", "🛏", "🛌", "🧸", "🪆", "🖼", "🪞", "🪟", "🛍", "🛒", "🎁", "🎈", "🎏", "🎀", "🪄", "🪅", "🎊", "🎉", "🪩", "🎎", "🏮", "🎐", "🧧", "✉️", "📩", "📨", "📧", "💌", "📥", "📤", "📦", "🏷", "🪧", "📪", "📫", "📬", "📭", "📮", "📯", "📜", "📃", "📄", "📑", "🧾", "📊", "📈", "📉", "🗒", "🗓", "📆", "📅", "🗑", "🪪", "📇", "🗃", "🗳", "🗄", "📋", "📁", "  📂", "🗂", "🗞", "📰", "📓", "📔", "📒", "📕", "📗", "📘", "📙", "📚", "📖", "🔖", "🧷", "🔗", "📎", "🖇", "📐", "📏", "🧮", "📌", "📍", "✂️", "🖊", "🖋", "✒️", "🖌", "🖍", "📝", "✏️", "🔍", "🔎", "🔏", "🔐", "🔒", "🔓"]
        }

        for name, emojis in sections.items():
            lbl = QLabel(name)
            lbl.setStyleSheet("font-weight: bold; color: white;")
            layout.addWidget(lbl)

            grid = QGridLayout()
            grid.setSpacing(3)
            for idx, e in enumerate(emojis):
                btn = QPushButton(e)
                btn.setFixedSize(40, 40)
                btn.clicked.connect(lambda _, em=e: self.setEmoji(em))
                row, col = divmod(idx, 7)
                grid.addWidget(btn, row, col)
            wrapper = QWidget()
            wrapper.setLayout(grid)
            layout.addWidget(wrapper)

        layout.addStretch()

    def toggleEmojiPopup(self):
        if self.emoji_popup.isVisible():
            self.emoji_popup.hide()
        else:
            pos = self.emoji_button.mapToGlobal(QPoint(0, self.emoji_button.height()))
            self.emoji_popup.move(pos)
            self.emoji_popup.show()

    def setEmoji(self, emoji):
        self.selected_emoji = emoji
        self.updateImage()
        self.emoji_popup.hide()

    def makeSlider(self, min_val, max_val, start, name):
        label = QLabel(f"{name}: {start}")
        label.setStyleSheet("color: white;")
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(min_val, max_val)
        slider.setValue(start)
        slider.valueChanged.connect(lambda val, l=label, n=name: self.updateLabel(l, n, val))
        slider.valueChanged.connect(self.updateImage)
        return {'slider': slider, 'label': label}

    def updateLabel(self, label, name, val):
        label.setText(f"{name}: {val}")

    def resetSliders(self):
        self.hue_slider['slider'].setValue(0)
        self.sat_slider['slider'].setValue(100)
        self.bri_slider['slider'].setValue(100)
        self.selected_emoji = ""
        self.updateImage()

    def updateImage(self):
        if self.original is None:
            return
        img = self.original.copy()
        hue_shift = self.hue_slider['slider'].value()/100.0
        sat_factor = self.sat_slider['slider'].value()/100.0
        bri_factor = self.bri_slider['slider'].value()/100.0
        if abs(hue_shift) > 0.001:
            img = shiftHueNP(img, hue_shift)
        img = ImageEnhance.Color(img).enhance(sat_factor)
        img = ImageEnhance.Brightness(img).enhance(bri_factor)
        if self.selected_emoji:
            img = addEmojiCenter(img, self.selected_emoji, size_ratio=0.2)
        self.current_img = img
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        qimg = QPixmap()
        qimg.loadFromData(buf.getvalue())
        self.image_label.setPixmap(qimg.scaled(
            self.image_label.width(),
            self.image_label.height(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        ))

    def setIcon(self):
        if self.current_img is None: return
        dir = sys.argv[1]
        ini = f"{dir}/desktop.ini"
        icon = f"{dir}/icon.ico"
        if dir:
            if os.path.exists(ini): win32api.SetFileAttributes(ini, 0)
            if os.path.exists(icon): win32api.SetFileAttributes(icon, 0)
            with open(ini, "w", encoding="utf-8") as f:
                s = f"[.ShellClassInfo]\nIconResource=.\\icon.ico,0\nIconFile=.\\icon.ico\nIconIndex=0\nhue={self.hue_slider['slider'].value()}"
                if len(self.selected_emoji) > 0: s += f"\nemoji={ord(self.selected_emoji)}"
                f.write(s)
                subprocess.run(["attrib","+H",ini],check=True, shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
            
            img = self.current_img.copy()
            img = img.resize((256, 256), Image.Resampling.LANCZOS)
            img.save(icon, format="ICO")
            subprocess.run(["attrib","+H",icon],check=True, shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
            ctypes.windll.shell32.SHChangeNotify(0x8000000, 0x1000, None, None)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ColorAdjuster()
    window.show()
    sys.exit(app.exec())
