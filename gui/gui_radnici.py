import PySimpleGUI as sg
from db.radnici_db import *

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
            [sg.Listbox(values=[f"{r[0]} - {r[1]}" for r in radnici], size=(40, 6), key="RADNIK_LISTA")],
            [sg.Button("Obriši radnika")]
        ])],
        [sg.Button("Nazad")],
        [sg.Text("", key="STATUS", size=(50,1), font=("Arial", 10), text_color="green")]
    ]
    return sg.Window("Radnici", layout, finalize=True)

def run_radnici_window():
    while True:
        pozicije = fetch_pozicije()
        radnici_data = fetch_radnici()
        if not radnici_data:
            radnici_data = []
            
        rad_win = radnici_window(pozicije, radnici_data)

        while True:
            event, values = rad_win.read()
            if event in (sg.WIN_CLOSED, "Nazad"):
                rad_win.close()
                return
            
            if event == "Dodaj radnika":
                ime, prezime, datum, poz = values["IME"], values["PREZIME"], values["DATUM"], values["POZICIJA"]
                if ime and prezime and datum and poz:
                    if dodaj_radnika(ime, prezime, datum, poz):
                        rad_win["STATUS"].update(f"Dodan radnik", text_color="white")
                        for key in ["IME", "PREZIME", "DATUM", "POZICIJA"]:
                            rad_win[key].update("")
                        new_radnici = fetch_radnici()
                        rad_win["RADNIK_LISTA"].update([f"{r[0]} - {r[1]}" for r in new_radnici])
                    else:
                        rad_win["STATUS"].update("Greška pri dodavanju!", text_color="red")
                else:
                    rad_win["STATUS"].update("Popuni sva polja!", text_color="red")
            
            elif event == "Obriši radnika":
                selected = values["RADNIK_LISTA"]
                if selected:
                    radnik_id = int(selected[0].split(" - ")[0])
                    if obrisi_radnika(radnik_id):
                        rad_win["STATUS"].update(f"Deaktiviran radnik", text_color="white")
                        new_radnici = fetch_radnici()
                        rad_win["RADNIK_LISTA"].update([f"{r[0]} - {r[1]}" for r in new_radnici])
                    else:
                        rad_win["STATUS"].update("Greška pri brisanju!", text_color="red")
                else:
                    rad_win["STATUS"].update("Odaberi radnika!", text_color="red")
