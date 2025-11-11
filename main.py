from PyQt6.QtWidgets import QApplication, QLabel, QMainWindow, QVBoxLayout, QWidget, QSlider, QPushButton, QHBoxLayout, QGridLayout, QScrollArea
from PyQt6.QtCore import Qt, QBuffer, QIODevice, QRect, QPoint
from PyQt6.QtGui import QPixmap, QPainter, QFont, QColor
from PIL import Image, ImageEnhance
import colorsys, io, os, ctypes, sys, subprocess, win32api

def shiftHue(image, shift):
    image = image.convert('RGBA')
    width, height = image.size
    pixels = list(image.getdata())
    
    new_pixels = []
    for r, g, b, a in pixels:
        r_f, g_f, b_f = r / 255.0, g / 255.0, b / 255.0
        h, s, v = colorsys.rgb_to_hsv(r_f, g_f, b_f)
        h = (h + shift) % 1.0
        r_new, g_new, b_new = colorsys.hsv_to_rgb(h, s, v)
        new_pixels.append((
            int(r_new * 255),
            int(g_new * 255),
            int(b_new * 255),
            a
        ))

    new_image = Image.new('RGBA', (width, height))
    new_image.putdata(new_pixels)
    return new_image

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
        self.dir_path = sys.argv[1]
        self.ini_path = f"{self.dir_path}/desktop.ini"
        self.icon_path = f"{self.dir_path}/icon.ico"
        self.setWindowTitle("Custom folder")
        self.resize(400, 200)
        
        
        
    def resetIcon(self):
        if self.dir_path:
            self.resetSliders()
            if os.path.exists(self.ini_path): 
                win32api.SetFileAttributes(self.ini_path, 0)
                os.remove(self.ini_path)
            if os.path.exists(self.icon_path): 
                win32api.SetFileAttributes(self.icon_path, 0)
                os.remove(self.icon_path)
            ctypes.windll.shell32.SHChangeNotify(0x8000000, 0x1000, None, None)
        
    def closeEvent(self, event):
        if os.path.exists(self.ini_path): subprocess.run(["attrib","+H",self.ini_path],check=True, shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
        if os.path.exists(self.icon_path): subprocess.run(["attrib","+H",self.icon_path],check=True, shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
        
    def loadData(self):
        if os.path.exists(self.ini_path): 
            win32api.SetFileAttributes(self.ini_path, 0)
            with open(self.ini_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith(";") or line.startswith("#") or line.startswith("["):
                        continue
                    if "=" in line:
                        k, v = line.split("=", 1)
                        if k.strip().lower() == "hue":
                            self.hue_slider["slider"].setValue(int(v.strip()))
                        if k.strip().lower() == "sat":
                            self.sat_slider["slider"].setValue(int(v.strip()))
                        if k.strip().lower() == "bri":
                            self.bri_slider["slider"].setValue(int(v.strip()))
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
            img = shiftHue(img, hue_shift)
        img = ImageEnhance.Color(img).enhance(sat_factor)
        img = ImageEnhance.Brightness(img).enhance(bri_factor)
        if self.selected_emoji:
            img = addEmojiCenter(img, self.selected_emoji, size_ratio=0.3)
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
        if self.dir_path:
            if os.path.exists(self.ini_path): win32api.SetFileAttributes(self.ini_path, 0)
            if os.path.exists(self.icon_path): win32api.SetFileAttributes(self.icon_path, 0)
            with open(self.ini_path, "w", encoding="utf-8") as f:
                
                if len(self.selected_emoji) > 0: s += f"\nemoji={ord(self.selected_emoji)}"
                f.write(s)
                subprocess.run(["attrib","+H",self.ini_path],check=True, shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
            
            img = self.current_img.copy()
            img = img.resize((256, 256), Image.Resampling.LANCZOS)
            img.save(self.icon_path, format="ICO")
            subprocess.run(["attrib","+H",self.icon_path],check=True, shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
            ctypes.windll.shell32.SHChangeNotify(0x8000000, 0x1000, None, None)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ColorAdjuster()
    window.show()
    sys.exit(app.exec())
