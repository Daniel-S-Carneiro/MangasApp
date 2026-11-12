# 📚 Gerenciador de Mangas (MangasApp)

> ⚠️ **Projeto descontinuado.** O MangasApp não recebe mais atualizações, e a **v1.2.0** é a última versão.
>
> O sucessor é o **[Manga_Manager](https://github.com/Daniel-S-Carneiro/Manga_Manager)**. Ele foi reescrito em Flutter, tem leitor embutido e backup, e funciona no Windows, no Linux e no Android.

Gerenciador de mangás para Windows feito com **Electron**, **Vue 3** e **Python** (SQLite).

## 🚀 Funcionalidades

- Cadastro de mangás com nome em português e em inglês, capítulo atual, link de leitura, capa e status (**Lendo**, **Concluído** e **Pausado**).
- Busca pelo nome, reordenação arrastando os cards e carregamento da lista em páginas.
- O botão **Ler** abre o link no navegador padrão.
- Tema claro e escuro.
- Todos os dados ficam no seu computador.

## 📥 Instalação

Baixe o instalador `.exe` da [última release](https://github.com/Daniel-S-Carneiro/MangasApp/releases/latest) e execute.

Os dados ficam em `%APPDATA%\Gerenciador de Mangas`. Ao desinstalar, o instalador pergunta se você quer apagá-los.

**Vindo da v1.1.0?** Até a v1.1.0 o app se chamava "Gerenciador de Mangás", com acento, e os dados ficavam em `%APPDATA%\Gerenciador de Mangás`. O acento quebrava o novo protocolo de comunicação, por isso o nome ficou sem acento. Na primeira abertura, a v1.2.0 copia o banco e as capas da pasta antiga para a nova. A pasta antiga não é apagada.

> **⚠️ Aviso do Windows SmartScreen ou do antivírus**
>
> O instalador não tem assinatura digital paga da Microsoft. Por isso, o SmartScreen ou alguns antivírus podem mostrar um alerta de "Fornecedor desconhecido" ou um falso positivo.
>
> Para instalar mesmo assim, clique em **Mais informações** e depois em **Executar assim mesmo**. Todo o código-fonte está aberto neste repositório para conferência.

## 🛠️ Como funciona

- **Frontend:** Vue 3, TypeScript e Vite.
- **Desktop:** Electron. A janela roda com `contextIsolation` ligado e `nodeIntegration` desligado, e o preload expõe só uma API mínima.
- **Backend:** Python com SQLite, compilado com PyInstaller. Ele fica aberto junto com o app e conversa com o Electron por stdin/stdout: uma mensagem JSON por linha, com um ID para cada requisição.
- **Capas:** carregadas pelo protocolo `manga://`, que só lê arquivos da pasta de capas.

## 💻 Desenvolvimento

Requisitos: Node.js 22 ou mais novo, Python 3 no PATH e, para gerar o instalador, o PyInstaller (`python -m pip install pyinstaller`).

```bash
git clone https://github.com/Daniel-S-Carneiro/MangasApp.git
cd MangasApp
npm install
```

O `postinstall` instala também as dependências da pasta `frontend`.

Para rodar em modo de desenvolvimento:

```bash
npm run dev
```

> O modo de desenvolvimento usa a mesma pasta de dados do app instalado.

Para gerar o instalador em `dist_electron/`:

```bash
npm run build:full
```

## 📄 Licença

Distribuído sob a licença MIT. Veja o arquivo [LICENSE](LICENSE).
