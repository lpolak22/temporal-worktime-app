import PySimpleGUI as sg

def main_menu():
    layout = [
        [sg.Text("Evidencija rada", font=("Arial", 16))],
        [sg.Button("Radnici")],
        [sg.Button("Ugovori i aktivnosti")],
        [sg.Button("Evidencija rada")],
        [sg.Button("Satnice radnika")],
        [sg.Button("Obračun i isplate")],
        [sg.Button("Izlaz")]
    ]
    return sg.Window("Glavni izbornik", layout)
