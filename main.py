from pathlib import Path
import ctypes
import tkinter as tk

from editor import SpeedRacerEditor


def main() -> None:

    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
        "FQ.SpeedRacerResourceEditor"
    )

    root = tk.Tk()

    pasta_projeto = Path(__file__).resolve().parent
    caminho_icone = pasta_projeto / "assets" / "icon.ico"

    root.iconbitmap(
        default=str(caminho_icone)
    )

    SpeedRacerEditor(root)

    root.mainloop()


if __name__ == "__main__":
    main()