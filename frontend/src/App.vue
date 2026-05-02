<script setup lang="ts">
import { ref, onMounted } from "vue";
import MangaForm from "./components/MangaForm.vue";
import MangaModal from "./components/MangaModal.vue";

const listaMangas = ref<any[]>([]);
const filtro = ref("");
const isFormOpen = ref(false);
const isModalOpen = ref(false);
const darkTheme = ref(true); // Recuperado
const mangaParaEditar = ref<any>(null);
const draggedItem = ref<any>(null);
const exibirConfirmacao = ref(false);
const idParaExcluir = ref<number | null>(null);
const api = (window as any).api;

function pedirExclusao(id: number) {
  idParaExcluir.value = id;
  exibirConfirmacao.value = true;
}

async function confirmarExclusao() {
  // Verificação de segurança: só prossegue se houver um ID válido
  if (idParaExcluir.value === null) return;

  await window.api.callPython({ action: "delete", id: idParaExcluir.value });
  exibirConfirmacao.value = false;
  idParaExcluir.value = null; // Limpa o ID após a exclusão bem-sucedida
  listarMangas();
}

async function listarMangas() {
  const rawResponse = await window.api.callPython({ action: "list" });
  listaMangas.value = JSON.parse(rawResponse);
}

// Recuperado: Lógica de Tema
function toggleTheme() {
  darkTheme.value = !darkTheme.value;
  document.body.classList.toggle("light-mode", !darkTheme.value);
}

async function mudarStatus(id: number, atual: string) {
  const ordem = ["Lendo", "Concluído", "Pausado"];
  const novo = ordem[(ordem.indexOf(atual) + 1) % ordem.length];
  await window.api.callPython({ action: "update_status", id, status: novo });
  listarMangas();
}

function abrirModal(manga: any) {
  mangaParaEditar.value = { ...manga };
  isModalOpen.value = true;
}

// Funções de Drag and Drop
function onDragStart(manga: any) {
  draggedItem.value = manga;
}
function onDragEnd() {
  draggedItem.value = null;
}
async function onDrop(target: any) {
  if (!draggedItem.value || draggedItem.value.id === target.id) return;
  const oldIdx = listaMangas.value.findIndex(
    (m) => m.id === draggedItem.value.id,
  );
  const newIdx = listaMangas.value.findIndex((m) => m.id === target.id);
  listaMangas.value.splice(oldIdx, 1);
  listaMangas.value.splice(newIdx, 0, draggedItem.value);
  await window.api.callPython({
    action: "update_order",
    order_list: listaMangas.value.map((m) => m.id),
  });
  draggedItem.value = null;
}

onMounted(listarMangas);
</script>

<template>
  <h1>📚 Meu Gerenciador de Mangás</h1>

  <div class="controls">
    <!-- Botão de Tema Recuperado -->
    <button @click="toggleTheme" class="btn-theme">🌓 Tema</button>
    <button @click="isFormOpen = !isFormOpen" class="btn-toggle">
      {{ isFormOpen ? "➖ Fechar" : "➕ Novo Mangá" }}
    </button>
    <input type="text" v-model="filtro" placeholder="🔍 Pesquisar..." />
  </div>

  <MangaForm
    :isOpen="isFormOpen"
    @saved="
      isFormOpen = false;
      listarMangas();
    "
  />

  <div class="grid">
    <div
      v-for="m in listaMangas.filter((i) =>
        i.nome_pt.toLowerCase().includes(filtro.toLowerCase()),
      )"
      :key="m.id"
      class="card"
      :class="{ dragging: draggedItem?.id === m.id }"
      draggable="true"
      @dragstart="onDragStart(m)"
      @dragover.prevent
      @drop="onDrop(m)"
      @dragend="onDragEnd"
    >
      <!-- Tag de Status -->
      <div
        :class="[
          'status-tag',
          m.status
            .toLowerCase()
            .normalize('NFD')
            .replace(/[\u0300-\u036f]/g, '')
            .replace(' ', ''),
        ]"
      >
        {{ m.status }}
      </div>

      <img
        :src="
          m.capa.startsWith('manga_') ? `capas://${m.capa}` : `./img/${m.capa}`
        "
        class="sua-classe-de-estilo"
      />

      <h3>{{ m.nome_pt }}</h3>
      <small>{{ m.nome_en }}</small>
      <p>
        Capítulo: <strong>{{ m.capitulo }}</strong>
      </p>

      <!-- Rodapé do Card Recuperado -->
      <div class="card-footer">
        <!-- Mude de window.api para apenas api -->
        <a :href="m.link" class="btn-ler" @click.prevent="api.openLink(m.link)">
          Ler
        </a>

        <button
          @click="mudarStatus(m.id, m.status)"
          class="btn-icon"
          title="Trocar Status"
        >
          🔄
        </button>
        <button @click="abrirModal(m)" class="btn-icon" title="Editar Dados">
          ⚙️
        </button>
      </div>
    </div>
  </div>

  <MangaModal
    :isOpen="isModalOpen"
    :manga="mangaParaEditar"
    @close="isModalOpen = false"
    @save="
      listarMangas();
      isModalOpen = false;
    "
    @delete="
      isModalOpen = false;
      pedirExclusao(mangaParaEditar.id);
    "
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
</template>
