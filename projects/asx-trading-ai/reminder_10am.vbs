Set objShell = CreateObject("WScript.Shell")
objShell.Popup "ASX TRADING TEST REMINDER" & vbCrLf & vbCrLf & _
              "It's 10:00 AM - Time to start the half-day test!" & vbCrLf & vbCrLf & _
              "Action:" & vbCrLf & _
              "1. Go to: C:\Users\riord\asx-trading-ai" & vbCrLf & _
              "2. Double-click: start_halfday_test.bat" & vbCrLf & _
              "3. Let it run until 2:30 PM" & vbCrLf & vbCrLf & _
              "Press OK to open the folder now", _
              0, "ASX Trading Reminder", 64

' Open the folder
objShell.Run "explorer.exe C:\Users\riord\asx-trading-ai"
