#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Application main launcher.
"""

import tovian_gui

if __name__ == "__main__":
    tovian_gui.check_requirements()
    tovian_gui.start('debug')