# -*- coding: utf-8 -*-

#	SAGA Modules plugin for Quantum GIS
#
#	blacklist.py (C) Camilo Polymeris
#	
#   This program is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation; either version 2 of the License, or
#   (at your option) any later version.
# 
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#       
#   You should have received a copy of the GNU General Public License
#   along with this program; if not, write to the Free Software
#   Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#   MA 02110-1301, USA.

""" List of library names not to be loaded.
A partial name will suffice.
"""
libraryBlacklist = []

""" List of full module names not to be loaded. """
moduleBlacklist = []

""" List of full tag strings not to be displayed. """
tagBlacklist = ["introducing module programming", "lectures"]


def libraryIsBlackListed(l):
    for bl in libraryBlacklist:
        if l in bl:
            return True

moduleIsBlackListed = lambda m: m in moduleBlacklist
tagIsBlackListed = lambda t: t in tagBlacklist
