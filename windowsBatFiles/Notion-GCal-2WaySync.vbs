Set WshShell = CreateObject("WScript.Shell" ) 
WshShell.Run chr(34) & "FULL_PATH_TO_BAT_FILE_HERE" & Chr(34), 0 
Set WshShell = Nothing 