REM @echo off

REM if "%2" == "" goto runscript

REM cd %2

REM runscript:

REM cd bin\script

call %2\setup.bat

call %2\bin\windows\perl\bin\perl %2\bin\script\import.pl %1

call %2\bin\windows\perl\bin\perl %2\bin\script\buildcol.pl %1

xcopy /s /y %2\collect\%1\building %2\collect\%1\index

call %2\bin\windows\perl\bin\perl %2\bin\script\exportcol.pl %1

:End

