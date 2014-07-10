# -*- coding: utf-8 -*-

"""
Application main launcher.
"""
__version__ = "$Id: tovian_gui_debug_db.py 65 2013-08-16 12:35:43Z campr $"

import tovian_gui

if __name__ == "__main__":
    tovian_gui.check_requirements()
    tovian_gui.start('debug_db')