import {
  app,
  BrowserWindow,
  ipcMain,
  protocol,
  dialog,
  shell,
  type IpcMainInvokeEvent,
} from "electron";

import { spawn } from "child_process";
import { fileURLToPath } from "url";
import { promises as fs } from "fs";
import path from "path";

process.env["ELECTRON_DISABLE_SECURITY_WARNINGS"] = "false";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const isDev = !app.isPackaged;
const ENABLE_PROD_DEBUG = process.env.DEBUG_PROD === "true";
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
]);

function createWindow(): void {
  const win = new BrowserWindow({
    width: 1200,
    height: 800,
    show: false,
    title: "Gerenciador de Mangás",
    icon: path.join(
      process.resourcesPath,
      "frontend",
      "public",
      "icon",
      "manga.ico",
    ),
    webPreferences: {
      preload: path.join(__dirname, "preload.cjs"),
      contextIsolation: true,
      nodeIntegration: false,
      webSecurity: true,
    },
  });

  win.maximize();

  //  Controle de menu e DevTools
  if (isDev || ENABLE_PROD_DEBUG) {
    // Em dev ou se DEBUG_PROD=true → mantém menu e DevTools
    win.webContents.openDevTools({ mode: "detach" });
  } else {
    // Em produção normal → remove menu e bloqueia DevTools
    win.removeMenu();
    win.webContents.on("devtools-opened", () => {
      win.webContents.closeDevTools();
    });
  }

  ipcMain.handle("open-link", async (_event, url: string) => {
    try {
      const parsed = new URL(url);
      if (parsed.protocol !== "http:" && parsed.protocol !== "https:") {
        console.warn("Tentativa de abrir protocolo inválido:", url);
        return;
      }
      shell.openExternal(url);
    } catch {
      _event.sender.send("alert-link", "URL inválida recebida: " + url);
      console.log("DEBUG main.ts → enviando alert-link:", url);
    }
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

  win.webContents.on("did-finish-load", async () => {
    if (ENABLE_DEBUG_LOGS) {
      win.webContents.send("log", "teste");
      win.webContents.send(
        "log",
        "process.resourcesPath → " + process.resourcesPath,
      );
      win.webContents.send(
        "log",
        "app.getPath('userData') → " + app.getPath("userData"),
      );
      win.webContents.send("log", "app.getAppPath() → " + app.getAppPath());

      // Testa leitura da pasta de imagens no build
      const imgDir = path.join(
        app.getPath("userData"), // aqui você vê o que está em %APPDATA%
        "frontend",
        "public",
        "img",
      );
      try {
        const files = await fs.readdir(imgDir);
        win.webContents.send(
          "log",
          "Arquivos de capa encontrados em userData:",
        );
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
        : path.join(process.resourcesPath, "backend", "app", "app.exe");

      const args = isDev ? [path.join(process.cwd(), "backend", "app.py")] : [];

      const py = spawn(pythonPath, args);

      // Usamos arrays de Buffers em vez de strings vazias para evitar corrupção de caracteres UTF-8
      const stdoutChunks: Buffer[] = [];
      const stderrChunks: Buffer[] = [];

      py.stdout.on("data", (chunk: Buffer) => {
        stdoutChunks.push(chunk);
      });

      py.stderr.on("data", (chunk: Buffer) => {
        stderrChunks.push(chunk);
        // O log imediato pode continuar como string para debug
        console.error("ERRO NO PYTHON (Parcial):", chunk.toString());
      });

      // Envia o payload para o stdin do Python
      py.stdin.write(JSON.stringify(payload));
      py.stdin.end();

      py.on("close", (code) => {
        // Ao fechar, concatenamos todos os pedaços e convertemos para string de uma vez só
        const dataFinal = Buffer.concat(stdoutChunks).toString("utf-8");
        const errorDataFinal = Buffer.concat(stderrChunks).toString("utf-8");

        if (code === 0) {
          // Retornamos o JSON processado
          resolve(dataFinal.trim() || "[]");
        } else {
          // Em caso de erro, rejeitamos com a mensagem completa capturada no stderr
          reject(`Erro no Backend (Código ${code}): ${errorDataFinal}`);
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

// NOVO HANDLER PARA CAPAS CORRIGIDO PARA PROD E DEV
ipcMain.handle("get-capa-base64", async (_event, url: string) => {
  try {
    const pathCapa = isDev
      ? path.join(process.cwd(), "frontend", "public", "img", url)
      : path.join(app.getPath("userData"), "frontend", "public", "img", url);

    // Verifica se o arquivo existe de forma assíncrona
    const stats = await fs.stat(pathCapa).catch(() => null);
    if (!stats) return null;

    // Lendo o arquivo sem bloquear a Main Thread
    const buffer = await fs.readFile(pathCapa);

    const ext = path.extname(url).toLowerCase().replace(".", "");
    const mime = ext === "jpg" ? "jpeg" : ext;

    return `data:image/${mime};base64,${buffer.toString("base64")}`;
  } catch (error) {
    console.error("Erro ao converter imagem para base64:", error);
    return null;
  }
});

app.whenReady().then(() => {
  createWindow();
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") app.quit();
});
