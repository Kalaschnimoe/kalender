import datetime
import math

state_codes = {
    'Tirol': 'TI',
    'Niederösterreich': 'NO',
    'Baden-Württemberg': 'BW',
    'Bayern': 'BY',
    'Berlin': 'BE',
    'Brandenburg': 'BB',
    'Bremen': 'HB',
    'Hamburg': 'HH',
    'Hessen': 'HE',
    'Mecklenburg-Vorpommern': 'MV',
    'Niedersachsen': 'NI',
    'Nordrhein-Westfalen': 'NW',
    'Rheinland-Pfalz': 'RP',
    'Saarland': 'SL',
    'Sachsen': 'SN',
    'Sachsen-Anhalt': 'ST',
    'Schleswig-Holstein': 'SH',
    'Thüringen': 'TH'
}


def holidays(year, state=None):
    """
    prüft die eingegebenen Werte für die Berechnung der Feiertage
    year  => Jahreszahl ab 1970
    state => Bundesland als offizielle Abkürzung oder Vollname
    """

    try:
        year = int(year)
        if year < 1970:
            year = 1970
            print(u'Jahreszahl wurde auf 1970 geändert')
    except ValueError:
        print(u'Fehlerhafte Angabe der Jahreszahl')
        return

    if state:
        if state in state_codes.keys():
            state_code = state_codes[state]
        else:
            if state.upper() in state_codes.values():
                state_code = state.upper()
            else:
                state_code = None
    else:
        state_code = None

    if not state_code:
        print(u'Es werden nur die deutschlandweit gültigen Feiertage ausgegeben')

    hl = Holidays(year, state_code)
    holidays = hl.get_holiday_list()
    for h in holidays:
        print(h[1], h[0])


class Holidays:
    """
    Berechnet die Feiertage für ein Jahr. Wird ein Bundesland übergeben, werden
    alle Feiertage des Bundeslandes zurückgegeben. Das erfolgt über die
    Funktion get_holiday_list().
    Das Bundesland (state_code) muss mit der offiziellen zweistelligen
    Bezeichnung übergeben werden (z.B. Sachsen mit SN)

    Holidays(year(int), [state_code(str)])
    """

    def __init__(self, year, state_code):
        self.year = int(year)
        if self.year < 1970:
            self.year = 1970
        if state_code:
            self.state_code = state_code.upper()
            if self.state_code not in state_codes.values():
                self.state_code = None
        easter_day = EasterDay(self.year)
        self.easter_date = easter_day.get_date()
        self.holiday_list = []
        self.general_public_holidays()

        if state_code:
            self.get_three_kings(state_code)
            self.get_assumption_day(state_code)
            self.get_reformation_day(state_code)
            self.get_all_saints_day(state_code)
            self.get_repentance_and_prayer_day(state_code)
            self.get_corpus_christi(state_code)

    def get_holiday_list(self):
        """
        Gibt die Liste mit den Feiertagen zurück
        """
        self.holiday_list.sort()
        return self.holiday_list

    def general_public_holidays(self):
        """
        Alle bundeseinheitlichen Feiertage werden der Feiertagsliste
        zugefügt.
        """
        # feste Feiertage:
        newyear = datetime.date(self.year, 1, 1)
        self.holiday_list.append([newyear, u'Neujahr'])
        may = datetime.date(self.year, 5, 1)
        self.holiday_list.append([may, u'Tag der Arbeit'])
        nationalfeiertag = datetime.date(self.year, 10, 26)
        self.holiday_list.append([nationalfeiertag, u'Nationalfeiertag'])
        allerheiligen = datetime.date(self.year, 11, 1)
        self.holiday_list.append([allerheiligen, u'Allerheiligen'])
        mariaempfaengnis = datetime.date(self.year, 12, 8)
        self.holiday_list.append([mariaempfaengnis, u'Maria Empfängnis'])
        weihnachten = datetime.date(self.year, 12, 24)
        self.holiday_list.append([weihnachten, u'Weihnachten'])
        christmas1 = datetime.date(self.year, 12, 25)
        self.holiday_list.append([christmas1, u'Christtag'])
        christmas2 = datetime.date(self.year, 12, 26)
        self.holiday_list.append([christmas2, u'Stefanitag'])
        # bewegliche Feiertage:
        #self.holiday_list.append([self.get_holiday(2, _type='minus'), u'Karfreitag'])
        self.holiday_list.append([self.easter_date, u'Ostersonntag'])
        self.holiday_list.append([self.get_holiday(1), u'Ostermontag'])
        self.holiday_list.append([self.get_holiday(39), u'Christi Himmelfahrt'])
        self.holiday_list.append([self.get_holiday(49), u'Pfingstsonntag'])
        self.holiday_list.append([self.get_holiday(50), u'Pfingstmontag'])

    def get_holiday(self, days, _type='plus'):
        """
        Berechnet anhand des Ostersonntages und der übergebenen Anzahl Tage
        das Datum des gewünschten Feiertages. Mit _type wird bestimmt, ob die Anzahl
        Tage addiert oder subtrahiert wird.
        """
        delta = datetime.timedelta(days=days)
        if _type == 'minus':
            return self.easter_date - delta
        else:
            return self.easter_date + delta

    def get_three_kings(self, state_code):
        """ Heilige Drei Könige """
        valid = ['BY', 'BW', 'ST', 'TI', 'NO']
        if state_code in valid:
            three_kings = datetime.date(self.year, 1, 6)
            self.holiday_list.append([three_kings, u'Heilige Drei Könige'])

    def get_assumption_day(self, state_code):
        """ Mariä Himmelfahrt """
        valid = ['BY', 'SL', 'TI', 'NO']
        if state_code in valid:
            assumption_day = datetime.date(self.year, 8, 15)
            self.holiday_list.append([assumption_day, u'Mariä Himmelfahrt'])

    def get_reformation_day(self, state_code):
        """ Reformationstag """
        valid = ['BB', 'MV', 'SN', 'ST', 'TH']
        if state_code in valid:
            reformation_day = datetime.date(self.year, 10, 31)
            self.holiday_list.append([reformation_day, u'Reformationstag'])

    def get_all_saints_day(self, state_code):
        """ Allerheiligen """
        valid = ['BW', 'BY', 'NW', 'RP', 'SL']
        if state_code in valid:
            all_saints_day = datetime.date(self.year, 11, 1)
            self.holiday_list.append([all_saints_day, u'Allerheiligen'])

    def get_repentance_and_prayer_day(self, state_code):
        """
        Buß und Bettag
        (Mittwoch zwischen dem 16. und 22. November)
        """
        valid = ['SN']
        if state_code in valid:
            first_possible_day = datetime.date(self.year, 11, 16)
            rap_day = first_possible_day
            weekday = rap_day.weekday()
            step = datetime.timedelta(days=1)
            while weekday != 2:
                rap_day = rap_day + step
                weekday = rap_day.weekday()
            self.holiday_list.append([rap_day, u'Buß und Bettag'])

    def get_corpus_christi(self, state_code):
        """
        Fronleichnam
        60 Tage nach Ostersonntag
        """
        valid = ['BW', 'BY', 'HE', 'NW', 'RP', 'SL', 'TI', 'NO']
        if state_code in valid:
            corpus_christi = self.get_holiday(60)
            self.holiday_list.append([corpus_christi, u'Fronleichnam'])


class EasterDay:
    """
    Berechnung des Ostersonntages nach der Formel von Heiner Lichtenberg für
    den gregorianischen Kalender. Diese Formel stellt eine Zusammenfassung der
    Gaußschen Osterformel dar
    Infos unter http://de.wikipedia.org/wiki/Gaußsche_Osterformel
    """

    def __init__(self, year):
        self.year = year

    def get_m(self):
        """
        säkulare Mondschaltung:
        M(K) = 15 + (3K + 3) div 4 − (8K + 13) div 25
        """
        m = 24  # Konstante
        return m

    def get_a(self):
        """
        Jahr im 19-jährigen Osterzyklus. Wert 0 – 18, entspricht der um 1 verringerten Goldenen Zahl.
        """
        a = self.year % 19
        return a

    def get_b(self):
        """Zyklus der Schaltjahre, Wert 0 – 3"""
        b = self.year % 4
        return b

    def get_c(self):
        """Zyklus der Wochentage, Wert 0 – 6"""
        c = self.year % 7
        return c

    def get_d(self):
        """
        Abstand der „Luna XIV“ vom 21. März, Wert 0 – 29
        """
        a = self.get_a()
        m = self.get_m()
        d = (19 * a + m) % 30
        return d

    def get_e(self):
        """ Abstand des auf „Luna XIV“ folgenden Tages (frühester Ostertermin) zum folgenden Sonntag, Wert 0 – 6 """
        b = self.get_b()
        c = self.get_c()
        d = self.get_d()
        n = 5  # Konstante
        e = (2 * b + 4 * c + 6 * d + n) % 7
        return e

    def get_os(self):
        """
        das Datum des Ostersonntags
        """
        e = self.get_e()
        d = self.get_d()
        summe = d + e + 1
        return summe

    def get_date(self):
        """
        Ausgabe des Ostersonntags als datetime-Objekt
        """
        os = self.get_os()

        # Frühlingsvollmond: 21.03. + Jahrzahl
        fvm = datetime.date(self.year, 3, 21)

        easter_day = fvm + datetime.timedelta(days=os)
        return easter_day


if __name__ == '__main__':
    y = input('Bitte geben Sie die Jahreszahl ein: ')
    print(u'Für die Eingabe eines Bundeslandes folgende Abkürzungen verwenden:')
    print(u'< leer > um kein Bundesland auszuwählen')
    states = state_codes.keys()
    for l in states:
        print('%s für %s' % (state_codes[l], l))
    s = input('Bitte geben Sie das gewünschte Bundesland ein: ')
    holidays(y, s)
