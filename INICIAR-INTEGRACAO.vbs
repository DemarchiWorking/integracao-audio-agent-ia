' ============================================================
'  INICIAR-INTEGRACAO.vbs
'  DataDev Demarchi Lab - duplo clique, sem janela preta
'  Inicia o pipeline completo em background.
' ============================================================

Dim shell, scriptDir, psFile, cmd
Set shell = CreateObject("WScript.Shell")

' Diretorio deste arquivo
scriptDir = Left(WScript.ScriptFullName, InStrRev(WScript.ScriptFullName, "\"))

' Garantir npm no PATH (para claude CLI)
Dim npmBin
npmBin = shell.ExpandEnvironmentStrings("%APPDATA%") & "\npm"

' Carregar ANTHROPIC_API_KEY do .env antes de passar para o PS
Dim envFile, apiKey
envFile = scriptDir & ".env"
apiKey  = ""

If CreateObject("Scripting.FileSystemObject").FileExists(envFile) Then
    Dim fso, ts, line, parts
    Set fso = CreateObject("Scripting.FileSystemObject")
    Set ts  = fso.OpenTextFile(envFile, 1, False) ' 1 = ForReading
    Do While Not ts.AtEndOfStream
        line = Trim(ts.ReadLine())
        If Left(line, 1) <> "#" And InStr(line, "=") > 0 Then
            parts = Split(line, "=", 2)
            If LCase(Trim(parts(0))) = "anthropic_api_key" Then
                apiKey = Trim(parts(1))
            End If
        End If
    Loop
    ts.Close
End If

' Montar comando PowerShell em modo oculto
psFile = scriptDir & "start-integracao.ps1"

If apiKey <> "" And apiKey <> "sk-ant-COLE-SUA-CHAVE-AQUI" Then
    ' Passa a API key como variavel de ambiente para o processo PowerShell
    cmd = "powershell -ExecutionPolicy Bypass -WindowStyle Hidden -Command " & _
          """$env:ANTHROPIC_API_KEY='" & apiKey & "'; " & _
          "& '" & psFile & "'"""
Else
    cmd = "powershell -ExecutionPolicy Bypass -WindowStyle Hidden -File """ & psFile & """"
End If

' Executar em background (0 = oculto, False = nao aguardar)
shell.Run cmd, 0, False

' Notificacao imediata de que o processo foi iniciado
WScript.Sleep 2000

' Verificar se a API subiu na porta 8765
Dim http, status
On Error Resume Next
Set http = CreateObject("MSXML2.XMLHTTP")
http.Open "GET", "http://localhost:8765/health", False
http.Send
status = http.Status
On Error GoTo 0

' Aguardar ate 30s para a API ficar pronta
Dim attempts
attempts = 0
Do While status <> 200 And attempts < 15
    WScript.Sleep 2000
    On Error Resume Next
    http.Open "GET", "http://localhost:8765/health", False
    http.Send
    status = http.Status
    On Error GoTo 0
    attempts = attempts + 1
Loop

' Notificacao via balao do Windows
Dim notify
Set notify = CreateObject("WScript.Shell")

If status = 200 Then
    ' Balloon tip: pipeline pronto
    notify.RegWrite "HKCU\Software\DataDevLab\LastStart", Now(), "REG_SZ"
    ShowBalloon "DataDev Lab — Pipeline ATIVO", _
                "API pronta | Whisper | Claude Pro | KDE Connect aguardando audio do S10", _
                64 ' 64 = icone de informacao
Else
    ShowBalloon "DataDev Lab — Verifique", _
                "Pipeline iniciado mas API nao respondeu. Abra INICIAR-INTEGRACAO.bat para detalhes.", _
                48 ' 48 = icone de aviso
End If

Sub ShowBalloon(title, msg, icon)
    ' Usa PowerShell para exibir balao de notificacao na bandeja do sistema
    Dim ps
    ps = "powershell -WindowStyle Hidden -Command """ & _
         "[System.Reflection.Assembly]::LoadWithPartialName('System.Windows.Forms') | Out-Null;" & _
         "$n = New-Object System.Windows.Forms.NotifyIcon;" & _
         "$n.Icon = [System.Drawing.SystemIcons]::Application;" & _
         "$n.Visible = `$true;" & _
         "$n.ShowBalloonTip(6000, '" & Replace(title, "'", "") & "', '" & Replace(msg, "'", "") & "', " & icon & ");" & _
         "Start-Sleep 7;" & _
         "$n.Dispose()"""
    shell.Run ps, 0, False
End Sub
