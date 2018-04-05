#!/usr/bin/env python
# -*- coding: utf-8 -*-

#import arrow
#from daemonize import Daemonize
from models import Temperature, Config, Status, Horaires_confort
#import urllib2
#import requests
import time
from ds1820 import DS1820
import json
import sys
import os
import logging
from logging.handlers import RotatingFileHandler
import argparse
#import Config

import configparser


def set_chauffage(temperature_consigne):
    """
    decide if heating in on/off
    :param temperature_consigne: 
    :return: 
    """
    temperature_courante = Temperature().get_last('sejour')
    hysteresis = float(Config().get(Config.clef == 'hysteresis').valeur)
    status = Status.get(Status.clef == 'status_chauffage')
    cons_min = temperature_consigne - hysteresis
    cons_max = temperature_consigne + hysteresis
    logger.info("Temp : " + str(temperature_courante))
    logger.info("Consigne mini: " + str(cons_min))
    logger.info("Consigne maxi: " + str(cons_max))
    if temperature_courante <= cons_min:
        chauffage = 'ON'
        logger.info('Temp inf a mini => ON')
    elif temperature_courante > cons_max:
        chauffage = 'OFF'
        logger.info('Temp sup a maxi => OFF')
    else:
        if status == 'ON':
            chauffage = 'ON'
            logger.info("Temp intermédiaire et On => ON")
        else:
            chauffage = 'OFF'
            logger.info("Temp intermédiaire et Off => OFF")

    return chauffage


def thermostat():
    """
    describe the thermostat rules
    :return: 
    """
    if Status().get(Status.clef == 'marche_forcee').valeur == 'True':
        Status().set('confort_level', 'FORCEE')
        chauffage = 'ON'
        logger.info('Set marche forcée')
    elif Status().get(Status.clef == 'hors_gel').valeur == 'True':
        Status().set('confort_level', 'HORS GEL')
        temperature_consigne = float(Config().get(Config.clef == 'temp_consigne_hors_gel').valeur)
        chauffage = set_chauffage(temperature_consigne)
        logger.info('Set hors gel')
    else:
        is_confort_mode = Horaires_confort().is_confort(arrow.now('Europe/Paris').time())
        if is_confort_mode == 1:
            temperature_consigne = float(Config().get(Config.clef == 'temp_consigne_confort').valeur)
            Status().set('confort_level', 'CONF')
            logger.info('Set mode confort')
        else:
            temperature_consigne = float(Config().get(Config.clef == 'temp_consigne_eco').valeur)
            Status().set('confort_level', 'ECO')
            logger.info('Set mode éco')
        chauffage = set_chauffage(temperature_consigne)
    try:
        uri_sonoff = Config().get(Config.clef == 'uri_sonoff_tableau').valeur
        r = requests.get(uri_sonoff + 'cm?cmnd=Power')
        Status().set('status_chauffage', json.loads(r.text)['POWER'])
        Status().set('message', '-')
    except requests.exceptions.ConnectionError:
        logger.warning('Sonoff connection error on read')
        Status().set('message', 'Erreur envoi')
    return chauffage


def send_command(chauffage, dry_run):
    """
    send on/off command to sonoff
    :param chauffage: 
    :return: 
    """
    uri_sonoff = Config().get(Config.clef == 'uri_sonoff_tableau').valeur
    if chauffage == 'ON':
        logger.info("On allume les radiateurs")
        try:
            if not dry_run:
                requests.get(uri_sonoff + 'cm?cmnd=Power%20On')
            Status().set('sonoff_1', 'ON')
        except requests.exceptions.ConnectionError:
            logger.error('cannot reach relay for power on')
            Status().set('message', 'Erreur envoi')
    if chauffage == 'OFF':
        logger.info("On coupe les radiateurs")
        try:
            if not dry_run:
                requests.get(uri_sonoff + 'cm?cmnd=Power%20Off')
            Status().set('sonoff_1', 'OFF')
            Status().set('message', '-')
        except requests.exceptions.ConnectionError:
            logger.error('cannot reach relay for power off')
            Status().set('message', 'Erreur envoi')


def thermometre(sonde):
    """
    Lit la  valeur sur la sonde
    :param sonde: 
    :return: 
    """
    sonde_1_file = Config().get(Config.clef == 'sonde_file').valeur+'/'+Config().get(Config.clef == sonde).valeur
    if os.path(sonde_1_file):
        sonde_1 = DS1820.read_temp(sonde_1_file)
        if sonde_1 is not None:
            temp = Temperature(lieu=1, date_mesure=arrow.now('Europe/Paris').datetime, mesure=sonde_1)
            logger.info(str(sonde_1) + "°C")
            return temp
    else:
        logger.error('Cannot read temp')
    return 0


def get_temperature_consigne():
    """
    get the target temperature
    :return: 
    """
    mode_thermostat = Config().get(Config.clef == 'mode').valeur
    mode_confort = Horaires_confort().is_confort(arrow.now('Europe/Paris').time(), mode_thermostat)
    if mode_confort:
        temp = Config().get(Config.clef == 'temp_consigne_confort').valeur
    else:
        temp = Config().get(Config.clef == 'temp_consigne_eco').valeur
    if Status().get(Status.clef == 'marche_forcee').valeur == 'True':
        temp = 25.0
    if Status().get(Status.clef == 'hors_gel').valeur == 'True':
        temp = Config().get(Config.clef == 'temp_consigne_hors_gel').valeur
    return temp


def main(dry_run):
    while True:
        intervalle_mesure = int(Config().get(Config.clef == 'intervalle_mesure').valeur)
        temp = thermometre(sonde='sonde_1')
        chauffage = thermostat()
        temp.chauffage_status = chauffage
        temp.mode_confort = get_temperature_consigne()
        send_command(chauffage, dry_run)
        temp.save()
        time.sleep(intervalle_mesure)


def get_logger():
    """

    :return:
    """
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(asctime)s :: %(levelname)s :: %(message)s')
    file_handler = RotatingFileHandler('/tmp/thermostat.log', 'a', 1000000, 1)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.DEBUG)
    logger.addHandler(stream_handler)

    return logger


if __name__ == '__main__':
    logger = get_logger()
    parser = argparse.ArgumentParser(description='Thermostat')
    parser.add_argument('-d', help='deamonize', action='store_true')
    parser.add_argument('-f', help='dry run', action='store_true')
    args = parser.parse_args()
    must_deamonize = args.d
    dry_run = args.f

    os.system('cd /usr/local/bin/thermostat')
    if os.path.isfile('/tmp/thermostat.pid'):
        logger.info("Process already running")
        sys.exit(0)
    else:
        if must_deamonize:
            pid = '/tmp/thermostat.pid'
            daemon = Daemonize(app='thermostat', pid=pid, action=thermostat)
            daemon.start()
            logger.info("deamon started")
        else:
            logger.info('without deamon')
    main(dry_run)
