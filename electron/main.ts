import {
  app,
  BrowserWindow,
  ipcMain,
  protocol,
  type IpcMainInvokeEvent,
} from "electron";
import * as path from "path";
import { spawn } from "child_process";
import { fileURLToPath } from "url";

// Desativa avisos de segurança no console durante o desenvolvimento
process.env["ELECTRON_DISABLE_SECURITY_WARNINGS"] = "true";

/**
 * Registra privilégios para o protocolo file://.
 * Isso ajuda o Chromium a entender que arquivos locais dentro do ASAR são seguros.
 */
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

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Detecta se o app está rodando em desenvolvimento ou produção
const isDev = !app.isPackaged;

function createWindow(): void {
  const win = new BrowserWindow({
    width: 1000,
    height: 700,
    show: false,
    title: "Electron + Vue + Python + SQLite",
    webPreferences: {
      // Aponta para o arquivo .cjs (geralmente na mesma pasta do main compilado)
      preload: path.join(__dirname, "preload.cjs"),
      contextIsolation: true,
      nodeIntegration: false,
      /**
       * webSecurity: false permite carregar scripts e estilos do protocolo file://
       * sem erros de "Not allowed to load local resource" em ambientes restritos.
       */
      webSecurity: false,
    },
  });

  win.maximize();
  win.show();

  if (isDev) {
    win.loadURL("http://localhost:5173");
  } else {
    // app.getAppPath() nos leva à raiz do pacote asar
    // Como no package.json incluímos "frontend/dist/**/*", o caminho interno é:
    const indexPath = path.join(
      app.getAppPath(),
      "frontend",
      "dist",
      "index.html",
    );

    win.loadFile(indexPath).catch((err) => {
      console.error("Não encontrou o index.html principal. Tentando raiz...");
      // Tentativa de backup caso a estrutura mude no build
      win.loadFile(path.join(app.getAppPath(), "dist", "index.html"));
    });
  }

  // Previne que o título da janela seja sobrescrito pelo título do HTML
  win.on("page-title-updated", (e) => e.preventDefault());
}

/**
 * Handler para comunicação IPC com o Python.
 * Executa o script app.py e retorna o resultado para o Frontend.
 */
ipcMain.handle(
  "python:query",
  async (_event: IpcMainInvokeEvent, payload: any): Promise<string> => {
    return new Promise((resolve, reject) => {
      // Define o caminho do script Python baseado no ambiente (Dev ou Packaged)
      const pythonScriptPath = isDev
        ? path.join(process.cwd(), "backend", "app.py")
        : path.join(process.resourcesPath, "backend", "app.py");

      // Spawna o processo Python
      const py = spawn("python", [pythonScriptPath, JSON.stringify(payload)], {
        cwd: isDev ? process.cwd() : process.resourcesPath,
        shell: false,
      });

      let data = "";
      let errorData = "";

      py.stdout.on("data", (chunk: Buffer) => {
        data += chunk.toString();
      });

      py.stderr.on("data", (chunk: Buffer) => {
        errorData += chunk.toString();
      });

      py.on("close", (code: number) => {
        if (code === 0) {
          resolve(data);
        } else {
          console.error("Erro no Python (Stderr):", errorData);
          reject(
            `Processo Python falhou (Código ${code}). Detalhes: ${errorData}`,
          );
        }
      });
    });
  },
);

app.whenReady().then(createWindow);

// Fecha o aplicativo quando todas as janelas forem fechadas (exceto no macOS)
app.on("window-all-closed", () => {
  if (process.platform !== "darwin") app.quit();
});
