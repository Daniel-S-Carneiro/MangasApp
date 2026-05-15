<script setup lang="ts">
import { ref, onMounted, watch } from "vue";

// Captura as props em uma constante
const props = defineProps<{
  manga: any;
  isDragging?: boolean;
}>();

const emit = defineEmits([
  "mudarStatus",
  "abrirModal",
  "dragStart",
  "drop",
  "dragEnd",
]);

const api = (window as any).api;

// Estado reativo para armazenar o caminho da capa
const capaSrc = ref("");

// Função isolada para carregar a imagem
const carregarCapa = async () => {
  if (!props.manga.capa) {
    capaSrc.value = "./img/default.jpg";
    return;
  }

  if (
    props.manga.capa.startsWith("capa_") ||
    props.manga.capa.startsWith("manga_")
  ) {
    // Agora pegamos a string Base64 direta
    const res = await api.getCapaBase64(props.manga.capa);
    capaSrc.value = res || "./img/default.jpg";
  } else {
    capaSrc.value = `./img/${props.manga.capa}`;
  }
};

// Carrega ao montar o componente
onMounted(carregarCapa);

// Se o nome da capa mudar (ex: após uma edição), atualiza a imagem automaticamente
watch(() => props.manga.capa, carregarCapa);

// Handlers locais
const handleStatus = (id: number, status: string) =>
  emit("mudarStatus", id, status);
const handleEdit = (manga: any) => emit("abrirModal", manga);
</script>

<template>
  <div
    class="card"
    :class="{ dragging: props.isDragging }"
    draggable="true"
    @dragstart="emit('dragStart')"
    @dragover.prevent
    @drop="emit('drop')"
    @dragend="emit('dragEnd')"
  >
    <div
      :class="[
        'status-tag',
        props.manga.status
          .toLowerCase()
          .normalize('NFD')
          .replace(/[\u0300-\u036f]/g, '')
          .replace(' ', ''),
      ]"
    >
      {{ props.manga.status }}
    </div>

    <img :src="capaSrc" class="capa-manga" loading="lazy" />

    <div class="info-container">
      <h3>{{ props.manga.nome_pt }}</h3>
      <small>{{ props.manga.nome_en }}</small>
      <p>
        Capítulo: <strong>{{ props.manga.capitulo }}</strong>
      </p>
    </div>

    <div class="card-footer">
      <a
        :href="props.manga.link"
        class="btn-ler"
        @click.prevent="api.openLink(props.manga.link)"
      >
        Ler
      </a>

      <button
        @click="handleStatus(props.manga.id, props.manga.status)"
        class="btn-icon"
        title="Trocar Status"
      >
        🔄
      </button>

      <button
        @click="handleEdit(props.manga)"
        class="btn-icon"
        title="Editar Dados"
      >
        ⚙️
      </button>
    </div>
  </div>
</template>
