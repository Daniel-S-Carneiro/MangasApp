<script setup lang="ts">
import { ref, onMounted, computed } from "vue";
import MangaForm from "./components/MangaForm.vue";
import MangaModal from "./components/MangaModal.vue";
import MangaCard from "./components/MangaCard.vue";

const listaMangas = ref<any[]>([]);
const filtro = ref("");
const isFormOpen = ref(false);
const isModalOpen = ref(false);
const darkTheme = ref(true);
const mangaParaEditar = ref<any>(null);
const draggedItem = ref<any>(null);
const exibirConfirmacao = ref(false);
const idParaExcluir = ref<number | null>(null);

// 🔔 Novo estado para alerta de link inválido
const exibirAlertaLink = ref(false);
const mensagemAlertaLink = ref("");

const mangasFiltrados = computed(() => {
  return listaMangas.value.filter((i) =>
    i.nome_pt.toLowerCase().includes(filtro.value.toLowerCase()),
  );
});

function pedirExclusao(id: number) {
  idParaExcluir.value = id;
  exibirConfirmacao.value = true;
}

async function confirmarExclusao() {
  if (idParaExcluir.value === null) return;

  try {
    await window.api.callPython({ action: "delete", id: idParaExcluir.value });
    exibirConfirmacao.value = false;
    idParaExcluir.value = null;
    listarMangas();
  } catch (error) {
    console.error("Erro ao excluir:", error);
    alert("ERRO NO BACKEND (Delete): " + error);
  }
}

async function listarMangas() {
  let response = ""; // Declaramos aqui fora para o catch poder acessar

  try {
    response = await window.api.callPython({ action: "list" });

    let validJson = response.trim();

    // Se por acaso o Python mandar lixo no final, limpamos
    if (validJson.includes("][")) {
      validJson = validJson.split("][")[0] + "]";
    }

    listaMangas.value = JSON.parse(validJson);
  } catch (error) {
    console.error("Erro ao listar mangás:", error);
    console.warn("Falha no parse. Resposta bruta recebida:", response);
  }
}

function toggleTheme() {
  darkTheme.value = !darkTheme.value;
  document.body.classList.toggle("light-mode", !darkTheme.value);
}

async function mudarStatus(id: number, atual: string) {
  const ordem = ["Lendo", "Concluído", "Pausado"];

  // Normaliza e limpa o texto vindo do Python para garantir a comparação
  const statusNormalizado = atual.trim().normalize("NFC"); // Tenta reconstruir caracteres quebrados

  // Procura o índice. Se não achar por causa do encoding, tenta por aproximação
  let indexAtual = ordem.indexOf(statusNormalizado);

  if (indexAtual === -1) {
    if (statusNormalizado.includes("Lendo")) indexAtual = 0;
    else if (
      statusNormalizado.includes("Conclu") ||
      statusNormalizado.includes("conclu")
    )
      indexAtual = 1;
    else if (statusNormalizado.includes("Pausado")) indexAtual = 2;
  }

  const proximoIndex = (indexAtual + 1) % ordem.length;
  const novo = ordem[proximoIndex];

  try {
    await window.api.callPython({ action: "update_status", id, status: novo });
    listarMangas();
  } catch (error) {
    console.error("Erro ao mudar status:", error);
  }
}
function abrirModal(manga: any) {
  mangaParaEditar.value = { ...manga };
  isModalOpen.value = true;
}

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

  try {
    await window.api.callPython({
      action: "update_order",
      order_list: listaMangas.value.map((m) => m.id),
    });
  } catch (error) {
    alert("ERRO NO BACKEND (Ordem): " + error);
  }
  draggedItem.value = null;
}

onMounted(() => {
  listarMangas();

  window.api.onLog((message: string) => {
    console.log(message);
  });

  // 🔔 Escuta os avisos de link inválido vindos do main.ts
  window.api.onAlertLink((mensagem: string) => {
    mensagemAlertaLink.value = mensagem;
    exibirAlertaLink.value = true;
  });
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

  <MangaForm
    :isOpen="isFormOpen"
    @saved="
      isFormOpen = false;
      listarMangas();
    "
  />

  <div class="grid">
    <MangaCard
      v-for="m in mangasFiltrados"
      :key="m.id"
      :manga="m"
      :isDragging="draggedItem?.id === m.id"
      @mudarStatus="mudarStatus"
      @abrirModal="abrirModal"
      @dragStart="onDragStart(m)"
      @drop="onDrop(m)"
      @dragEnd="onDragEnd"
    />
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

  <!-- Modal de confirmação de exclusão -->
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

  <!-- 🔔 Novo modal de alerta de link inválido -->
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
