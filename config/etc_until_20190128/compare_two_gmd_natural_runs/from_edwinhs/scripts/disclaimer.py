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
    disclaimer_message += " Copyright (C) 2016, Ludovicus P. H. (Rens) van Beek, Edwin H. Sutanudjaja, Yoshihide Wada, " + "\n"
    disclaimer_message += " Joyce H. C. Bosmans, Niels Drost, Inge E. M. de Graaf, Kor de Jong, Patricia Lopez Lopez,  " + "\n" 
    disclaimer_message += " Stefanie Pessenteiner, Oliver Schmitz, Menno W. Straatsma, Niko Wanders, Dominik Wisser,   " + "\n"
    disclaimer_message += " and Marc F. P. Bierkens,                                                                   " + "\n"
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
