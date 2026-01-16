import gui.gui as gui
import gui.gui_radnici as gui_radnici
import PySimpleGUI as sg

window = gui.main_menu()

def run_radnici_window():
    pozicije = ["Programer", "Voditelj projekta"]
    radnici = [(1, "Ivana Klarić"), (2, "Marko Marić")]

    rad_win = gui_radnici.radnici_window(pozicije, radnici)

    while True:
        event, values = rad_win.read()
        if event in (sg.WIN_CLOSED, "Nazad"):
            break

    rad_win.close()

while True:
    event, values = window.read()
    if event in (sg.WIN_CLOSED, "Izlaz"):
        break

    if event == "Radnici":
        window.close()
        run_radnici_window()
        window = gui.main_menu()  
window.close()
