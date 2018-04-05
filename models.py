# -*- coding: utf-8 -*-
from datetime import datetime, date, time

import peewee
from peewee import mysql

print(mysql)

database = peewee.MySQLDatabase(
    'thermostat',
    host='192.168.0.80',
    user='thermostat',
    passwd='toto'
)


class BaseModel(peewee.Model):
    class Meta:
        database = database


class Agenda(BaseModel):
    """
    Modele de la table agenda
    """
    date = peewee.CharField()
    message = peewee.CharField()

    def get_events(self, jour_semaine):
        events = []
        for event in self.select().where(Agenda.date == jour_semaine):
            events.append(str(event.message))
        return events

    def get_events_for_now(self):
        events = []
        jour_semaine = datetime.now().strftime('%A')
        [events.append(event) for event in self.get_events(jour_semaine)]
        date_mois = datetime.now().strftime('%d/%m')
        [events.append(event) for event in self.get_events(date_mois)]
        date_mois_annee = datetime.now().strftime('%d/%m/%Y')
        [events.append(event) for event in self.get_events(date_mois_annee)]
        return events


class Config(BaseModel):
    """
    Modele de la table config
    """
    clef = peewee.CharField(unique=True)
    valeur = peewee.CharField()

    def get_all(self):
        configs = {}
        for config in self.select():
            configs[self.clef] = config.valeur
        return configs

    def set(self, clef, valeur):
        conf = self.get(Config.clef == clef)
        conf.valeur = valeur
        conf.save()

    def preload(self):
        self.set('hysteresis', '0.5')
        self.set('temp_consigne_hors_gel', '10')
        self.set('temp_consigne_confort', '19.5')
        self.set('temp_consigne_eco', '17')
        self.set('uri_sonoff_tableau', '')
        self.set('sonde_file', '')
        self.set('sonde', '')
        self.set('mode', '')
        self.set('intervalle_mesure', '60')
        self.set('default_temp_consigne_eco', '17')
        self.set('default_temp_consigne_confort', '19.5')
        self.set('meteoblue', '')


class Lieu(BaseModel):
    """
    Modele de la table lieu
    """
    name = peewee.CharField(unique=True)
    description = peewee.CharField()


class Status(BaseModel):
    """
    Modele de la table status
    """
    clef = peewee.CharField(unique=True)
    valeur = peewee.CharField()

    def set(self, clef, valeur):
        status = self.get(Status.clef == clef)
        status.valeur = valeur
        status.save()

    def preload(self):
        self.set('status_chauffage', 'OFF')
        self.set('marche_forcee', 'False')
        self.set('confort_level', '')
        self.set('hors_gel', '')
        self.set('message', '')
        self.set('sonoff_1', '')
        self.set('marche_forcee_remaining', '0')
        self.set('status_programme', 'default')
        self.set('status_programme_default', '')
        self.set('status_confort_level', '')


class Temperature(BaseModel):
    """
    modele de la table temperature
    """
    lieu = peewee.ForeignKeyField(Lieu)
    date_mesure = peewee.DateTimeField()
    mesure = peewee.FloatField()
    mode_confort = peewee.CharField()
    chauffage_status = peewee.CharField()

    def get_last(self, lieu):
        last = self.select().join(Lieu).where(Lieu.name == lieu).order_by(-Temperature.date_mesure).limit(1)
        if last.count() != 0:
            return last.get().mesure
        else:
            return 'N/A'
        return last


class Horaires_confort(BaseModel):
    """
    modele de la table horaires_confort
    """
    mode = peewee.TextField()
    debut = peewee.TimeField()
    fin = peewee.TimeField()

    def is_confort(self, now, mode_thermostat='global'):
        """
        are we in confort mode ?
        :param now: 
        :param mode_thermostat: 
        :return: 
        """
        confort_global = self.select(). \
            where(Horaires_confort.debut <= now). \
            where(Horaires_confort.fin >= now). \
            where(Horaires_confort.mode == mode_thermostat). \
            count()
        if mode_thermostat == 'global':
            return confort_global
        else:
            confort = False
            return confort
