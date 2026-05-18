import fs from "fs";
import path from "path";

const packageJsonPath = path.join(process.cwd(), "package.json");
const versionInfoPath = path.join(
  process.cwd(),
  "backend",
  "file_version_info.txt",
);

try {
  // 1. Lê a versão do package.json
  const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, "utf8"));
  const version = packageJson.version; // Ex: "1.1.0"

  // Monta as variações necessárias (Padrão Windows de 4 blocos)
  const versionParts = version.split(".");
  while (versionParts.length < 4) {
    versionParts.push("0");
  }
  const tupleVersion = versionParts.join(", "); // "1, 1, 0, 0"
  const stringVersion = versionParts.join("."); // "1.1.0.0"

  console.log(
    `\x1b[36m[Sync-Version]\x1b[0m Sincronizando versão para ${stringVersion}...`,
  );

  // 2. Lê o arquivo de texto
  let content = fs.readFileSync(versionInfoPath, "utf8");

  // 3. Substituições Cirúrgicas (Preserva toda a estrutura ao redor)
  // Alvo: filevers=(X, X, X, X)
  content = content.replace(
    /(filevers\s*=\s*\()[^)]+(\))/g,
    `$1${tupleVersion}$2`,
  );

  // Alvo: prodvers=(X, X, X, X)
  content = content.replace(
    /(prodvers\s*=\s*\()[^)]+(\))/g,
    `$1${tupleVersion}$2`,
  );

  // Alvo: StringStruct('FileVersion', 'X.X.X.X')
  content = content.replace(
    /(StringStruct\s*\(\s*'FileVersion'\s*,\s*')[^']+(\'\s*\))/g,
    `$1${stringVersion}$2`,
  );

  // Alvo: StringStruct('ProductVersion', 'X.X.X.X')
  content = content.replace(
    /(StringStruct\s*\(\s*'ProductVersion'\s*,\s*')[^']+(\'\s*\))/g,
    `$1${stringVersion}$2`,
  );

  // 4. Salva o arquivo atualizado
  fs.writeFileSync(versionInfoPath, content, "utf8");
  console.log(
    "\x1b[32m[Sync-Version] Sucesso!\x1b[0m file_version_info.txt atualizado sem quebras de estrutura.",
  );
} catch (error) {
  console.error(
    "\x1b[31m[Sync-Version] Erro crítico ao sincronizar versões:\x1b[0m",
    error.message,
  );
  process.exit(1);
}
