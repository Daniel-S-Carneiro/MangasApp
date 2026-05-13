const { contextBridge, ipcRenderer, shell } = require("electron");

contextBridge.exposeInMainWorld("api", {
  callPython: (data) => ipcRenderer.invoke("python:query", data),
  selecionarArquivo: () => ipcRenderer.invoke("dialog:openFile"),
  openLink: (url) => ipcRenderer.invoke("open-link", url),

  onLog: (callback) =>
    ipcRenderer.on("log", (_event, message) => callback(message)),
});
