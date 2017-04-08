@echo off
:: Copyright (c) 2013 The Chromium Authors. All rights reserved.
:: Use of this source code is governed by a BSD-style license that can be
:: found in the LICENSE file.

python "%~dp0/../../main_host.py" %*
:: When combined, this should be...
:: python "%~dp0/../main.py" %*
:: this file will be in /Scripts
:: FukurouViewer
::     /Scripts
::     /FukurouViewer
::         program.py
::         threads.py, etc.