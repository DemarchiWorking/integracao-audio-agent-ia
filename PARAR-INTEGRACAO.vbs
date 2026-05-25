' ============================================================
'  PARAR-INTEGRACAO.vbs
'  DataDev Demarchi Lab - duplo clique, sem janela preta
'  Para todos os servicos do pipeline em background.
' ============================================================

Dim shell, scriptDir, psFile, cmd
Set shell = CreateObject("WScript.Shell")

scriptDir = Left(WScript.ScriptFullName, InStrRev(WScript.ScriptFullName, "\"))
psFile = scriptDir & "stop-integracao.ps1"

cmd = "powershell -ExecutionPolicy Bypass -WindowStyle Hidden -File """ & psFile & """"
shell.Run cmd, 0, True  ' True = aguardar terminar antes de notificar

' Notificacao de encerramento
Dim ps
ps = "powershell -WindowStyle Hidden -Command """ & _
     "[System.Reflection.Assembly]::LoadWithPartialName('System.Windows.Forms') | Out-Null;" & _
     "$n = New-Object System.Windows.Forms.NotifyIcon;" & _
     "$n.Icon = [System.Drawing.SystemIcons]::Application;" & _
     "$n.Visible = `$true;" & _
     "$n.ShowBalloonTip(5000, 'DataDev Lab — Pipeline PARADO', 'API, Watchers e inbox encerrados com seguranca.', 64);" & _
     "Start-Sleep 6;" & _
     "$n.Dispose()"""
shell.Run ps, 0, False
