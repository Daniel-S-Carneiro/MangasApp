const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("api", {
  // Comunicação com o backend Python Sidecar
  callPython: (data) => ipcRenderer.invoke("python:query", data),

  // Utilitários nativos do Electron
  selecionarArquivo: () => ipcRenderer.invoke("dialog:openFile"),
  openLink: (url) => ipcRenderer.invoke("open-link", url),

  // Listeners de Eventos (com retorno para remoção do listener no Vue)
  onAlertLink: (callback) => {
    const listener = (_event, mensagem) => callback(mensagem);
    ipcRenderer.on("alert-link", listener);
    return () => ipcRenderer.removeListener("alert-link", listener);
  },

  onLog: (callback) => {
    const listener = (_event, message) => callback(message);
    ipcRenderer.on("log", listener);
    return () => ipcRenderer.removeListener("log", listener);
  },
});
