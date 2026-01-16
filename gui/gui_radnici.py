import PySimpleGUI as sg
from db.radnici_db import *

def radnici_window(pozicije, radnici_data):
    heading = ["ID", "Ime", "Prezime", "Pozicija", "Datum zaposlenja"]
    table_data = [[r[0], r[1].split()[0], r[1].split()[1], r[2], r[3]] for r in radnici_data]
    
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
            [sg.Table(
                values=table_data,
                headings=heading,
                auto_size_columns=True,
                select_mode='browse',
                num_rows=10,
                key="RADNIK_LISTA",
                alternating_row_color="#7260D7",
                selected_row_colors=('white', '#98D8C8'),
                enable_events=False
            )],
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
                        rad_win["STATUS"].update("Dodan radnik", text_color="white")
                        for key in ["IME", "PREZIME", "DATUM", "POZICIJA"]:
                            rad_win[key].update("")
                        new_data = fetch_radnici()
                        heading = ["ID", "Ime", "Prezime", "Pozicija", "Datum zaposlenja"]
                        table_data = [[r[0], r[1].split()[0], r[1].split()[1], r[2], r[3]] for r in new_data]
                        rad_win["RADNIK_LISTA"].update(values=table_data)
                    else:
                        rad_win["STATUS"].update("Greška pri dodavanju", text_color="orange")
                else:
                    rad_win["STATUS"].update("Popuni sva polja", text_color="orange")
            
            elif event == "Obriši radnika":
                selected = values["RADNIK_LISTA"]
                if selected:
                    radnik_id = new_data[selected[0]][0]
                    if obrisi_radnika(radnik_id):
                        rad_win["STATUS"].update("Radnik deaktiviran", text_color="white")
                        new_data = fetch_radnici()
                        table_data = [[r[0], r[1].split()[0], r[1].split()[1], r[2], r[3]] for r in new_data]
                        rad_win["RADNIK_LISTA"].update(values=table_data)
                    else:
                        rad_win["STATUS"].update("Greška pri brisanju!", text_color="orange")
                else:
                    rad_win["STATUS"].update("Odaberi radnika!", text_color="orange")
