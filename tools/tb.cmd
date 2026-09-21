@echo off
REM Copyright 2026 Doug Trier
REM
REM Licensed under the Apache License, Version 2.0 (the "License");
REM you may not use this file except in compliance with the License.
REM You may obtain a copy of the License at
REM
REM     https://www.apache.org/licenses/LICENSE-2.0
REM
REM Unless required by applicable law or agreed to in writing, software
REM distributed under the License is distributed on an "AS IS" BASIS,
REM WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
REM See the License for the specific language governing permissions and
REM limitations under the License.
REM
REM tb.cmd - Windows entry point for the Trier Bridge read-only tools.
REM Usage: tools\tb context
setlocal
set "TB_DIR=%~dp0"
where python >nul 2>nul
if errorlevel 1 (
  echo tb: python 3.12+ not found on PATH
  exit /b 2
)
python "%TB_DIR%tb.py" %*
exit /b %ERRORLEVEL%
