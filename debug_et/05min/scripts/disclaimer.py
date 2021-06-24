#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
logger = logging.getLogger(__name__)

def print_disclaimer(with_logger = False):

    # disclaimer message
    disclaimer_message  =                                                                                                  "\n"
    disclaimer_message +=                                                                                                  "\n"
    disclaimer_message += " PCR-GLOBWB (PCRaster Global Water Balance) Global Hydrological Model                       " + "\n"
    disclaimer_message +=                                                                                                  "\n"
    disclaimer_message += " Copyright (C) 2016, Edwin H. Sutanudjaja, Rens van Beek, Niko Wanders, Yoshihide Wada,     " + "\n"
    disclaimer_message += " Joyce H. C. Bosmans, Niels Drost, Ruud J. van der Ent, Inge E. M. de Graaf, Jannis M. Hoch," + "\n"
    # ~ disclaimer_message += " Kor de Jong, Derek Karssenberg, Patricia López López, Stefanie Peßenteiner, Oliver Schmitz," + "\n"
    disclaimer_message += " Kor de Jong, Derek Karssenberg, Patricia Lopez Lopez, Stefanie Pessenteiner, Oliver Schmitz," + "\n"
    disclaimer_message += " Menno W. Straatsma, Ekkamol Vannametee, Dominik Wisser, and Marc F. P. Bierkens            " + "\n"
    disclaimer_message += " Faculty of Geosciences, Utrecht University, Utrecht, The Netherlands                       " + "\n"
    disclaimer_message +=                                                                                                  "\n"
    disclaimer_message += " This program comes with ABSOLUTELY NO WARRANTY                                             " + "\n"
    disclaimer_message += " This is free software, and you are welcome to redistribute it under certain conditions     " + "\n"
    disclaimer_message += " See the LICENSE file for more details                                                      " + "\n"
    disclaimer_message +=                                                                                                  "\n"
    
    # print disclaimer
    if with_logger:
        logger.info(disclaimer_message)
    else:
        print(disclaimer_message)
