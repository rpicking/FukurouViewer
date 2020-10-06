@echo off
:: Copyright (c) 2013 The Chromium Authors. All rights reserved.
:: Use of this source code is governed by a BSD-style license that can be
:: found in the LICENSE file.

call %~dp0/../venv/Scripts/activate.bat
python "%~dp0/../main.py" -d%*
call %~dp0/../venv/Scripts/deactivate.bat
