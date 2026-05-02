const { contextBridge, ipcRenderer, shell } = require("electron");

contextBridge.exposeInMainWorld("api", {
  callPython: (data) => ipcRenderer.invoke("python:query", data),
  selecionarArquivo: () => ipcRenderer.invoke("dialog:openFile"),
  // O shell PRECISA estar aqui para o link abrir no navegador externo
  openLink: (url) => shell.openExternal(url),
});
