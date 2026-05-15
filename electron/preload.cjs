const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("api", {
  callPython: (data) => ipcRenderer.invoke("python:query", data),
  selecionarArquivo: () => ipcRenderer.invoke("dialog:openFile"),
  openLink: (url) => ipcRenderer.invoke("open-link", url),
  getCapaBase64: (url) => ipcRenderer.invoke("get-capa-base64", url),
  onAlertLink: (callback) =>
    ipcRenderer.on("alert-link", (_event, mensagem) => callback(mensagem)),
  onLog: (callback) =>
    ipcRenderer.on("log", (_event, message) => callback(message)),
});
