#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This script has been disabled because it was causing data inconsistencies
by keeping multiple database tables in sync. The system now uses only
the 'scores' and 'players' tables, not the legacy 'score' table.
"""

import logging
logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(levelname)s - %(message)s')

if __name__ == "__main__":
    logging.warning("This script has been disabled to prevent database inconsistencies.")
    logging.warning("The system now uses only the 'scores' and 'players' tables.")
    exit(1)
