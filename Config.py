# -*- coding: utf-8 -*-


class Config:
    def __init__(self):
        self.available_pin = self.get_available_pins()
        self.conf = self.set_consignes()
        self.sondes = self.set_sondes()
        self.sonde_file = "/sys/bus/w1/devices/"
        self.data_dir = "/home/pi/thermostat/thermostat_txt/data/"
        self.intervalle_mesures = 5  # en secondes
        self.jour_poubelles_noire = ''
        self.txt_poubelle_noire = 'Sortir la poubelle noire'
        self.jour_poubelles_jaunes = ''
        self.txt_poubelle_verte = 'Sortir la poubelle jaune'
        self.jour_dechet_vert = []
        self.jour_dechet_vert.append("15/02/2017")
        self.jour_dechet_vert.append("25/02/2017")
        self.txt_dechet_vert = "Sortir déchets verts"

    def set_consignes(self):
        """
        Configuration du thermostat
        :return:
        """
        conf = {}
        conf['mode'] = '24' # 24 - WEEKEND - HEBDO
        conf['hysteresis'] = 0.5
        conf['24'] = {}
        conf['24']['ECO'] = 18
        conf['24']['CONF'] = 21
        conf['24']['defaut'] = "ECO"
        conf['24'][1] = {}
        conf['24'][1]['debut'] = "5:30"
        conf['24'][1]['fin'] = "7:00"
        conf['24'][1]['confort_level'] = "CONF"
        conf['24'][2] = {}
        conf['24'][2]['debut'] = "7:00"
        conf['24'][2]['fin'] = "11:00"
        conf['24'][2]['confort_level'] = "ECO"
        conf['24'][3] = {}
        conf['24'][3]['debut'] = "12:00"
        conf['24'][3]['fin'] = "22:00"
        conf['24'][3]['confort_level'] = "CONF"
        return conf

    def set_sondes(self):
        """
        liste des sondes disponibles
        :return:
        """
        sondes = {}
        sondes['ext'] = "28-011561577dff"
        sondes['bureau'] = "28-0115615a35ff"
  #      sondes['sondeA'] = "28-800000270d72"
   #     sondes['sondeB'] = "28-8000002719aa"
 #       sondes['sondeC'] = "28-80000026a3d7"
 #       sondes['sondeD'] = "28-800000270c86"
  #      sondes['sondeE'] = "28-80000026aec6"
        return sondes

    def get_available_pins(self):
        pin = {}
        pin[12] = 'relai'
        pin[18] = 'db4'
        pin[22] = 'e'
        pin[23] = 'db3'
        pin[24] = 'db2'
        pin[25] = 'db1'
        pin[27] = 'rs'
        return pin

    def search_gpio_pin(self, value):
        result = [c for c, v in self.get_available_pins().items() if v == value]
        if len(result) == 0:
            return None
        elif len(result) == 1:
            return result[0]
        else:
            return result


