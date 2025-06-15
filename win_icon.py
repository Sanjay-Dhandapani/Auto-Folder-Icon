from PIL import Image
import os
import subprocess
import logging

class WinIconSetter:
    def set_folder_icon(self, folder_path, image_name):
        """
        Converts the given image to .ico, writes desktop.ini, and sets attributes for Windows folder icon.
        Args:
            folder_path (str): Path to the folder
            image_name (str): Name of the image file (e.g., poster.jpg)
        """
        folder_path = os.path.abspath(folder_path)
        image_path = os.path.join(folder_path, image_name)
        icon_path = os.path.join(folder_path, 'folder.ico')
        desktop_ini_path = os.path.join(folder_path, 'desktop.ini')

        # Convert image to .ico with poster aspect ratio
        self._convert_to_ico(image_path, icon_path)

        # Remove attributes from desktop.ini if it exists
        self._remove_ini_attributes(desktop_ini_path)

        # Write desktop.ini
        self._write_desktop_ini(desktop_ini_path)

        # Set attributes
        self._set_attributes(folder_path, desktop_ini_path)

    def _convert_to_ico(self, image_path, icon_path):
        try:
            # Target icon sizes (square, but poster centered)
            sizes = [(256,256), (128,128), (64,64), (48,48), (32,32), (16,16)]
            poster_ratio = 2/3  # e.g., 128x192
            icons = []
            img = Image.open(image_path).convert('RGBA')
            for size in sizes:
                canvas = Image.new('RGBA', size, (0,0,0,0))
                w, h = size
                # Calculate poster size for this icon size
                poster_h = int(h * 0.9)  # 90% of icon height
                poster_w = int(poster_h * poster_ratio)
                if poster_w > w * 0.9:
                    poster_w = int(w * 0.9)
                    poster_h = int(poster_w / poster_ratio)
                poster = img.resize((poster_w, poster_h), Image.LANCZOS)
                offset = ((w - poster_w)//2, (h - poster_h)//2)
                canvas.paste(poster, offset, poster)
                icons.append(canvas)
            icons[0].save(icon_path, format='ICO', sizes=sizes)
        except Exception as e:
            logging.error(f"Error converting image to .ico: {e}")

    def _remove_ini_attributes(self, desktop_ini_path):
        if os.path.exists(desktop_ini_path):
            try:
                subprocess.run(["attrib", "-s", "-h", "-r", "-a", desktop_ini_path], shell=True)
            except Exception as e:
                logging.error(f"Error removing attributes from desktop.ini: {e}")

    def _write_desktop_ini(self, desktop_ini_path):
        content = (
            "[.ShellClassInfo]\n"
            "IconResource=.\\folder.ico,0\n"
            "[ViewState]\n"
            "Mode=\n"
            "Vid=\n"
            "FolderType=Pictures\n"
        )
        with open(desktop_ini_path, 'w', encoding='utf-8') as f:
            f.write(content)

    def _set_attributes(self, folder_path, desktop_ini_path):
        try:
            # Set desktop.ini as system+hidden+archive
            subprocess.run(["attrib", "+s", "+h", "+a", desktop_ini_path], shell=True)
            # Set folder as system+readonly
            subprocess.run(["attrib", "+s", "+r", folder_path], shell=True)
        except Exception as e:
            logging.error(f"Error setting attributes: {e}")
