import PySimpleGUI as sg

def radnici_window(pozicije, radnici):
    layout = [
        [sg.Text("Upravljanje radnicima", font=("Arial", 14))],

        [sg.Frame("Dodavanje novog radnika", [
            [sg.Text("Ime"), sg.Input(key="IME")],
            [sg.Text("Prezime"), sg.Input(key="PREZIME")],
            [sg.Text("Datum zaposlenja"), sg.Input(key="DATUM"), sg.CalendarButton("KALENDAR", target="DATUM", format="%Y-%m-%d")],
            [sg.Text("Pozicija"), sg.Combo(pozicije, key="POZICIJA", readonly=True)],
            [sg.Button("Dodaj radnika")]
        ])],

        [sg.HorizontalSeparator()],

        [sg.Frame("Postojeći radnici", [
            [sg.Listbox(
                values=[f"{r[0]} - {r[1]}" for r in radnici],
                size=(40, 6),
                key="RADNIK_LISTA"
            )],
            [sg.Button("Obriši radnika")]
        ])],

        [sg.Button("Nazad")]
    ]

    return sg.Window("Radnici", layout)
