const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("api", {
  callPython: (data) => ipcRenderer.invoke("python:query", data),
});
