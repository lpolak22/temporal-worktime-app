import PySimpleGUI as sg

layout = [
    [sg.Text("Evidencija rada")],
    [sg.Button("Izlaz")]
]

window = sg.Window("Evidencija rada", layout)

while True:
    event, values = window.read()
    if event in (sg.WIN_CLOSED, "Izlaz"):
        break

window.close()
