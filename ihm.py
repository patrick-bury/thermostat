#!/usr/bin/env python
# -*- coding: utf-8 -*-

from gi.repository import Gtk
from gi.repository import GObject
from datetime import datetime
import os.path
import wget
from PIL import Image
import sys

from models import Agenda, Temperature, Config, Status


class Thermo:

    @staticmethod
    def set_hors_gel(status):
        config = Config()
        Status().set('hors_gel', status)

        if status:
            hors_gel_temp = Config.get(Config.clef == 'temp_consigne_hors_gel').valeur
            config.set('temp_consigne_eco', hors_gel_temp)
            config.set('temp_consigne_confort', hors_gel_temp)
        else:
            config.set('temp_consigne_eco', Config.get(Config.clef == 'default_temp_consigne_eco').valeur)
            config.set('temp_consigne_confort', Config.get(Config.clef == 'default_temp_consigne_confort').valeur)


class Meteo:

    @staticmethod
    def get_meteogramme():
        meteoblue_url = Config.get(Config.clef == 'meteoblue').valeur
        filename = '/usr/local/bin/thermostat/data/meteo/' + datetime.now().strftime("%Y_%m_%d")+".png"
        if not os.path.isfile(filename):
            try:
                download_name = wget.download(meteoblue_url)
                os.rename(download_name, filename)
                img = Image.open(filename)
                w, h = img.size
                img = img.crop((0, 30, w, h-290))
                img.save('/usr/local/bin/thermostat/data/meteo/meteogramme.png')
            except Exception:
                pass


class Afficheur(Thermo):

    def on_window1_destroy(self, object, data=None):
        print("quit with cancel")
        Gtk.main_quit()

    def on_gtk_quit_activate(self, menuitem, data=None):
        print("quit from menu")
        Gtk.main_quit()

    def delete(self, source=None, event=None):
        Gtk.main_quit()

    def on_marche_forcee(self, switch=None, event=None):
        if event:
            Status().set('marche_forcee', True)
            Status().set('status_chauffage', True)
            Status().set('status_programme', 'Reste '+str(Status().get(Status.clef == 'marche_forcee_remaining').valeur) +' mn')
        else:
            Status().set('marche_forcee', False)
            Status().set('marche_forcee_remaining', 30.0)
            Status().set('status_programme', 'default')

        self.refresh_status_bar()

    def on_marche_forcee_changed(self, switch=None, event=None):
        Status().set('marche_forcee_remaining', switch.get_model()[switch.get_active()][1])
        self.refresh_status_bar()

    def on_consigne_eco_changed(self, switch=None, event=None):
        Config().set('temp_consigne_eco', switch.get_model()[switch.get_active()][1])
        self.refresh_status_bar()

    def on_consigne_confort_changed(self, switch=None, event=None):
        Config().set('temp_consigne_confort', switch.get_model()[switch.get_active()][1])
        self.refresh_status_bar()

    def refresh_status_bar(self):
        self.meteo.get_meteogramme()
        msg_line = Status().get(Status.clef == 'message').valeur
        default_line = datetime.now().strftime('%H:%M:%S')
        if msg_line != '-':
            status_msg = msg_line + '\n' + default_line
        else:
            status_msg = default_line
        Status().set('status_programme_default', status_msg)
        if Status.get(Status.clef == 'status_programme').valeur == 'default':
            self.builder.get_object('status_programme').set_text(Status().get(Status.clef == 'status_programme_default').valeur)
        if Status().get(Status.clef == 'marche_forcee').valeur == 'True':
            self.builder.get_object('status_confort_level').set_text('Marche forcée')
            Status().set('marche_forcee_remaining',
                         str(float(Status().get(Status.clef == 'marche_forcee_remaining').valeur)
                             - float(Config().get(Config.clef == 'intervalle_mesure').valeur)/60.))
            Status().set('status_programme',
                         'Reste '+str(float(Status().get(Status.clef == 'marche_forcee_remaining').valeur))+' mn')
            self.builder.get_object('status_programme').set_text(
                Status.get(Status.clef == 'status_programme_default').valeur
                + '\n'
                + Status.get(clef='status_programme').valeur)
            if float(Status.get(Status.clef == 'marche_forcee_remaining').valeur) < 1:
                Status().set('marche_forcee_remaining', 0.0)
                Status().set('marche_forcee', False)
                # changer l'etat du bouton
                self.builder.get_object('switch_marche_forcee').set_active(False)
        else:
            self.builder.get_object('value_temp_eco').set_text(str(Config().get(Config.clef == 'temp_consigne_eco').valeur))
            self.builder.get_object('value_temp_confort').set_text(str(Config().get(Config.clef == 'temp_consigne_confort').valeur))
            if Status().get(Status.clef == 'hors_gel') == 'True':
                self.builder.get_object('status_confort_level').set_text('Hors Gel')
                self.builder.get_object('value_temp_eco').set_text(str(Config().get(Config.clef == 'hors_gel_temp').valeur))
                self.builder.get_object('value_temp_confort').set_text(str(Config().get(Config.clef == 'hors_gel_temp').valeur))
            else:
                self.builder.get_object('status_confort_level').set_text(Status().get(Status.clef == 'confort_level').valeur)

        self.builder.get_object('status_chauffage').set_text(Status.get(Status.clef == 'status_chauffage').valeur)
        self.builder.get_object('status_chauffage').set_use_markup(True)

        self.builder.get_object('value_temp_eco').set_text(str(Config().get(Config.clef == 'temp_consigne_eco').valeur))
        self.builder.get_object('value_temp_confort').set_text(str(Config().get(Config.clef == 'temp_consigne_confort').valeur))
        temp = (int(10 * Temperature().get_last('sejour')))/10.
        self.builder.get_object('status_temp_sejour').set_text(str(temp))
#        temp = (int(10 * Temperature().get_last('ext')))/10.
#        self.builder.get_object('status_temp_ext').set_text(str(temp))
        self.builder.get_object('message_jour').set_text(', '.join(Agenda().get_events_for_now()))
        self.builder.get_object('image_meteo').set_from_file('data/meteo/meteogramme.png')
        return True

    def on_hors_gel(self, switch=None, event=None):
        Thermo().set_hors_gel(event)
        self.refresh_status_bar()

    def get_status_chauffage_txt(self):
        if self.get_status_chauffage():
            return '<span foreground="#ff0000">On</span>'
        else:
            return 'Off'

    def __init__(self):
        self.agenda = Agenda()
        self.meteo = Meteo()

        self.gladefile = "/usr/local/bin/thermostat/glade_1.glade"
        self.builder = Gtk.Builder()
        self.builder.add_from_file(self.gladefile)
        self.builder.connect_signals(self)
        self.window = self.builder.get_object("window1")
        GObject.PRIORITY_DEFAULT = 1
        GObject.timeout_add_seconds(int(Config().get(Config.clef == 'intervalle_mesure').valeur), self.refresh_status_bar)
        self.builder.get_object('status_temp_sejour').set_text(str(Temperature().get_last('sejour')))
        self.builder.get_object('status_temp_ext').set_text(str(Temperature().get_last('ext')))
        self.builder.get_object('status_chauffage').set_text(Status.get(Status.clef == 'status_chauffage').valeur)
        self.builder.get_object('status_chauffage').set_use_markup(True)
        self.builder.get_object('status_confort_level').set_text('Eco')
        self.refresh_status_bar()
        self.window.show()

if __name__ == "__main__":
    Status().set('marche_forcee_remaining', '30.0')
    main = Afficheur()
    Gtk.main()

