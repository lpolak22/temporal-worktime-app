import gui.gui as gui
import gui.gui_radnici as gui_radnici
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
        
window.close()
