REM @echo off

REM if "%2" == "" goto create

REM cd %2

REM create:

REM cd bin\script

call %2\setup.bat

call %2\bin\windows\perl\bin\perl %2\bin\script\mkcol.pl -creator me@myaddress.is.fake %1

:End