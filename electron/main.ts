import {
  app,
  BrowserWindow,
  ipcMain,
  protocol,
  dialog,
  shell,
  type IpcMainInvokeEvent,
} from "electron";
import * as path from "path";
import { spawn } from "child_process";
import { fileURLToPath } from "url";

process.env["ELECTRON_DISABLE_SECURITY_WARNINGS"] = "true";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const isDev = !app.isPackaged;

protocol.registerSchemesAsPrivileged([
  {
    scheme: "file",
    privileges: {
      standard: true,
      secure: true,
      allowServiceWorkers: true,
      supportFetchAPI: true,
      corsEnabled: true,
      stream: true,
    },
  },
  {
    scheme: "capas",
    privileges: {
      standard: true,
      secure: true,
      supportFetchAPI: true,
      corsEnabled: true,
    },
  },
]);

function createWindow(): void {
  const win = new BrowserWindow({
    width: 1000,
    height: 700,
    show: false,
    title: "Gerenciador de Mangás",
    icon: path.join(__dirname, "../frontend/public/icon/manga.ico"),
    webPreferences: {
      preload: path.join(__dirname, "preload.cjs"),
      contextIsolation: true,
      nodeIntegration: false,
      webSecurity: false,
      sandbox: false,
    },
  });

  win.maximize();

  win.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: "deny" };
  });

  if (isDev) {
    win.loadURL("http://localhost:5173");
  } else {
    const indexPath = path.join(
      app.getAppPath(),
      "frontend",
      "dist",
      "index.html",
    );
    win.loadFile(indexPath).catch(() => {
      win.loadFile(path.join(app.getAppPath(), "dist", "index.html"));
    });
  }

  win.on("page-title-updated", (e) => e.preventDefault());
  win.once("ready-to-show", () => win.show());
}

// HANDLERS IPC
ipcMain.handle("dialog:openFile", async () => {
  const { canceled, filePaths } = await dialog.showOpenDialog({
    properties: ["openFile"],
    filters: [{ name: "Imagens", extensions: ["jpg", "png", "jpeg", "webp"] }],
  });
  return canceled ? null : filePaths[0];
});

ipcMain.handle(
  "python:query",
  async (_event: IpcMainInvokeEvent, payload: any): Promise<string> => {
    return new Promise((resolve, reject) => {
      const pythonScriptPath = isDev
        ? path.join(process.cwd(), "backend", "app.py")
        : path.join(process.resourcesPath, "backend", "app.py");

      const py = spawn("python", [pythonScriptPath, JSON.stringify(payload)], {
        cwd: isDev ? process.cwd() : process.resourcesPath,
        shell: false,
      });

      let data = "";
      let errorData = "";

      py.stdout.on("data", (chunk) => (data += chunk.toString()));
      py.stderr.on("data", (chunk) => (errorData += chunk.toString()));

      py.on("close", (code) => {
        if (code === 0) resolve(data);
        else reject(`Erro Python (${code}): ${errorData}`);
      });
    });
  },
);

app.whenReady().then(() => {
  // Protocolo para carregar as capas direto da pasta do projeto
  protocol.registerFileProtocol("capas", (request, callback) => {
    const url = decodeURIComponent(
      request.url.replace(/^capas:\/\//, "").replace(/\/$/, ""),
    );

    // Constrói o caminho dinâmico baseado no ambiente
    const pathCapa = path.join(
      isDev ? process.cwd() : process.resourcesPath,
      "frontend",
      "public",
      "img",
      decodeURIComponent(url),
    );

    callback({ path: path.normalize(pathCapa) });
  });

  createWindow();
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") app.quit();
});
