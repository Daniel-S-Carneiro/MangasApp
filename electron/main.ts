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
import * as fs from "fs";

process.env["ELECTRON_DISABLE_SECURITY_WARNINGS"] = "true";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const isDev = !app.isPackaged;
const ENABLE_DEBUG_LOGS = false;

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
    width: 1200,
    height: 800,
    show: false,
    title: "Gerenciador de Mangás",
    icon: path.join(__dirname, "../frontend/public/icon/manga.ico"),
    webPreferences: {
      preload: path.join(__dirname, "preload.cjs"),
      contextIsolation: true,
      nodeIntegration: false,
      webSecurity: false,
    },
  });

  win.maximize();

  ipcMain.handle("open-link", async (_event, url: string) => {
    shell.openExternal(url);
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

  win.webContents.on("did-finish-load", () => {
    if (ENABLE_DEBUG_LOGS) {
      // exemplo simples
      win.webContents.send("log", "teste");

      // agora envia os logs de listarCapas para o renderer
      const imgDir = path.join(
        process.resourcesPath,
        "frontend",
        "public",
        "img",
      );
      try {
        const files = fs.readdirSync(imgDir);
        win.webContents.send("log", "Arquivos de capa encontrados no build:");
        files.forEach((f) => {
          win.webContents.send("log", " - " + f);
        });
      } catch (err) {
        if (err instanceof Error) {
          win.webContents.send("log", "Erro ao listar imagens: " + err.message);
        } else {
          win.webContents.send("log", "Erro desconhecido ao listar imagens");
        }
      }
    }
  });
}

// HANDLERS IPC PARA PYTHON
ipcMain.handle(
  "python:query",
  async (_event: IpcMainInvokeEvent, payload: any): Promise<string> => {
    return new Promise((resolve, reject) => {
      const pythonPath = isDev
        ? "python"
        : path.join(process.resourcesPath, "backend", "app.exe");

      const args = isDev ? [path.join(process.cwd(), "backend", "app.py")] : [];

      const py = spawn(pythonPath, args);

      let data = "";
      let errorData = "";

      py.stdout.on("data", (chunk) => {
        const text = chunk.toString();
        data += text;
      });

      py.stderr.on("data", (chunk) => {
        errorData += chunk.toString();
        console.error("ERRO NO PYTHON:", chunk.toString());
      });

      py.stdin.write(JSON.stringify(payload));
      py.stdin.end();

      py.on("close", (code) => {
        if (code === 0) {
          resolve(data.trim() || "[]");
        } else {
          reject(`Erro no Backend (Código ${code}): ${errorData}`);
        }
      });

      py.on("error", (err) => {
        reject(`Falha ao iniciar processo Python: ${err.message}`);
      });
    });
  },
);

ipcMain.handle("dialog:openFile", async () => {
  const { canceled, filePaths } = await dialog.showOpenDialog({
    properties: ["openFile"],
    filters: [{ name: "Imagens", extensions: ["jpg", "png", "jpeg", "webp"] }],
  });
  return canceled ? null : filePaths[0];
});

app.whenReady().then(() => {
  protocol.registerFileProtocol("capas", (request, callback) => {
    const url = decodeURIComponent(
      request.url.replace(/^capas:\/\//, "").replace(/\/$/, ""),
    );

    const pathCapa = path.join(
      isDev ? process.cwd() : process.resourcesPath,
      "frontend",
      "public",
      "img",
      url,
    );

    callback({ path: path.normalize(pathCapa) });
  });

  createWindow();
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") app.quit();
});
