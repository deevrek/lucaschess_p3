#!/usr/bin/python
# -*- coding: utf-8 -*-

# ==============================================================================
# Author : Lucas Monge, lukasmonk@gmail.com
# Web : http://lucaschess.pythonanywhere.com/
# Blog : http://lucaschess.blogspot.com
# Licence : GPL
# ==============================================================================


























import os
import sip
from imp import reload
import sys

EXCEPTION_HOOK = True

if EXCEPTION_HOOK:
    sys._excepthook = sys.excepthook

    def my_exception_hook(exctype, value, tb):
        # Print the error and traceback
        print(exctype, value, tb)
        # import traceback
        # traceback.print_tb(tb)

        # Call the normal Exception hook after
        sys._excepthook(exctype, value, tb)
        sys.exit(1)

    sys.excepthook = my_exception_hook

# reload(sys)
# sys.setdefaultencoding("latin-1")
sys.path.insert(0, os.curdir)

sip.setapi('QDate', 2)
sip.setapi('QDateTime', 2)
sip.setapi('QString', 2)
sip.setapi('QTextStream', 2)
sip.setapi('QTime', 2)
sip.setapi('QUrl', 2)
sip.setapi('QVariant', 2)

current_dir = os.path.dirname(sys.argv[0])
if current_dir:
    os.chdir(current_dir)

from Code import VarGen

sys.path.append(os.path.join(current_dir, "Code"))
sys.path.append(os.path.join(current_dir, VarGen.folder_engines, "_tools"))
import Code.Traducir as Traducir
Traducir.install()

nArgs = len(sys.argv)
if nArgs == 1:
    import Code.Init

    Code.Init.init()

elif nArgs >= 2:
    print("lucas argv[1] " + sys.argv[1])
    arg = sys.argv[1].lower()
    if (arg.endswith(".pgn") or arg.endswith(".pks") or
            arg.endswith(".lcg") or arg.endswith(".lcf") or
            arg == "-play" or arg.endswith(".bmt")):
        import Code.Init
        Code.Init.init()

    elif arg == "-kibitzer":
        import Code.RunKibitzer
        Code.RunKibitzer.run(sys.argv[2])

