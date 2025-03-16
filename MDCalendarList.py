from kivymd.app import MDApp
from kivy.lang import Builder

from kivy.uix.screenmanager import ScreenManager
from kivymd.uix.screen import MDScreen
from kivy.uix.recycleview import RecycleView
from kivymd.uix.list import OneLineListItem
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton
from pathlib import Path

import requests
import json

kv = """
<CustomRecycle>:
    key_viewclass: 'viewclass'
    key_size: "height"


    RecycleBoxLayout:
        padding: "10dp"
        default_size: None, dp(48)
        default_size_hint: 1, None
        size_hint_y: None
        height: self.minimum_height
        orientation: "vertical"

<Countries>:
    MDBoxLayout:
        orientation: 'vertical'
        MDTextField:
            hint_text: 'Search for Country'
            size_hint_x: .95
            pos_hint: {"center_x": .5}
            on_text: root.set_list(self.text, True)

        CountryRecycle:
            id: recycle

<Cities>:
    MDBoxLayout:
        orientation: 'vertical'
        MDBoxLayout:
            orientation: 'horizontal'
            size_hint_y: .1
            MDIconButton:
                icon: 'arrow-left'
                on_release: 
                    root.parent.current = 'countries'
                    root.parent.transition.direction = 'right'

            MDTextField:
                hint_text: 'Search for City'
                size_hint_x: .9
                pos_hint: {"center_x": .5}
                on_text: 
                    root.set_list(self.text, True, root.parent.get_screen('countries').country)

        CountryRecycle:
            id: rv

<CountryRecycle@CustomRecycle>:

<CountryListItem>:
    on_release: 
        self.parent.parent.parent.parent.country = self.text
        self.sm = self.parent.parent.parent.parent.parent
        self.sm.get_screen('city').set_list("", False, self.text)
        self.sm.transition.direction = 'left'
        self.sm.current = 'city'


<CityListItem>:
    on_release: self.saveLocation(self.text)

"""


class CityListItem(OneLineListItem):
    def saveLocation(self, location):
        with open("../data/config.json", 'r') as f:
            file = json.load(f)

        file['location'] = str(location)

        with open('../data/config.json', 'w') as f:
            json.dump(file, f)


class CountryListItem(OneLineListItem):
    pass


class Cities(MDScreen):
    def set_list(self, text="", search=False, country=None):
        cities = json.loads(requests.get(
            'https://raw.githubusercontent.com/russ666/all-countries-and-cities-json/master/countries.json').text)

        def add_icon_item(city):
            self.ids.rv.data.append(
                {
                    "viewclass": "CityListItem",
                    "text": city,
                    "callback": lambda x: x,
                }
            )

        self.ids.rv.data = []
        for city in cities[country]:
            if search:
                if text.lower() in city.lower():
                    add_icon_item(city)
            else:
                add_icon_item(city)


class Countries(MDScreen):
    def set_list(self, text="", search=False):
        countries_cities = json.loads(requests.get(
            'https://raw.githubusercontent.com/russ666/all-countries-and-cities-json/master/countries.json').text)

        def add_icon_item(country):
            self.ids.recycle.data.append(
                {
                    "viewclass": "CountryListItem",
                    "text": country,
                    "callback": lambda x: x,
                }
            )

        self.ids.recycle.data = []

        for country in countries_cities:
            if search:
                if text.lower() in country.lower():
                    add_icon_item(country)
            else:
                add_icon_item(country)


class LocationContent(MDScreen):
    def build(self):
        return Builder.load_string(kv)

    def create(self):
        self.build()

        country_screen = Countries(name="countries")
        country_screen.set_list()

        city_screen = Cities(name="city")

        sm = ScreenManager()
        sm.add_widget(country_screen)
        sm.add_widget(city_screen)

        sm.current = "countries"
        self.add_widget(sm)

        return self


class CustomRecycle(RecycleView):
    pass


class test(MDApp):
    def build(self):
        screen = MDScreen()
        button = MDFlatButton(text="Click Me", on_release=self.open_dialog)
        screen.add_widget(button)

        self.content = LocationContent(size_hint_y=None, height=400).create()

        self.dialog = MDDialog(
            type="custom",
            title="Choose Location",
            content_cls=self.content,
        )

        self.dialog.size_hint_x = .9

        return screen

    def open_dialog(self, instance):
        self.dialog.open()


if __name__ == '__main__':
    test().run()