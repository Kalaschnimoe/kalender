from datetime import date, timedelta, datetime
from threading import Thread

import numpy as np
from easysettings import EasySettings
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.properties import ObjectProperty, StringProperty
from kivy.uix.colorpicker import ColorPicker
from kivy.uix.label import Label
from kivy.uix.screenmanager import ScreenManager, SlideTransition, NoTransition, SwapTransition
from kivy.utils import platform
from kivymd.app import MDApp
from kivymd.toast import toast
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.dialog import MDDialog
from kivymd.uix.expansionpanel import MDExpansionPanel, MDExpansionPanelTwoLine
from kivymd.uix.label import MDLabel
from kivymd.uix.list import IRightBodyTouch, TwoLineRightIconListItem, TwoLineIconListItem, OneLineIconListItem
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.screen import MDScreen
from plyer import uniqueid

import berechnung_feiertage as bf
from clsDatabase import Database
from customExceptions import NoStartzeit, NoEndzeit, NoDienstbezeichnung, NoInternetConnection
from picker import MDDatePicker, MDTimePicker


class RightContentCls(IRightBodyTouch, MDBoxLayout):
    icon = StringProperty()
    text = StringProperty()


class UniqueIDInterface(MDBoxLayout):
    uniqueid = ObjectProperty()
    uid = StringProperty()
    text = "Serial Number"

    def get_uid(self):
        self.uid = self.uniqueid.id or self.uid


class MonthYearLabel(MDLabel):
    myroot = ObjectProperty()

    def __init__(self, *args, **kwargs):
        self.date = date.today()
        self.actdate = self.date

        super(MonthYearLabel, self).__init__(**kwargs)
        self.month_names = ('Jänner',
                            'Februar',
                            'März',
                            'April',
                            'Mai',
                            'Juni',
                            'Juli',
                            'August',
                            'September',
                            'Oktober',
                            'November',
                            'Dezember')
        if kwargs.__contains__("month_names"):
            self.month_names = kwargs['month_names']

        self.month_year_text = self.month_names[self.date.month - 1] + ' ' + str(self.date.year)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            year = self.actdate.year
            month = self.actdate.month
            day = self.actdate.day
            datePicker = MDDatePicker(year=year, month=month, day=day)
            datePicker.bind(on_save=self.selected_date)
            datePicker.open()

    def selected_date(self, instance, datum, range):
        self.actdate = datum
        self.month_year_text = self.month_names[self.actdate.month - 1] + ' ' + str(self.actdate.year)
        self.text = self.month_year_text
        self.myroot.populate_calendar()


class Kalendercard(MDCard):
    selected = False

    def __init__(self, **kwargs):
        super(Kalendercard, self).__init__(**kwargs)

    def clicked(self):
        # falls schon ausgewählt wurde (quasi ein doppelklick), dann auf tagesansichtsscreen wechseln

        if self.selected:
            MDApp.get_running_app().root.ids.dienstescreen.late_init()
            self.selected = False
            MDApp.get_running_app().root.changescreen(screen="dienstescreen")
        else:
            # alle kalenderkarten zurücksetzen
            for child in MDApp.get_running_app().root.ids.kalenderscreen.ids.cal.children:
                if type(child) == Kalendercard:
                    child.md_bg_color = (1, 1, 1, 1)
                    child.selected = False

            # selected auf True setzen, damit evtl. ein Doppelklick ausgelöst werden kann
            self.selected = True

            # Karte einfärben
            self.md_bg_color = (0, 0, 0, .2)

            # selektierten Tag abspeichern, um bei einem neuen Eintrag gleich darauf zugreifen zu können
            MDApp.get_running_app().root.ids.kalenderscreen.selday = self.ids.day.text


class DiensteTwoLineIconListItem(TwoLineIconListItem):
    def deletedienst(self):
        try:
            loeschendb = Database()
            if not loeschendb.connectToDatabase():
                loeschendb.closeDatabaseConnection()
                raise NoInternetConnection
            else:
                # in der Datenbank löschen
                loeschendb.deleteDienst(dienst_id=self.dienstid)
                loeschendb.closeDatabaseConnection()

                # Datenbank neu laden
                MDApp.get_running_app().root.get_dienste_from_server()
                MDApp.get_running_app().root.save_dienste_into_txt()
                MDApp.get_running_app().root.get_dienste_from_txt()

                # Eintrag aus Liste entfernen
                MDApp.get_running_app().root.ids.dienstescreen.ids.vorlagencontainer.remove_widget(self)

                # Kalender aktualisieren
                MDApp.get_running_app().root.ids.kalenderscreen.populate_calendar()

                # timestamp file öffnen und zeit vom timestamp reinschreiben
                try:
                    servertimestamp = MDApp.get_running_app().root.get_servertimestamp()
                except:
                    servertimestamp = datetime.today()

                servertimestamp = servertimestamp.strftime("%Y, %m, %d, %H, %M, %S")
                timestampfile = open("timestamp.txt", "w")
                timestampfile.write(servertimestamp)
                timestampfile.close()

                toast("Dienst erfolgreich gelöscht")

        except NoInternetConnection:
            toast("Keine Verbindung zum Server. Bitte überprüfe deine Internetverbindung!")


class DiensteScreen(MDScreen):
    def late_init(self):
        # Liste leeren, damit die Einträge nicht mehrmals angezeigt werden
        self.ids.vorlagencontainer.clear_widgets()

        # Jahr:
        year = MDApp.get_running_app().root.ids.kalenderscreen.ids.current_month.actdate.year
        # Monat:
        month = MDApp.get_running_app().root.ids.kalenderscreen.ids.current_month.actdate.month
        # Tag:
        day = int(MDApp.get_running_app().root.ids.kalenderscreen.selday)

        # Feiertage:
        feiertage = MDApp.get_running_app().root.feiertage
        feiertagsname = ""
        for feiertag in feiertage:
            if feiertag[0] == date(year, month, day):
                feiertagsname = feiertag[1]

        # Datum in Toolbar schreiben
        datumwaehlentext = f"{str(day).zfill(2)}.{str(month).zfill(2)}.{str(year)}"
        if feiertagsname != "":
            self.ids.titel.title = "Dienste an " + feiertagsname
        else:
            self.ids.titel.title = "Dienste am " + datumwaehlentext

        # Dienste vom Kalender holen
        dienste = MDApp.get_running_app().root.ids.kalenderscreen.dienstenachmonatgefiltert

        tag = np.array(MDApp.get_running_app().root.ids.kalenderscreen.selday)
        diensteamheutigentag = dienste[np.in1d(dienste[:, 5], tag)]

        # Liste befüllen
        if len(diensteamheutigentag) != 0:
            for dienst in diensteamheutigentag:
                if dienst[2][1:-1] == MDApp.get_running_app().root.username:
                    dienstelistitem = DiensteTwoLineIconListItem(text=f"{dienst[2][1:-1]}: {dienst[10][1:-2]}",
                                                                 secondary_text=f"{str(dienst[6]).zfill(2)}:{str(dienst[7]).zfill(2)} - {str(dienst[8]).zfill(2)}:{str(dienst[9]).zfill(2)}",
                                                                 )
                    dienstelistitem.dienstid = dienst[0]
                else:
                    dienstelistitem = TwoLineIconListItem(text=f"{dienst[2][1:-1]}: {dienst[10][1:-2]}",
                                                          secondary_text=f"{str(dienst[6]).zfill(2)}:{str(dienst[7]).zfill(2)} - {str(dienst[8]).zfill(2)}:{str(dienst[9]).zfill(2)}",
                                                          )
                    dienstelistitem._no_ripple_effect = True
                self.ids.vorlagencontainer.add_widget(dienstelistitem)

        else:
            # falls keine Vorlagen vorhanden sind, muss das angezeigt werden
            keineDienste = MDLabel(text="Keine Dienste vorhanden", halign="center")
            self.ids.vorlagencontainer.add_widget(keineDienste)


class Kalenderansicht(MDBoxLayout):
    pass


class Dienstlabel(Label):
    pass


class KalenderScreen(MDScreen):
    selday = str(date.today().day)

    def __init__(self, **kwargs):
        super(KalenderScreen, self).__init__(**kwargs)
        # MDApp.get_running_app().root.ids["kalenderscreen"] = self
        Clock.schedule_once(self.populate_calendar, .3)
        Clock.schedule_once(self.set_title, .5)

    def set_title(self, dt=0):
        self.ids.toptoolbar.ids.label_title.halign = "center"
        self.ids.toptoolbar.ids.label_title.text = f"{MDApp.get_running_app().root.username}s Kalender"

    def move_previous_month(self):
        if self.ids.current_month.actdate.month == 1:
            self.ids.current_month.actdate = date(self.ids.current_month.actdate.year - 1,
                                                  12,
                                                  self.ids.current_month.actdate.day)
            MDApp.get_running_app().root.get_feiertage(jahr=self.ids.current_month.actdate.year)

        else:
            try:
                self.ids.current_month.actdate = date(self.ids.current_month.actdate.year,
                                                      self.ids.current_month.actdate.month - 1,
                                                      self.ids.current_month.actdate.day)
            except ValueError:
                self.ids.current_month.actdate = date(month=self.ids.current_month.actdate.month - 1,
                                                      day=1,
                                                      year=self.ids.current_month.actdate.year)

        self.ids.current_month.text = self.ids.current_month.month_names[
                                          self.ids.current_month.actdate.month - 1] + ' ' + str(
            self.ids.current_month.actdate.year)
        self.populate_calendar()

    def move_next_month(self):
        if self.ids.current_month.actdate.month == 12:
            self.ids.current_month.actdate = date(self.ids.current_month.actdate.year + 1,
                                                  1,
                                                  self.ids.current_month.actdate.day)
            MDApp.get_running_app().root.get_feiertage(jahr=self.ids.current_month.actdate.year)
        else:
            try:
                self.ids.current_month.actdate = date(month=self.ids.current_month.actdate.month + 1,
                                                      day=self.ids.current_month.actdate.day,
                                                      year=self.ids.current_month.actdate.year)
            except ValueError:
                self.ids.current_month.actdate = date(month=self.ids.current_month.actdate.month + 1,
                                                      day=1,
                                                      year=self.ids.current_month.actdate.year)

        self.ids.current_month.text = self.ids.current_month.month_names[
                                          self.ids.current_month.actdate.month - 1] + ' ' + str(
            self.ids.current_month.actdate.year)
        self.populate_calendar()

    def populate_calendar(self, dt=0):
        self.ids.cal.clear_widgets()

        date_cursor = date(self.ids.current_month.actdate.year, self.ids.current_month.actdate.month, 1)
        for filler in range(date_cursor.isoweekday() - 1):
            self.ids.cal.add_widget(MDLabel())

        month = self.ids.current_month.actdate.month
        today = date.today()

        feiertagsliste = MDApp.get_running_app().root.feiertage
        feiertageimmonat = {}
        for feiertag in feiertagsliste:
            if feiertag[0].month == month:
                feiertageimmonat[feiertag[0].day] = feiertag[1]
        while date_cursor.month == month:
            newCard = Kalendercard()
            newCard.ids.day.text = str(date_cursor.day)
            if date_cursor.day in feiertageimmonat.keys():
                newCard.ids.day.md_bg_color = [1, 0, 0, .5]
            if date_cursor == today:
                newCard.md_bg_color = [0, 1, 0, 0.15]
            self.ids.cal.add_widget(newCard)
            date_cursor += timedelta(days=1)

        try:
            self.populate_calendar_with_dienste(1)
        except:
            pass

    def add_new_entry(self):
        datumwaehlentext = f"{str(self.selday).zfill(2)}.{str(self.ids.current_month.actdate.month).zfill(2)}.{str(self.ids.current_month.actdate.year)}"
        MDApp.get_running_app().root.ids.neuerEintrag.ids.datumwaehlen.text = datumwaehlentext
        MDApp.get_running_app().root.ids.neuerEintrag.selected_days_list.clear()
        day = self.selday
        month = self.ids.current_month.actdate.month
        year = self.ids.current_month.actdate.year
        datum = f"{day}.{str(month)}.{str(year)}"
        datum = datetime.strptime(datum, "%d.%m.%Y")
        datum = datetime.date(datum)
        MDApp.get_running_app().root.ids.neuerEintrag.selected_days_list.append(datum)
        print(MDApp.get_running_app().root.ids.neuerEintrag.selected_days_list)
        # MDApp.get_running_app().root.ids.neuerEintrag.datum = datetime.strptime(datumwaehlentext, "%d.%m.%Y")
        MDApp.get_running_app().root.changescreen("neuerEintrag")

    def changescreen(self, screen):
        self.ids.nav_drawer.set_state("close")
        MDApp.get_running_app().root.ids.neuerUser.ids.username.text = ""
        if screen == "vorlagenuebersicht":
            MDApp.get_running_app().root.ids.vorlagenuebersicht.late_init()
        MDApp.get_running_app().root.changescreen(screen=screen, direction="right")

    def populate_calendar_with_dienste(self, dt=0):
        # Jahr und Monat auslesen
        jahr = str(self.ids.current_month.actdate.year)
        monat = str(self.ids.current_month.actdate.month)
        # relevante Dienste in Liste abspeichern:
        dienste = MDApp.get_running_app().root.dienste
        arr = np.array(dienste)
        jahresfilter = np.array(jahr)
        monatsfilter = np.array(monat)
        dienstenachjahrgefiltert = arr[np.in1d(arr[:, 3], jahresfilter)]
        self.dienstenachmonatgefiltert = dienstenachjahrgefiltert[np.in1d(dienstenachjahrgefiltert[:, 4], monatsfilter)]

        userdict = MDApp.get_running_app().root.settingsdict
        # Labels auf der Kalendercard einfügen
        for child in self.ids.cal.children:
            if type(child) == Kalendercard:
                tag = np.array(child.ids.day.text)
                diensteamheutigentag = self.dienstenachmonatgefiltert[
                    np.in1d(self.dienstenachmonatgefiltert[:, 5], tag)]
                if len(diensteamheutigentag) != 0:
                    for entry in diensteamheutigentag:
                        newlabel = Dienstlabel()
                        newlabel.text = entry[2][1:-1]
                        newlabel.font_size = MDApp.get_running_app().root.settingsdict["schriftgroesse"]
                        try:
                            newlabel.color = userdict[newlabel.text]
                        except:
                            pass
                        child.ids.dienste.add_widget(newlabel)
                else:
                    child.add_widget(MDLabel())


class NeuerEintragScreen(MDScreen):
    def __init__(self, **kwargs):
        super(NeuerEintragScreen, self).__init__(**kwargs)
        self.selected_days_list = []
        Clock.schedule_once(self.late_init, .5)

    def late_init(self, dt=0):
        self.vorlagen = MDApp.get_running_app().root.vorlagen
        if self.vorlagen == "":
            self.ids.vorlagewaehlen.text = "Keine Vorlagen vorhanden"
        else:
            self.create_vorlagendropdown()

        self.startzeit = MDTimePicker()
        self.startzeit.military = True
        self.startzeit.bind(time=self.selectedStartzeit)

        self.endzeit = MDTimePicker()
        self.endzeit.military = True
        self.endzeit.bind(time=self.selectedEndzeit)

    def drop(self):
        if MDApp.get_running_app().root.vorlagen != "":
            self.menu.open()
        else:
            pass

    def menu_callback(self, text_item):
        self.menu.dismiss()
        self.ids.vorlagewaehlen.text = str(text_item[7])
        startzeit = f"{str(text_item[3]).zfill(2)}:{str(text_item[4]).zfill(2)}"
        endzeit = f"{str(text_item[5]).zfill(2)}:{str(text_item[6]).zfill(2)}"
        self.ids.startzeit.text = startzeit
        self.ids.endzeit.text = endzeit
        self.ids.dienstname.text = str(text_item[7])
        self.ids.dienstname.hint_text = ""

    def datepicker(self):
        self.datum = datetime.strptime(str(self.selected_days_list[-1]), "%Y-%m-%d")

        # try:
        #     self.datum = datetime.strptime(str(self.selected_days_list[-1]), "%d.%m.%Y")
        # except ValueError:
        #     self.datum = datetime.strptime(str(self.selected_days_list[-1]), "%Y-%m-%d")

        dp = MDDatePicker(day=self.datum.day, month=self.datum.month, year=self.datum.year)
        dp.bind(on_save=self.selDate)
        dp.selected_days_list = [(self.datum.day, self.datum.month, self.datum.year)]
        dp.open()

    def selDate(self, instance, datum, range):
        text_fuers_feld = ""
        self.selected_days_list = []
        for selected_date in instance.selected_days_list:
            # Datum als Tuple: (d, m, y)
            # print(selected_date)
            # print(type(selected_date))

            # in date object umwandeln
            dateobject = date(day=selected_date[0], month=selected_date[1], year=selected_date[2])
            self.selected_days_list.append(dateobject)

            # Text aufbereiten
            text = f"{selected_date[0]}.{selected_date[1]}.{selected_date[2]}, "
            text_fuers_feld = text_fuers_feld + text

        text_fuers_feld = text_fuers_feld[:-2]

        if text_fuers_feld == "":
            text_fuers_feld = f"{datum.day}.{datum.month}.{datum.year}"
            self.selected_days_list.append(datum)

        self.ids.datumwaehlen.text = text_fuers_feld

    def timepicker_startzeit(self):
        if self.ids.startzeit.text == "Startzeit":
            self.startzeit.set_time(datetime.strptime("07:00", '%H:%M').time())
        else:
            self.startzeit.set_time(datetime.strptime(self.ids.startzeit.text, '%H:%M'))
        self.startzeit.open()

    def selectedStartzeit(self, instance, time):
        startzeittext = time.strftime('%H:%M')
        self.ids.startzeit.text = str(startzeittext)

    def timepicker_endzeit(self):
        if self.ids.endzeit.text == "Endzeit":
            self.endzeit.set_time(datetime.strptime("17:00", '%H:%M').time())
        else:
            self.endzeit.set_time(datetime.strptime(self.ids.endzeit.text, '%H:%M'))
        self.endzeit.open()

    def selectedEndzeit(self, instance, time):
        endzeittext = time.strftime('%H:%M')
        self.ids.endzeit.text = str(endzeittext)

    def upload_dienst(self):
        while True:
            try:
                # Felder auslesen und abspeichern
                try:
                    startzeit = datetime.strptime(self.ids.startzeit.text, "%H:%M")
                except ValueError:
                    raise NoStartzeit
                try:
                    endzeit = datetime.strptime(self.ids.endzeit.text, "%H:%M")
                except ValueError:
                    raise NoEndzeit
                dienstbezeichnung = str(self.ids.dienstname.text)
                if dienstbezeichnung == "":
                    raise NoDienstbezeichnung

                user_id = MDApp.get_running_app().root.user_id
                username = MDApp.get_running_app().root.username

                # db öffnen
                # daten hochladen
                # db schließen
                self.db = Database()

                if not self.db.connectToDatabase():
                    self.db.closeDatabaseConnection()
                    raise NoInternetConnection
                else:
                    for datum in self.selected_days_list:
                        self.db.uploadDienst(benutzer_id=user_id, benutzername=username, jahr=datum.year,
                                             monat=datum.month, tag=datum.day,
                                             startzeitstunde=str(startzeit.hour),
                                             startzeitminute=str(startzeit.minute), endzeitstunde=str(endzeit.hour),
                                             endzeitminute=str(endzeit.minute),
                                             dienstbezeichnung=str(dienstbezeichnung))

                    self.db.closeDatabaseConnection()
                    if len(self.selected_days_list) == 1:
                        toast(f"{dienstbezeichnung} am {date.strftime(datum, '%d.%m.%Y')} erfolgreich hochgeladen")
                    else:
                        toast("Dienste erfolgreich hochgeladen")

                    # Dienste vom Server holen
                    MDApp.get_running_app().root.get_dienste_from_server()

                    # Dienste in txt abspeichern
                    MDApp.get_running_app().root.save_dienste_into_txt()

                    # Dienste von txt wieder einlesen. Dadurch wird jeder Dienst richtig aufbereitet
                    MDApp.get_running_app().root.get_dienste_from_txt()

                    # Kalender neu zeichnen, damit der neue Dienst angezeigt wird
                    MDApp.get_running_app().root.ids.kalenderscreen.populate_calendar()

                    # timestamp file öffnen und zeit vom timestamp reinschreiben
                    try:
                        servertimestamp = MDApp.get_running_app().root.get_servertimestamp()
                    except:
                        servertimestamp = datetime.today()

                    servertimestamp = servertimestamp.strftime("%Y, %m, %d, %H, %M, %S")
                    timestampfile = open("timestamp.txt", "w")
                    timestampfile.write(servertimestamp)
                    timestampfile.close()

                    self.text_zuruecksetzen()
                    MDApp.get_running_app().root.changescreen(screen="kalender", direction="right",
                                                              transition="SwapTransition")
                break

            except NoStartzeit:
                toast("gib eine gültige Startzeit ein")
                break
            except NoEndzeit:
                toast("gib eine gültige Endzeit ein")
                break
            except NoDienstbezeichnung:
                toast("gib eine Dienstbezeichnung ein")
                break
            except NoInternetConnection:
                toast("Keine Verbindung zum Server. Bitte versuche es erneut")
                break

    def text_zuruecksetzen(self):
        self.ids.datumwaehlen.text = "Tag auswählen"
        self.ids.vorlagewaehlen.text = "Vorlage wählen"
        self.ids.startzeit.text = "Startzeit"
        self.ids.endzeit.text = "Endzeit"
        self.ids.dienstname.text = ""
        self.ids.dienstname.hint_text = "Dienstbezeichnung"
        self.selected_days_list = []

    def create_vorlagendropdown(self):
        menu_items = [
            {
                "text": f"{vorlage[7]}",
                "secondary_text": f"{str(vorlage[3]).zfill(2)}:{str(vorlage[4]).zfill(2)} - {str(vorlage[5]).zfill(2)}:{str(vorlage[6]).zfill(2)}",
                "viewclass": "TwoLineListItem",
                "height": dp(60),
                "pos_hint": {'center_y': .5},
                "on_release": lambda x=vorlage: self.menu_callback(x)
            }
            for vorlage in self.vorlagen
        ]
        self.menu = MDDropdownMenu(
            caller=self.ids.vorlagewaehlen,
            items=menu_items,
            width_mult=3,
            position="bottom"
        )

    def upload_vorlage(self):
        while True:
            try:
                # Felder auslesen und abspeichern
                try:
                    startzeit = datetime.strptime(self.ids.startzeit.text, "%H:%M")
                except ValueError:
                    raise NoStartzeit
                try:
                    endzeit = datetime.strptime(self.ids.endzeit.text, "%H:%M")
                except ValueError:
                    raise NoEndzeit
                dienstbezeichnung = str(self.ids.dienstname.text)
                if dienstbezeichnung == "":
                    raise NoDienstbezeichnung

                user_id = MDApp.get_running_app().root.user_id
                username = MDApp.get_running_app().root.username

                # db öffnen
                # daten hochladen
                # db schließen
                # dropdown neu laden
                self.db = Database()

                if not self.db.connectToDatabase():
                    self.db.closeDatabaseConnection()
                    raise NoInternetConnection
                else:
                    self.db.upload_vorlage(benutzer_id=user_id, benutzername=username,
                                           startzeitstunde=str(startzeit.hour),
                                           startzeitminute=str(startzeit.minute), endzeitstunde=str(endzeit.hour),
                                           endzeitminute=str(endzeit.minute), dienstbezeichnung=str(dienstbezeichnung))

                    self.db.closeDatabaseConnection()

                    # Vorlagen laden
                    vorlagendb = Database()
                    vorlagendb.connectToDatabase()
                    self.vorlagen = vorlagendb.requestAllRowsInTable(table="Vorlagen", param1="Benutzer_ID",
                                                                     value1=user_id, sort=True)
                    vorlagendb.closeDatabaseConnection()
                    self.vorlagen = list(self.vorlagen)
                    MDApp.get_running_app().root.vorlagen = self.vorlagen
                    self.create_vorlagendropdown()

                    toast(f"{dienstbezeichnung} erfolgreich hochgeladen")
                break

            except NoStartzeit:
                toast("gib eine gültige Startzeit ein")
                break
            except NoEndzeit:
                toast("gib eine gültige Endzeit ein")
                break
            except NoDienstbezeichnung:
                toast("gib eine Dienstbezeichnung ein")
                break
            except NoInternetConnection:
                toast("Keine Verbindung zum Server. Bitte versuche es erneut")
                break


class Colorpickercard(MDCard):
    def hide_widget(self, dohide=True):
        if hasattr(self, 'saved_attrs'):
            if not dohide:
                self.height, self.size_hint_y, self.opacity, self.disabled = self.saved_attrs
                del self.saved_attrs
        elif dohide:
            # Farben ändern
            self.listitem.ids.icon.text_color = self.ids.custom_color_picker.color
            self.listitem.text_color = self.ids.custom_color_picker.color

            # Farbe in configfile speichern
            MDApp.get_running_app().root.settings.setsave(self.listitem.text, list(self.ids.custom_color_picker.color))

            # Farbe in settingsdict updaten
            MDApp.get_running_app().root.settingsdict[self.listitem.text] = list(self.ids.custom_color_picker.color)

            # Karte verstecken
            self.saved_attrs = self.height, self.size_hint_y, self.opacity, self.disabled
            self.height, self.size_hint_y, self.opacity, self.disabled = 0, None, 0, True

            # Kalender neu zeichnen
            MDApp.get_running_app().root.ids.kalenderscreen.populate_calendar()


class CustomColorPicker(ColorPicker):
    def on_color(self, instance, value):
        self.color = value


class Usercolorslistitem(OneLineIconListItem):
    def openColorpicker(self):
        self.card = Colorpickercard()
        self.card.listitem = self
        MDApp.get_running_app().root.ids.kalenderscreen.ids.nav_drawer.set_state("close")
        MDApp.get_running_app().root.ids.kalenderscreen.add_widget(self.card)


class ContentNavigationDrawer(MDBoxLayout):
    def __init__(self, **kwargs):
        super(ContentNavigationDrawer, self).__init__(**kwargs)
        Clock.schedule_once(self.createcolorpickerlist, 1)

    def createcolorpickerlist(self, dt=0):
        # Schriftgröße setzen
        MDApp.get_running_app().root.ids.kalenderscreen.ids.schriftgroesse.text = \
            MDApp.get_running_app().root.settingsdict["schriftgroesse"]

        # Liste mit usern erstellen
        anzahluserdb = Database()

        if not anzahluserdb.connectToDatabase():
            anzahluserdb.closeDatabaseConnection()
            listitem = Usercolorslistitem()
            listitem.text = "Mario"
            listitem.id = str(1)
            # in configfile schauen, ob es bereits eine gespeicherte Farbe für den Namen gibt
            settingsdict = MDApp.get_running_app().root.settingsdict
            if listitem.text in settingsdict.keys():
                listitem.customcolor = settingsdict[listitem.text]
            else:
                listitem.customcolor = (0, 0, 0, 1)
            listitem.ids.icon.text_color = listitem.customcolor
            listitem.text_color = listitem.customcolor
            MDApp.get_running_app().root.ids.kalenderscreen.ids.colorpickerlist.add_widget(listitem)

        else:
            anzahluser = anzahluserdb.requestAllRowsInTable(table="Login")
            anzahluserdb.closeDatabaseConnection()

            # configfile lesen
            settingsdict = MDApp.get_running_app().root.settingsdict

            for user in anzahluser:
                # listitem erstellen
                listitem = Usercolorslistitem()
                listitem.text = str(user[1])
                listitem.id = user[0]

                # in configfile schauen, ob es bereits eine gespeicherte Farbe für den Namen gibt
                if listitem.text in settingsdict.keys():
                    listitem.customcolor = settingsdict[listitem.text]
                else:
                    listitem.customcolor = (0, 0, 0, 1)

                # Farben setzen
                listitem.ids.icon.text_color = listitem.customcolor
                listitem.text_color = listitem.customcolor

                # listitem zur Liste hinzufügen
                MDApp.get_running_app().root.ids.kalenderscreen.ids.colorpickerlist.add_widget(listitem)


class NeuerUserScreen(MDScreen):
    def __init__(self, **kwargs):
        super(NeuerUserScreen, self).__init__(**kwargs)
        # MDApp.get_running_app().root.ids["neuerUser"] = self

    def create_new_user(self):
        # 1. zur Datenbank verbinden - done
        # 2. auslesen ob der user schon vorhanden ist - done
        # a) wenn ja, prüfen, ob schon eine device id eingetragen ist - done
        # b) wenn nein, neuen user erstellen - done
        # 3. user id abspeichern und anhand dessen den kalender laden

        # 1.
        self.db = Database()
        if not self.db.connectToDatabase():
            self.db.closeDatabaseConnection()
            MDApp.get_running_app().root.changescreen('noInternet')
        # 2.
        else:
            try:
                self.df = self.db.requestData(table="Login", reqItem="device_id", param1="Benutzername",
                                              value1=self.ids.username.text)
                # id auslesen
                user_id = self.db.requestData(table="Login", param1="Benutzername",
                                              value1=self.ids.username.text)
                self.user_id = user_id[0]
                # 2.a)
                # falls device id bereits bei irgendeinem user eingetragen ist, diese löschen
                self.db.deleteDeviceID(device_id=MDApp.get_running_app().root.myid.id)
                # device id vom Server holen
                self.db.updateDeviceID(username=self.ids.username.text,
                                       device_id=MDApp.get_running_app().root.myid.id)
                self.db.closeDatabaseConnection()

                # Variablen abspeichern
                MDApp.get_running_app().root.username = user_id[1]
                MDApp.get_running_app().root.user_id = self.user_id

                # Vorlagen holen und speichern
                Clock.schedule_once(MDApp.get_running_app().root.set_vorlagen, .1)

                # Dienste vom Server holen
                MDApp.get_running_app().root.get_dienste_from_server()
                MDApp.get_running_app().root.save_dienste_into_txt()
                MDApp.get_running_app().root.get_dienste_from_txt()
                MDApp.get_running_app().root.ids.kalenderscreen.populate_calendar()

                # Timestamp abspeichern
                MDApp.get_running_app().root.save_timestamp()

                # Timestampthread starten
                timestampvergleichenthread = Thread(target=MDApp.get_running_app().root.timestampvergleichenthread)
                timestampvergleichenthread.start()
                # Kalendertitel setzen
                MDApp.get_running_app().root.ids.kalenderscreen.set_title()

                # zum Kalender wechseln
                MDApp.get_running_app().root.changescreen("kalender")

                # 2.b)
            except LookupError:
                # device id löschen, falls sie schon vorhanden ist

                try:
                    self.db.deleteDeviceID(device_id=MDApp.get_running_app().root.myid.id)
                except:
                    pass
                # neuen User hochladen
                self.db.createNewUser(username=self.ids.username.text, device_id=MDApp.get_running_app().root.myid.id)

                # user_id vom Server laden
                user_id = self.db.requestData(table="Login", reqItem="ID", param1="Benutzername",
                                              value1=self.ids.username.text)
                self.user_id = user_id[0]
                self.db.closeDatabaseConnection()

                # Variablen eintragen
                MDApp.get_running_app().root.username = self.ids.username.text
                MDApp.get_running_app().root.user_id = self.user_id

                # Vorlagen holen und speichern
                Clock.schedule_once(MDApp.get_running_app().root.set_vorlagen, .3)

                # Dienste vom Server holen
                MDApp.get_running_app().root.get_dienste_from_server()
                MDApp.get_running_app().root.save_dienste_into_txt()
                MDApp.get_running_app().root.get_dienste_from_txt()
                MDApp.get_running_app().root.ids.kalenderscreen.populate_calendar()

                # Timestamp abspeichern
                MDApp.get_running_app().root.save_timestamp()

                # Timestampthread starten
                timestampvergleichenthread = Thread(target=MDApp.get_running_app().root.timestampvergleichenthread)
                timestampvergleichenthread.start()

                # Kalendertitel setzen
                MDApp.get_running_app().root.ids.kalenderscreen.set_title()

                # zum Kalender wechseln
                MDApp.get_running_app().root.changescreen("kalender")

            except Exception as ex:
                toast(str(ex))

            finally:
                self.db.closeDatabaseConnection()


class Content(MDBoxLayout):
    pass


class VorlagenScreen(MDScreen):
    """ Hier werden alle Vorlagen angezeigt. Diese kann man bearbeiten oder löschen"""

    def late_init(self):
        # Liste leeren, damit die Einträge nicht mehrmals angezeigt werden
        self.ids.vorlagencontainer.clear_widgets()

        # Vorlagen vom root holen
        vorlagen = MDApp.get_running_app().root.vorlagen

        # Liste befüllen
        if vorlagen != "":
            for vorlage in vorlagen:
                startzeit = f"{str(vorlage[3]).zfill(2)}:{str(vorlage[4]).zfill(2)}"
                endzeit = f"{str(vorlage[5]).zfill(2)}:{str(vorlage[6]).zfill(2)}"
                cont = Vorlage_expansion_content()
                cont.set_times(startzeit, endzeit)
                vorlage_expansion = MDExpansionPanel(
                    content=cont,
                    panel_cls=MDExpansionPanelTwoLine(
                        text=f"{vorlage[7]}",
                        secondary_text=f"{str(vorlage[3]).zfill(2)}:{str(vorlage[4]).zfill(2)} - {str(vorlage[5]).zfill(2)}:{str(vorlage[6]).zfill(2)}"
                    )
                )
                self.ids.vorlagencontainer.add_widget(vorlage_expansion)

        else:
            # falls keine Vorlagen vorhanden sind, muss das angezeigt werden
            leereVorlagen = MDLabel(text="Keine Vorlagen vorhanden", halign="center")
            self.ids.vorlagencontainer.add_widget(leereVorlagen)

        # Pickers vorbereiten
        self.startzeit = MDTimePicker()
        self.startzeit.military = True
        self.startzeit.bind(time=self.selectedStartzeit)

        self.endzeit = MDTimePicker()
        self.endzeit.military = True
        self.endzeit.bind(time=self.selectedEndzeit)

    def deletevorlage(self, widget, widget_parent):
        """ Funktion zum Löschen von Vorlagen. Es wird die Vorlage im root, in der Datenbank und in der Liste gelöscht"""
        # Daten aufbereiten
        dienstbezeichnung = widget_parent.panel_cls.text
        startzeit_stunde = widget_parent.panel_cls.secondary_text[:2]
        startzeit_minute = widget_parent.panel_cls.secondary_text[3:5]
        endzeit_stunde = widget_parent.panel_cls.secondary_text[-5:-3]
        endzeit_minute = widget_parent.panel_cls.secondary_text[-2:]

        # Position einer Vorlage in der Liste finden
        counter = 0

        # herausfinden, welche Vorlage ausgewählt wurde und deren ID abspeichern
        for vorlage in MDApp.get_running_app().root.vorlagen:
            if (str(vorlage[3]).zfill(2) == str(startzeit_stunde)) and (
                    str(vorlage[4]).zfill(2) == str(startzeit_minute)) and (
                    str(vorlage[5]).zfill(2) == str(endzeit_stunde)) and (
                    str(vorlage[6]).zfill(2) == str(endzeit_minute)) and (
                    str(vorlage[7]) == str(dienstbezeichnung)):
                vorlagen_id = str(vorlage[0])
                listenposition = counter
            counter += 1

        try:
            # Vorlage in der Datenbank löschen
            vorlagendb = Database()
            if not vorlagendb.connectToDatabase():
                vorlagendb.closeDatabaseConnection()
                raise NoInternetConnection
            else:
                try:
                    vorlagendb.deleteVorlage(vorlagen_id=vorlagen_id)
                    vorlagendb.closeDatabaseConnection()

                    # Vorlage in der Liste löschen
                    self.ids.vorlagencontainer.remove_widget(widget_parent)

                    # Vorlage im root löschen
                    del MDApp.get_running_app().root.vorlagen[listenposition]

                except LookupError:
                    raise NoInternetConnection

        except NoInternetConnection:
            toast("Keine Verbindung zum Server. Bitte versuche es erneut")

    def editvorlage(self, widget, widget_parent):
        """ Funktion zum Bearbeiten einer Vorlage:
        Startzeit mit Timepicker
        Endzeit mit Timepicker
        Dienstbezeichnung mit Textfeld
        """
        # Daten aufbereiten
        dienstbezeichnung = widget_parent.panel_cls.text
        startzeit = datetime.strptime(widget.ids.startzeit.text, '%H:%M')
        endzeit = datetime.strptime(widget.ids.endzeit.text, '%H:%M')

        # Vorlagen_id suchen
        counter = 0
        for vorlage in MDApp.get_running_app().root.vorlagen:
            if vorlage[7] == dienstbezeichnung:
                vorlagen_id = vorlage[0]
                vorlagennummerinrootvorlagen = counter
            counter += 1

        # Vorlage updaten
        self.db = Database()
        try:
            if not self.db.connectToDatabase():
                self.db.closeDatabaseConnection()
                raise NoInternetConnection
            else:
                # in der Datenbank updaten
                self.db.updateVorlage(startzeith=startzeit.hour, startzeitmin=startzeit.minute, endzeith=endzeit.hour,
                                      endzeitmin=endzeit.minute, vorlagen_id=vorlagen_id)
                self.db.closeDatabaseConnection()

                # in den root Vorlagen updaten
                rootvorlage = list(MDApp.get_running_app().root.vorlagen[vorlagennummerinrootvorlagen])
                rootvorlage[3] = str(startzeit.hour)
                rootvorlage[4] = str(startzeit.minute)
                rootvorlage[5] = str(endzeit.hour)
                rootvorlage[6] = str(endzeit.minute)
                rootvorlage = tuple(rootvorlage)
                MDApp.get_running_app().root.vorlagen[vorlagennummerinrootvorlagen] = rootvorlage

                # in der Liste updaten
                widget_parent.panel_cls.secondary_text = f"{widget.ids.startzeit.text} - {widget.ids.endzeit.text}"

                toast("Vorlage erfolgreich geändert")

        except NoInternetConnection:
            toast("Keine Verbindung zum Server. Bitte prüfe deine Internetverbindung!")

    def timepicker_startzeit(self, widget):
        self.startzeit_btn = widget
        self.startzeit.set_time(datetime.strptime(widget.text, '%H:%M'))
        self.startzeit.open()

    def selectedStartzeit(self, instance, time):
        startzeittext = time.strftime('%H:%M')
        self.startzeit_btn.text = str(startzeittext)

    def timepicker_endzeit(self, widget):
        self.endzeit_btn = widget
        self.endzeit.set_time(datetime.strptime(widget.text, '%H:%M'))
        self.endzeit.open()

    def selectedEndzeit(self, instance, time):
        endzeittext = time.strftime('%H:%M')
        self.endzeit_btn.text = str(endzeittext)


class Vorlage_expansion_content(TwoLineRightIconListItem):
    def __init__(self, **kwargs):
        super(Vorlage_expansion_content, self).__init__()
        self.ids._right_container.width = self.ids.container.width * 2
        self.ids._right_container.x = self.ids.container.width - 120
        self._no_ripple_effect = True

    def set_times(self, startzeit, endzeit):
        self.ids.startzeit.text = startzeit
        self.ids.endzeit.text = endzeit


class RechteSeiteContainer(IRightBodyTouch, MDBoxLayout):
    adaptive_width = True


class StartScreen(MDScreen):
    def __init__(self, **kwargs):
        super(StartScreen, self).__init__(**kwargs)
        # MDApp.get_running_app().root.ids["start"] = self


class NoInternetScreen(MDScreen):
    def __init__(self, **kwargs):
        super(NoInternetScreen, self).__init__(**kwargs)
        # MDApp.get_running_app().root.ids["noInternet"] = self

    def on_enter(self, *args):
        Clock.schedule_once(self.show_popup, 1)

    def show_popup(self, *args):
        self.nointernet = MDDialog(title="Problem beim Verbinden zur Datenbank!",
                                   text="Vergewissere dich, dass du mit dem Internet verbunden bist und versuche es erneut!",
                                   )
        self.nointernet.bind(on_dismiss=self.try_again)
        self.nointernet.open()

    def try_again(self, obj):
        if not MDApp.get_running_app().root.has_screen('start'):
            MDApp.get_running_app().root.add_widget(StartScreen())
        MDApp.get_running_app().root.changescreen(screen="start", transition="NoTransition")
        Clock.schedule_once(MDApp.get_running_app().root.get_login_information, .2)


class MyScreenManager(ScreenManager):
    myid = uniqueid
    username = "a"
    user_id = 0
    vorlagen = ""

    def __init__(self, **kwargs):
        super(MyScreenManager, self).__init__(**kwargs)
        self.get_feiertage()
        self.get_config()
        self.get_login_information()

    def get_config(self):
        if platform == 'android':
            self.settings = EasySettings("../dienstplanconfigfile.conf")
        else:
            self.settings = EasySettings("testconfigfile.conf")
        self.settingsdict = {}
        for key, value in self.settings.list_settings():
            self.settingsdict[key] = value

        if not "schriftgroesse" in self.settings.list_options():
            self.settingsdict["schriftgroesse"] = str(18)
            self.settings.setsave("schriftgroesse", str(18))
            self.firststart = True

    def get_login_information(self, *args):
        self.db = Database()
        if not self.db.connectToDatabase():
            self.db.closeDatabaseConnection()
            if platform == 'android':
                if not self.has_screen('noInternet'):
                    self.add_widget(NoInternetScreen())
                self.changescreen(screen="noInternet", transition="NoTransition")
            else:
                # falls in der Testumgebung, dann Dummyvorlagen und -dienste laden
                self.vorlagen = self.settingsdict["vorlagen"]
                self.set_dienste(1)
                timestampvergleichenthread = Thread(target=self.timestampvergleichenthread)
                timestampvergleichenthread.start()
                self.get_feiertage()
                self.changescreen(screen="kalender", transition="NoTransition")

        else:
            try:
                self.df = self.db.requestData(table="Login", param1="device_id", value1=self.myid.id)
                self.db.closeDatabaseConnection()

                # Benutzernamen speichern
                self.username = self.df[1]
                self.user_id = self.df[0]

                # Vorlagen speichern
                self.set_vorlagen(1)

                # Feiertage speichern
                self.get_feiertage()

                # Kalenderdaten holen
                self.set_dienste(1)

                # Timestampthread starten
                timestampvergleichenthread = Thread(target=self.timestampvergleichenthread)
                timestampvergleichenthread.start()

                # zum Kalender
                self.changescreen(screen="kalender", transition="NoTransition")

            except LookupError:
                self.db.closeDatabaseConnection()
                if not self.has_screen('neuerUser'):
                    self.add_widget(NeuerUserScreen())
                self.changescreen(screen="neuerUser", transition="NoTransition")

            except Exception as ex:
                print(str(ex))

            finally:
                self.db.closeDatabaseConnection()

    def set_vorlagen(self, dt):
        try:
            # Vorlagen laden
            self.vorlagendb = Database()
            if not self.vorlagendb.connectToDatabase():
                self.vorlagendb.closeDatabaseConnection()
                toast("Vorlagen konnten nicht vom Server gelesen werden. Bitte prüfe deine Internetverbindung!")
            else:
                self.vorlagen = self.vorlagendb.requestAllRowsInTable(table="Vorlagen", param1="Benutzer_ID",
                                                                      value1=self.user_id, sort=True)
                self.vorlagen = list(self.vorlagen)
                self.vorlagendb.closeDatabaseConnection()

        except ValueError:
            self.vorlagen = ""
            print("ValueError")
        except AttributeError:
            self.vorlagen = ""
            print("AttributeError")
        except LookupError:
            self.vorlagen = ""
            print("LookupError")

        finally:
            self.vorlagendb.closeDatabaseConnection()
            Clock.schedule_once(self.ids.neuerEintrag.late_init, .5)

    def set_dienste(self, dt):
        try:
            # falls es das timestamp file gibt, öffnen und auslesen. danach wieder schließen
            timestampfile = open("timestamp.txt")
            timestamp = timestampfile.readline()
            timestampfile.close()
            timestamp = datetime.strptime(timestamp, "%Y, %m, %d, %H, %M, %S")

            # Servertimestamp und Filetimestamp vergleichen
            try:
                servertimestamp = self.get_servertimestamp()
            except:
                servertimestamp = datetime.today()

            # wenn die timestamps gleich sind:
            # dienstetxt einlesen & kalender damit befüllen
            if timestamp == servertimestamp:
                self.get_dienste_from_txt()

            # wenn die timestamps nicht gleich sind:
            # dienste vom server laden
            # dienste in txt schreiben
            # zeit vom servertimestamp in timestamp.txt schreiben
            # kalender mit diensten befüllen
            else:
                # Dienste vom Server holen
                self.get_dienste_from_server()

                # Dienste in txt abspeichern
                self.save_dienste_into_txt()

                # Dienste von txt wieder einlesen. Dadurch wird jeder Dienst richtig aufbereitet
                self.get_dienste_from_txt()

                # timestamp file öffnen und zeit vom timestamp reinschreiben
                try:
                    servertimestamp = self.get_servertimestamp()
                except:
                    servertimestamp = datetime.today()

                servertimestamp = servertimestamp.strftime("%Y, %m, %d, %H, %M, %S")
                timestampfile = open("timestamp.txt", "w")
                timestampfile.write(servertimestamp)
                timestampfile.close()

        except:
            # wenn es das timestamp file noch nicht gibt, dieses erstellen
            timestampfile = open("timestamp.txt", "w")
            timestampfile.write("2021, 02, 02, 10, 17, 48")
            timestampfile.close()

            # Dienste vom Server holen
            self.get_dienste_from_server()

            # Dienste in txt abspeichern
            self.save_dienste_into_txt()

            # Dienste txt wieder einlesen. Dadurch werden die Dienste richtig aufbereitet
            self.get_dienste_from_txt()

            # timestamp file öffnen und zeit vom timestamp reinschreiben
            servertimestamp = self.get_servertimestamp()

            servertimestamp = servertimestamp.strftime("%Y, %m, %d, %H, %M, %S")
            timestampfile = open("timestamp.txt", "w")
            timestampfile.write(servertimestamp)
            timestampfile.close()

    def get_servertimestamp(self):
        timestampdb = Database()
        if not timestampdb.connectToDatabase():
            timestampdb.closeDatabaseConnection()
            timestamp = datetime.today()
            return timestamp
        else:
            servertimestamp = timestampdb.requestData(table="Timestamp")
            timestampdb.closeDatabaseConnection()
            return servertimestamp[0]

    def get_dienste_from_server(self):
        actyear = date.today().year
        dienstedb = Database()
        if not dienstedb.connectToDatabase():
            dienstedb.closeDatabaseConnection()
            if platform != 'android':
                self.dienste = self.settingsdict["dienste"]
        else:
            self.dienste = dienstedb.requestDienste(lastyear=actyear - 1, nextyear=actyear + 1)
            self.dienste = list(self.dienste)
            dienstedb.closeDatabaseConnection()

    def save_dienste_into_txt(self):
        # Dienste in txt abspeichern
        with open('dienste.txt', 'w') as dienstefile:
            for dienst in self.dienste:
                dienstforfile = str(dienst)
                dienstforfile = dienstforfile[1:-1]
                dienstefile.writelines(dienstforfile + '\n')

    def get_dienste_from_txt(self):
        dienstefile = open("dienste.txt", "r")
        self.dienste = dienstefile.readlines()
        dienstefile.close()

        diensteliste = []
        for dienst in self.dienste:
            dienst = dienst.split(", ")
            diensteliste.append(dienst)
        self.dienste = diensteliste

    def get_feiertage(self, jahr=datetime.now().year):
        holidays = bf.Holidays(jahr, 'TI')
        self.feiertage = holidays.get_holiday_list()

    def changescreen(self, screen, direction="left", transition="SlideTransition"):
        # self.transition.direction = direction
        if transition == "SwapTransition":
            self.transition = SwapTransition()
        elif transition == "NoTransition":
            self.transition = NoTransition()
        else:
            self.transition = SlideTransition()

        self.__screen = screen
        Clock.schedule_once(self._changescreen, .2)

    def _changescreen(self, dt):
        self.current = self.__screen

    def save_timestamp(self):
        servertimestamp = self.get_servertimestamp()
        servertimestamp = servertimestamp.strftime("%Y, %m, %d, %H, %M, %S")
        timestampfile = open("timestamp.txt", "w")
        timestampfile.write(servertimestamp)
        timestampfile.close()

    def timestampvergleichenthread(self, dt=0):
        while True:
            try:
                # Servertimestamp holen
                servertimestamp = self.get_servertimestamp()
                servertimestamp2 = self.get_servertimestamp()
                if servertimestamp != servertimestamp2:
                    break
                servertimestamp = servertimestamp.strftime("%Y, %m, %d, %H, %M, %S")
                servertimestamp = datetime.strptime(servertimestamp, "%Y, %m, %d, %H, %M, %S")

                # gespeicherten timestamp holen
                timestampfile = open("timestamp.txt")
                timestamp = timestampfile.readline()
                timestampfile.close()
                timestamp = datetime.strptime(timestamp, "%Y, %m, %d, %H, %M, %S")

                # wenn die timestamps unterschiedlich sind, dienste neu laden und timestamp speichern
                if servertimestamp != timestamp:
                    self.get_dienste_from_server()
                    self.save_dienste_into_txt()
                    self.get_dienste_from_txt()

                    if self.current == "kalender":
                        try:
                            MDApp.get_running_app().root.ids.kalenderscreen.populate_calendar()
                        except AttributeError:
                            pass

                    servertimestamp = servertimestamp.strftime("%Y, %m, %d, %H, %M, %S")
                    timestampfile = open("timestamp.txt", "w")
                    timestampfile.write(servertimestamp)
                    timestampfile.close()
                break

            except:
                break

        Clock.schedule_once(self.timestampvergleichenthread, 40)

    def setschriftgroesse(self, groesse):
        self.settingsdict["schriftgroesse"] = int(groesse)


class KalenderApp(MDApp):
    def build(self):
        sm = MyScreenManager()
        return sm

    def on_pause(self):
        # Here you can save data if needed
        return True

    def on_resume(self):
        # Here you can check if any data needs replacing (usually nothing)
        pass


if __name__ == '__main__':
    KalenderApp().run()
