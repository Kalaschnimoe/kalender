from kivy.lang import Builder

from kivymd.app import MDApp
from kivymd.uix.tab import MDTabsBase
from kivymd.uix.floatlayout import MDFloatLayout
from kivymd.icon_definitions import md_icons

KV = '''
MDBoxLayout:
    orientation: "vertical"

    MDToolbar:
        title: "Example Tabs"

    MDTabs:
        id: tabs
        on_tab_switch: app.next(*args)


<Tab>

    MDIconButton:
        id: icon
        icon: root.icon
        user_font_size: "48sp"
        pos_hint: {"center_x": .5, "center_y": .5}
'''


class Tab(MDFloatLayout, MDTabsBase):
    '''Class implementing content for a tab.'''


class Example(MDApp):
    icons = list(md_icons.keys())[15:30]

    def build(self):
        return Builder.load_string(KV)

    def on_start(self):
        for tab_name in self.icons:
            self.root.ids.tabs.add_widget(Tab(icon=tab_name))

    def next(
        self, instance_tabs, instance_tab, instance_tab_label, tab_text
    ):
        '''
        Called when switching tabs.

        :type instance_tabs: <kivymd.uix.tab.MDTabs object>;
        :param instance_tab: <__main__.Tab object>;
        :param instance_tab_label: <kivymd.uix.tab.MDTabsLabel object>;
        :param tab_text: text or name icon of tab;
        '''
        # get the tab icon.
        count_icon = instance_tab.icon
        # print it on shell/bash.
        print(f"Welcome to {count_icon}' tab'")


Example().run()