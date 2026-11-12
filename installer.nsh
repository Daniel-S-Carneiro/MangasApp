# Força o instalador a ser renderizado de forma nítida em telas de alta resolução (Hi-DPI)
ManifestDPIAware true

!macro customUnInstall
  MessageBox MB_YESNO|MB_ICONQUESTION "Deseja apagar todos os seus dados de Mangas, capas e histórico salvos neste computador?" IDNO manter_dados
  
  # --- SE O USUÁRIO CLICAR EM 'SIM' ---
  RMDir /r "$APPDATA\Gerenciador de Mangas"
  Goto fim

  # --- SE O USUÁRIO CLICAR EM 'NÃO' (LIMPEZA INTELIGENTE) ---
  manter_dados:
  # Deleta apenas as pastas de cache e lixo do Chromium/Electron
  RMDir /r "$APPDATA\Gerenciador de Mangas\Cache"
  RMDir /r "$APPDATA\Gerenciador de Mangas\Code Cache"
  RMDir /r "$APPDATA\Gerenciador de Mangas\GPUCache"
  RMDir /r "$APPDATA\Gerenciador de Mangas\DawnGraphiteCache"
  RMDir /r "$APPDATA\Gerenciador de Mangas\DawnWebGPUCache"
  RMDir /r "$APPDATA\Gerenciador de Mangas\blob_storage"
  RMDir /r "$APPDATA\Gerenciador de Mangas\Local Storage"
  RMDir /r "$APPDATA\Gerenciador de Mangas\Session Storage"
  RMDir /r "$APPDATA\Gerenciador de Mangas\Network"
  RMDir /r "$APPDATA\Gerenciador de Mangas\Shared Dictionary"
  Delete "$APPDATA\Gerenciador de Mangas\DIPS"
  Delete "$APPDATA\Gerenciador de Mangas\Local State"
  Delete "$APPDATA\Gerenciador de Mangas\Preferences"

  fim:
!macroend