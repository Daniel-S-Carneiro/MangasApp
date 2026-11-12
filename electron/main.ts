import {
  app,
  BrowserWindow,
  ipcMain,
  protocol,
  dialog,
  shell,
  type IpcMainInvokeEvent,
} from "electron";

import { spawn, type ChildProcessWithoutNullStreams } from "child_process";
import { fileURLToPath } from "url";
import { promises as fs } from "fs";
import path from "path";
import crypto from "crypto";

process.env["ELECTRON_DISABLE_SECURITY_WARNINGS"] = "true";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const isDev = !app.isPackaged;
const ENABLE_PROD_DEBUG = process.env.DEBUG_PROD === "true";
const ENABLE_DEBUG_LOGS = process.env.DEBUG_LOGS === "true";

// Controle para o Sidecar persistente do Python
let pyProcess: ChildProcessWithoutNullStreams | null = null;
const pendingRequests = new Map<
  string,
  { resolve: (val: string) => void; reject: (err: string) => void }
>();
let stdoutBuffer = "";
let restartAttempts = 0;
const MAX_RESTARTS = 3;

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
    scheme: "manga",
    privileges: {
      standard: true,
      secure: true,
      supportFetchAPI: true,
      corsEnabled: true,
      stream: true,
    },
  },
]);

// Função para iniciar e manter o Backend Python
function startPythonSidecar(): void {
  if (pyProcess) return;

  const pythonPath = isDev
    ? "python"
    : path.join(process.resourcesPath, "backend", "app", "app.exe");

  // Obtém o caminho dinâmico da pasta de dados do usuário criada pelo Electron
  const userDataPath = app.getPath("userData");

  // Injeta o caminho como argumento para o processo Python (tanto em Dev quanto em Prod)
  const args = isDev
    ? [
        path.join(process.cwd(), "backend", "app.py"),
        "--userdata",
        userDataPath,
      ]
    : ["--userdata", userDataPath];

  try {
    pyProcess = spawn(pythonPath, args);

    pyProcess.stdout.on("data", (chunk: Buffer) => {
      stdoutBuffer += chunk.toString("utf-8");
      let boundary = stdoutBuffer.indexOf("\n");

      while (boundary !== -1) {
        const line = stdoutBuffer.substring(0, boundary).trim();
        stdoutBuffer = stdoutBuffer.substring(boundary + 1);

        if (line) {
          try {
            const response = JSON.parse(line);
            const { id, data, error } = response;

            if (id && pendingRequests.has(id)) {
              const { resolve, reject } = pendingRequests.get(id)!;
              pendingRequests.delete(id);

              if (error) {
                reject(error);
              } else {
                resolve(JSON.stringify(data));
              }
            }
          } catch (err) {
            console.error(
              "Erro ao fazer parse da resposta JSON do Python:",
              err,
            );
          }
        }
        boundary = stdoutBuffer.indexOf("\n");
      }
    });

    pyProcess.stderr.on("data", (chunk: Buffer) => {
      console.error("LOG/ERRO INTERNO DO PYTHON:", chunk.toString("utf-8"));
    });

    // Sem estes listeners, uma falha ao iniciar o processo (python fora do
    // PATH, app.exe ausente ou em quarentena no antivírus) ou uma escrita no
    // stdin de um processo já encerrado vira exceção não tratada no processo
    // principal. O "close" que vem depois cuida das novas tentativas.
    pyProcess.on("error", (err) => {
      console.error("[SIDECAR] Falha no processo Python:", err);
    });
    pyProcess.stdin.on("error", (err) => {
      console.error("[SIDECAR] Falha ao escrever no stdin do Python:", err);
    });

    pyProcess.on("close", (code) => {
      console.warn(`[SIDECAR] Processo Python finalizado com código ${code}`);
      for (const { reject } of pendingRequests.values()) {
        reject(`O backend Python encerrou inesperadamente (Código ${code}).`);
      }
      pendingRequests.clear();
      stdoutBuffer = "";
      pyProcess = null;

      if (restartAttempts < MAX_RESTARTS) {
        restartAttempts++;
        console.log(
          `[SIDECAR] Tentando reiniciar (${restartAttempts}/${MAX_RESTARTS})...`,
        );
        setTimeout(startPythonSidecar, 2000 * restartAttempts);
      } else {
        console.error("[SIDECAR] Limite de reinícios atingido.");
        dialog.showErrorBox(
          "Erro ao iniciar o backend",
          "Não foi possível iniciar o backend do Gerenciador de Mangas, então " +
            "a sua lista não pode ser carregada.\n\n" +
            "Se o antivírus colocou o arquivo app.exe em quarentena, restaure-o " +
            "ou reinstale o aplicativo e abra-o de novo.",
        );
      }
    });
  } catch (err) {
    console.error("Erro ao iniciar o processo Python:", err);
    pyProcess = null;
  }
}

// Até a v1.1.0 o app se chamava "Gerenciador de Mangás" e os dados ficavam em
// %APPDATA%\Gerenciador de Mangás. O acento quebrava o novo protocolo de
// comunicação, então o nome ficou sem acento e a pasta de dados mudou junto.
// Na primeira abertura, copia o banco e as capas da pasta antiga. Só o Node
// lê esse caminho com acento; o Python já recebe a pasta nova.
async function migrarDadosDaPastaAntiga(
  pastaAntiga: string,
  pastaNova: string,
): Promise<void> {
  const existe = (p: string) =>
    fs.access(p).then(
      () => true,
      () => false,
    );

  const bancoAntigo = path.join(pastaAntiga, "data", "mangas.db");
  const bancoNovo = path.join(pastaNova, "data", "mangas.db");

  // Nada para migrar, ou a pasta nova já tem banco: não sobrescreve nada
  if (!(await existe(bancoAntigo)) || (await existe(bancoNovo))) return;

  // Capas primeiro e banco por último: se a cópia parar no meio, a próxima
  // abertura tenta de novo, porque o banco novo ainda não existe
  const capasAntigas = path.join(pastaAntiga, "frontend", "public", "img");
  if (await existe(capasAntigas)) {
    await fs.cp(
      capasAntigas,
      path.join(pastaNova, "frontend", "public", "img"),
      { recursive: true, force: false },
    );
  }
  await fs.mkdir(path.dirname(bancoNovo), { recursive: true });
  await fs.copyFile(bancoAntigo, bancoNovo);
  console.log(`[MIGRAÇÃO] Dados copiados de ${pastaAntiga}`);
}

// Prevenção de Path Traversal
function sanitizePath(baseDir: string, unsafePath: string): string | null {
  const normalized = path
    .normalize(unsafePath)
    .replace(/^(\.\.(\/|\\|$))+/, "");
  const finalPath = path.join(baseDir, normalized);
  if (!finalPath.startsWith(baseDir)) {
    return null;
  }
  return finalPath;
}

function createWindow(): void {
  const win = new BrowserWindow({
    width: 1200,
    height: 800,
    show: false,
    title: "Gerenciador de Mangas",
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

  if (isDev || ENABLE_PROD_DEBUG) {
    win.webContents.openDevTools({ mode: "detach" });
  } else {
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

  // Ferramentas de Debug recuperadas integralmente da V1
  win.webContents.on("did-finish-load", async () => {
    if (ENABLE_DEBUG_LOGS) {
      win.webContents.send(
        "log",
        "process.resourcesPath → " + process.resourcesPath,
      );
      win.webContents.send(
        "log",
        "app.getPath('userData') → " + app.getPath("userData"),
      );
      win.webContents.send("log", "app.getAppPath() → " + app.getAppPath());

      const imgDir = path.join(
        app.getPath("userData"),
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

// IPC para o Python Sidecar
ipcMain.handle(
  "python:query",
  async (_event: IpcMainInvokeEvent, payload: any): Promise<string> => {
    if (!pyProcess) {
      return Promise.reject("O processo backend Python não está em execução.");
    }

    return new Promise((resolve, reject) => {
      const id = crypto.randomUUID();
      pendingRequests.set(id, { resolve, reject });

      const wrappedRequest = { id, payload };

      try {
        pyProcess!.stdin.write(JSON.stringify(wrappedRequest) + "\n");
      } catch (err) {
        pendingRequests.delete(id);
        reject(
          "Falha ao enviar requisição: " +
            (err instanceof Error ? err.message : String(err)),
        );
      }
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

app.whenReady().then(async () => {
  // Protocolo manga com Sanitize (V2) e Fallback (V1)
  protocol.handle("manga", async (request) => {
    try {
      const requestUrl = new URL(request.url);
      let unsafePath = path.join(requestUrl.hostname, requestUrl.pathname);
      unsafePath = decodeURIComponent(unsafePath)
        .replace(/\\/g, "/")
        .replace(/^\/+|\/+$/g, "");

      const baseImgDir = isDev
        ? path.join(process.cwd(), "frontend", "public", "img")
        : path.join(app.getPath("userData"), "frontend", "public", "img");

      const filePath = sanitizePath(baseImgDir, unsafePath);
      if (!filePath) throw new Error("Tentativa de path traversal detectada");

      const fileBuffer = await fs.readFile(filePath);
      const ext = path.extname(filePath).toLowerCase();
      const mimeTypes: Record<string, string> = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
      };
      const contentType = mimeTypes[ext] || "application/octet-stream";

      return new Response(fileBuffer, {
        status: 200,
        headers: { "Content-Type": contentType },
      });
    } catch (error) {
      console.warn(
        "Imagem principal falhou no protocolo manga://, aplicando fallback...",
      );

      // Lógica de fallback recuperada
      try {
        const fallbackPath = isDev
          ? path.join(process.cwd(), "frontend", "public", "img", "default.jpg")
          : path.join(
              app.getPath("userData"),
              "frontend",
              "public",
              "img",
              "default.jpg",
            );

        const fallbackBuffer = await fs.readFile(fallbackPath);
        return new Response(fallbackBuffer, {
          status: 200,
          headers: { "Content-Type": "image/jpeg" },
        });
      } catch (fallbackError) {
        return new Response("Imagem padrão não encontrada", { status: 404 });
      }
    }
  });

  // Precisa terminar antes de o Python abrir o banco da pasta nova
  try {
    await migrarDadosDaPastaAntiga(
      path.join(app.getPath("appData"), "Gerenciador de Mangás"),
      app.getPath("userData"),
    );
  } catch (err) {
    console.error("[MIGRAÇÃO] Falha ao copiar os dados da versão antiga:", err);
  }

  startPythonSidecar();
  createWindow();
});

// Encerramento seguro
app.on("before-quit", () => {
  if (pyProcess) {
    try {
      pyProcess.kill();
    } catch (err) {
      console.error("Erro ao derrubar o processo Python:", err);
    }
    pyProcess = null;
  }
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") app.quit();
});
