import gui.gui as gui
import gui.gui_radnici as gui_radnici
import gui.gui_ugovori_aktivnost as gui_ua
import gui.gui_evidencija_rada as gui_er
import PySimpleGUI as sg

window = gui.main_menu()

while True:
    event, values = window.read()
    if event in (sg.WIN_CLOSED, "Izlaz"):
        break

    if event == "Radnici":
        window.close()
        gui_radnici.run_radnici_window()
        window = gui.main_menu()
    
    elif event == "Ugovori i aktivnosti":
        window.close()
        gui_ua.run_ugovori_aktivnosti_window()
        window = gui.main_menu()
    elif event == "Evidencija rada":
        window.close()
        gui_er.run_evidencija_rada_window()
        window = gui.main_menu()

window.close()
