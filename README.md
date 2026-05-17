# 📚 Manga Manager

Um gestor de mangás desktop construído com **Electron**, **Vue.js 3** e **Python**.

## 🚀 Funcionalidades

- Gestão completa de mangás (CRUD).
- Comunicação segura e assíncrona via IPC.
- Carregamento de capas em Base64 para performance e segurança.
- Interface moderna com suporte a tema escuro.

## 🛠️ Tecnologias

- **Frontend:** Vue.js 3, TypeScript, Vite.
- **Desktop:** Electron.
- **Backend:** Python (Scripts de processamento de dados).

## 📦 Como Instalar e Rodar

1. **Clone o repositório:**

   ```bash
   git clone [https://github.com/teu-utilizador/manga-manager.git](https://github.com/teu-utilizador/manga-manager.git)
   cd manga-manager

   ```

2. **Instale as dependências de Node (Raiz e Frontend):**
   ```bash
   npm install
   ```

> **Nota:** O projeto utiliza o gancho `postinstall` para baixar automaticamente os pacotes da pasta `frontend` logo após concluir os da raiz.

3. **Pré-requisitos do Python:**
   - O backend foi desenvolvido utilizando apenas bibliotecas nativas do Python (`sqlite3`, `json`, `os`, etc.), portanto **não é necessário** criar ambiente virtual (`venv`) ou instalar dependências extras.
   - _Opcional:_ Certifique-se de ter o **Python 3.x** instalado no seu sistema e adicionado ao PATH caso deseje testar ou alterar o backend em modo de desenvolvimento.

4. **Inicie o projeto em modo de desenvolvimento:**
   ```bash
   npm run dev
   ```

## 📄 Licença

Este projeto está sob a licença MIT - veja o ficheiro [LICENSE](LICENSE) para detalhes.
