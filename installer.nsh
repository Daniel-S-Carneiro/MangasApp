# Força o instalador a ser renderizado de forma nítida em telas de alta resolução (Hi-DPI)
ManifestDPIAware true

!macro customUnInstall
  MessageBox MB_YESNO|MB_ICONQUESTION "Deseja apagar todos os seus dados de mangás, capas e histórico salvos neste computador?" IDNO manter_dados
  
  # --- SE O USUÁRIO CLICAR EM 'SIM' ---
  RMDir /r "$APPDATA\Gerenciador de Mangás"
  Goto fim

  # --- SE O USUÁRIO CLICAR EM 'NÃO' (LIMPEZA INTELIGENTE) ---
  manter_dados:
  # Deleta apenas as pastas de cache e lixo do Chromium/Electron
  RMDir /r "$APPDATA\Gerenciador de Mangás\Cache"
  RMDir /r "$APPDATA\Gerenciador de Mangás\Code Cache"
  RMDir /r "$APPDATA\Gerenciador de Mangás\GPUCache"
  RMDir /r "$APPDATA\Gerenciador de Mangás\DawnGraphiteCache"
  RMDir /r "$APPDATA\Gerenciador de Mangás\DawnWebGPUCache"
  RMDir /r "$APPDATA\Gerenciador de Mangás\blob_storage"
  RMDir /r "$APPDATA\Gerenciador de Mangás\Local Storage"
  RMDir /r "$APPDATA\Gerenciador de Mangás\Session Storage"
  RMDir /r "$APPDATA\Gerenciador de Mangás\Network"
  RMDir /r "$APPDATA\Gerenciador de Mangás\Shared Dictionary"
  Delete "$APPDATA\Gerenciador de Mangás\DIPS"
  Delete "$APPDATA\Gerenciador de Mangás\Local State"
  Delete "$APPDATA\Gerenciador de Mangás\Preferences"

  fim:
!macroend