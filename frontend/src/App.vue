<script setup lang="ts">
import { ref, onMounted, computed, watch } from "vue";
import MangaForm from "./components/MangaForm.vue";
import MangaModal from "./components/MangaModal.vue";
import MangaCard from "./components/MangaCard.vue";

interface Manga {
  id: number;
  nome_pt: string;
  nome_en: string;
  capitulo: number;
  link: string;
  capa: string;
  status: string;
  ordem: number;
}

const listaMangas = ref<Manga[]>([]);
const filtro = ref("");
const isFormOpen = ref(false);
const isModalOpen = ref(false);
const darkTheme = ref(true);
const mangaParaEditar = ref<Manga | null>(null);
const draggedItem = ref<Manga | null>(null);
const exibirConfirmacao = ref(false);
const idParaExcluir = ref<number | null>(null);
const paginaAtual = ref(1);
const limitePorPagina = 20;
const temMaisMangas = ref(true);

const exibirAlertaLink = ref(false);
const mensagemAlertaLink = ref("");

// Filtro processado no banco de dados; a propriedade computada repassa a lista atualizada
const mangasExibidos = computed(() => listaMangas.value);

// Bloqueia a ordenação por arrasto (drag and drop) se houver filtro de texto ativo
const isDraggableActive = computed(() => filtro.value.trim() === "");

async function listarMangas(novaPagina = 1, append = false) {
  try {
    const response = await window.api.callPython({
      action: "list",
      limite: limitePorPagina,
      pagina: novaPagina,
      filtro: filtro.value,
    });

    let validJson = response.trim();
    if (validJson.includes("][")) {
      validJson = validJson.split("][")[0] + "]";
    }

    const novosMangas = JSON.parse(validJson);

    // Define o estado da paginação com base no volume de dados retornado
    if (novosMangas.length < limitePorPagina) {
      temMaisMangas.value = false;
    } else {
      temMaisMangas.value = true;
    }

    if (append) {
      // Adiciona os novos itens ao fim da lista existente (Scroll infinito / Carregar mais)
      listaMangas.value.push(...novosMangas);
      paginaAtual.value = novaPagina;
    } else {
      // Substitui a lista completa (Carregamento inicial ou nova pesquisa)
      listaMangas.value = novosMangas;
      paginaAtual.value = 1;
    }
  } catch (error) {
    console.error("Erro ao listar mangás:", error);
  }
}

// Watcher com debounce para otimizar as requisições de busca ao backend
let timeoutFiltro: number;
watch(filtro, () => {
  clearTimeout(timeoutFiltro);
  timeoutFiltro = window.setTimeout(() => {
    listarMangas(1, false);
  }, 300);
});

function carregarProximaPagina() {
  if (!temMaisMangas.value) return;
  listarMangas(paginaAtual.value + 1, true);
}

async function adicionarManga(novoManga: Manga) {
  draggedItem.value = null;
  isFormOpen.value = false;

  // Consulta o banco de dados para sincronizar o estado oficial da lista
  try {
    await listarMangas();
  } catch (error) {
    listaMangas.value.push(novoManga);
    console.error("Erro ao sincronizar nova lista:", error);
  }
}

function atualizarManga() {
  isModalOpen.value = false;
  listarMangas(1, false);
}

function pedirExclusao(id: number) {
  idParaExcluir.value = id;
  exibirConfirmacao.value = true;
}

async function confirmarExclusao() {
  if (idParaExcluir.value === null) return;

  const index = listaMangas.value.findIndex(
    (m) => m.id === idParaExcluir.value,
  );
  if (index === -1) return;

  const backup = listaMangas.value[index];
  listaMangas.value.splice(index, 1);
  exibirConfirmacao.value = false;
  isModalOpen.value = false;

  try {
    await window.api.callPython({ action: "delete", id: idParaExcluir.value });
    idParaExcluir.value = null;
  } catch (error) {
    listaMangas.value.splice(index, 0, backup);
    console.error("Erro ao excluir:", error);
  }
}

async function mudarStatus(id: number, atual: string) {
  const ordemStatus = ["Lendo", "Concluído", "Pausado"];
  const indexAtual =
    ordemStatus.indexOf(atual) !== -1 ? ordemStatus.indexOf(atual) : 0;
  const proximoIndex = (indexAtual + 1) % ordemStatus.length;
  const novo = ordemStatus[proximoIndex];

  const item = listaMangas.value.find((m) => m.id === id);
  if (!item) return;

  const backup = item.status;
  item.status = novo;

  try {
    await window.api.callPython({ action: "update_status", id, status: novo });
  } catch (error) {
    item.status = backup;
    console.error("Erro ao mudar status:", error);
  }
}

function abrirModal(manga: Manga) {
  // Passa a referência direta do objeto para mutação reativa no componente filho
  mangaParaEditar.value = manga;
  isModalOpen.value = true;
}

function onDragStart(manga: Manga) {
  if (!isDraggableActive.value) return;
  draggedItem.value = manga;
}

function onDragEnd() {
  draggedItem.value = null;
}

async function onDrop(target: Manga) {
  const dragged = draggedItem.value;
  if (!dragged || dragged.id === target.id) {
    draggedItem.value = null;
    return;
  }

  const backup = [...listaMangas.value];
  const oldIdx = listaMangas.value.findIndex((m) => m.id === dragged.id);
  const newIdx = listaMangas.value.findIndex((m) => m.id === target.id);

  listaMangas.value.splice(oldIdx, 1);
  listaMangas.value.splice(newIdx, 0, dragged);

  listaMangas.value.forEach((m, index) => {
    m.ordem = index;
  });

  // Reseta o estado visual do arrasto antes da resolução da API para otimizar a interface
  draggedItem.value = null;

  try {
    await window.api.callPython({
      action: "update_order",
      order_list: listaMangas.value.map((m) => m.id),
    });
  } catch (error) {
    listaMangas.value = backup;
    console.error("Erro ao salvar ordem:", error);
  }
}

function toggleTheme() {
  darkTheme.value = !darkTheme.value;
  localStorage.setItem("theme", darkTheme.value ? "dark" : "light");
  document.body.classList.toggle("light-mode", !darkTheme.value);
}

onMounted(() => {
  listarMangas();
  window.api.onLog((message: string) => console.log(message));
  window.api.onAlertLink((mensagem: string) => {
    mensagemAlertaLink.value = mensagem;
    exibirAlertaLink.value = true;
  });
  darkTheme.value = localStorage.getItem("theme") !== "light";
  document.body.classList.toggle("light-mode", !darkTheme.value);
});
</script>

<template>
  <h1>📚 Meu Gerenciador de Mangás</h1>

  <div class="controls">
    <button @click="toggleTheme" class="btn-theme">🌓 Tema</button>
    <button @click="isFormOpen = !isFormOpen" class="btn-toggle">
      {{ isFormOpen ? "➖ Fechar" : "➕ Novo Mangá" }}
    </button>
    <input type="text" v-model="filtro" placeholder="🔍 Pesquisar..." />
  </div>

  <MangaForm :isOpen="isFormOpen" @saved="adicionarManga" />

  <div class="grid">
    <MangaCard
      v-for="m in mangasExibidos"
      :key="m.id"
      :manga="m"
      :isDragging="draggedItem?.id === m.id"
      :draggable="isDraggableActive"
      @mudarStatus="mudarStatus"
      @abrirModal="abrirModal"
      @dragStart="onDragStart(m)"
      @drop="onDrop(m)"
      @dragEnd="onDragEnd"
    />
  </div>

  <div v-if="temMaisMangas" class="load-more-container">
    <button @click="carregarProximaPagina" class="btn-load-more">
      📥 Carregar Mais Mangás
    </button>
  </div>

  <MangaModal
    :isOpen="isModalOpen"
    :manga="mangaParaEditar"
    @close="isModalOpen = false"
    @save="atualizarManga"
    @delete="mangaParaEditar ? pedirExclusao(mangaParaEditar.id) : null"
  />

  <div v-if="exibirConfirmacao" class="modal-overlay">
    <div class="modal-card">
      <h3>⚠️ Atenção</h3>
      <p>Tem certeza que deseja excluir este mangá?</p>
      <div class="modal-buttons">
        <button @click="confirmarExclusao" class="btn-delete">
          Sim, Excluir
        </button>
        <button @click="exibirConfirmacao = false" class="btn-cancel">
          Cancelar
        </button>
      </div>
    </div>
  </div>

  <div v-if="exibirAlertaLink" class="modal-overlay">
    <div class="modal-card">
      <h3>⚠️ Atenção</h3>
      <p>{{ mensagemAlertaLink }}</p>
      <div class="modal-buttons">
        <button @click="exibirAlertaLink = false" class="btn-cancel">Ok</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* --- Layout Estrutural da Página (grid.css & base.css) --- */
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.controls {
  display: flex;
  justify-content: center;
  gap: 10px;
  margin-bottom: 20px;
}

.controls input[type="text"] {
  padding: 10px;
  border-radius: 4px;
  background: var(--input-bg);
  color: var(--text);
  border: 1px solid var(--border);
  font-size: 1rem;
}

/* --- Botões de Controle Principal --- */
.btn-theme,
.btn-toggle,
.btn-delete,
.btn-cancel {
  padding: 10px 15px;
  border-radius: 4px;
  border: none;
  cursor: pointer;
  font-weight: bold;
}

.btn-theme {
  background: #6c5ce7;
  color: white;
}

.btn-toggle {
  background: #333;
  color: white;
  border: 1px solid var(--border);
}

/* --- Seção de Paginação (Carregar Mais) --- */
.load-more-container {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 100%;
  padding: 20px 0 40px 0;
  box-sizing: border-box;
}

.btn-load-more {
  margin: 0;
  box-sizing: border-box;
  padding: 10px 15px;
  border-radius: 4px;
  cursor: pointer;
  font-weight: bold;
  background: #252525;
  color: var(--text);
  border: 1px solid var(--border);
  font-size: 0.95em;
  display: flex;
  align-items: center;
  gap: 8px;
  transition:
    background-color 0.2s ease,
    border-color 0.2s ease,
    transform 0.1s ease;
}

.btn-load-more:hover {
  background: #333333;
  border-color: #444444;
}

.btn-load-more:active {
  background: #1a1a1a;
  transform: scale(0.98);
}

.btn-load-more:focus-visible {
  outline: 2px solid #007acc;
  outline-offset: 2px;
}

/* --- Modais Locais de Confirmação e Alertas do App --- */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.85);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 9999;
  backdrop-filter: blur(4px);
  -webkit-backdrop-filter: blur(4px);
}

.modal-card {
  background: #1e1e1e;
  padding: 30px;
  border-radius: 15px;
  width: 90%;
  max-width: 400px;
  text-align: center;
  border: 1px solid #333;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
}

.modal-card h3 {
  margin-bottom: 20px;
  font-size: 1.3em;
  color: var(--text);
}

.modal-card p {
  color: #ccc;
  margin-bottom: 20px;
  font-size: 1rem;
  line-height: 1.4;
}

.modal-buttons {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 25px;
}

.btn-delete {
  background: #e74c3c;
  color: white;
}

.btn-cancel {
  background: #555;
  color: white;
}
</style>
