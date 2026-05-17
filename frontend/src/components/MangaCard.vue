<script setup lang="ts">
import { ref, onMounted, watch } from "vue";

const props = defineProps<{
  manga: {
    id: number;
    nome_pt: string;
    nome_en: string;
    capitulo: number;
    link: string;
    capa: string;
    status: string;
  };
  isDragging?: boolean;
  draggable?: boolean;
}>();

const emit = defineEmits([
  "mudarStatus",
  "abrirModal",
  "dragStart",
  "drop",
  "dragEnd",
]);

const api = (window as any).api;
const capaSrc = ref("./img/default.jpg");

const carregarCapa = async () => {
  if (!props.manga.capa || props.manga.capa === "default.jpg") {
    capaSrc.value = "./img/default.jpg";
    return;
  }

  if (
    props.manga.capa.startsWith("capa_") ||
    props.manga.capa.startsWith("manga_")
  ) {
    try {
      const res = await api.getCapaBase64(props.manga.capa);
      capaSrc.value = res || "./img/default.jpg";
    } catch (error) {
      console.error("Erro ao buscar Base64 da capa:", error);
      capaSrc.value = "./img/default.jpg";
    }
  } else {
    capaSrc.value = `./img/${props.manga.capa}`;
  }
};

onMounted(carregarCapa);

watch(() => props.manga.capa, carregarCapa);
watch(() => props.manga, carregarCapa, { deep: true });

const handleStatus = (id: number, status: string) =>
  emit("mudarStatus", id, status);
const handleEdit = (manga: any) => emit("abrirModal", manga);
</script>

<template>
  <div
    :class="['card', { dragging: props.isDragging }]"
    :draggable="props.draggable && props.manga.id !== undefined"
    @dragstart="props.manga.id !== undefined ? emit('dragStart') : null"
    @dragover.prevent
    @drop="props.manga.id !== undefined ? emit('drop') : null"
    @dragend="emit('dragEnd')"
  >
    <div
      :class="[
        'status-tag',
        props.manga.status.toLowerCase().includes('lendo') ? 'lendo' : '',
        props.manga.status.toLowerCase().includes('conclu') ? 'concluido' : '',
        props.manga.status.toLowerCase().includes('pausado') ? 'pausado' : '',
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

<style scoped>
.card {
  background: var(--card);
  border-radius: 8px;
  overflow: hidden;
  position: relative;
  display: flex;
  flex-direction: column;
  border: 1px solid var(--border);
  cursor: grab;
  transition:
    transform 0.2s,
    box-shadow 0.2s;
}

.card:active {
  cursor: grabbing;
}

.card.dragging {
  opacity: 0.5;
  transform: rotate(3deg) scale(1.05);
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.4);
  border: 2px dashed #00b894;
}

.capa-manga {
  width: 100%;
  height: 320px;
  object-fit: cover;
}

.info-container {
  display: flex;
  flex-direction: column;
}

.card h3 {
  padding: 10px 15px 0;
  font-size: 1.1em;
  color: var(--text);
}

.card small {
  display: block;
  padding: 0 15px;
  color: #888;
}

.card p {
  padding: 10px 15px;
  color: var(--text);
}

.card-footer {
  padding: 12px;
  margin-top: auto;
  display: flex;
  gap: 6px;
}

/* --- Tags de Status Internas --- */
.status-tag {
  position: absolute;
  top: 10px;
  left: 10px;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 10px;
  font-weight: bold;
  z-index: 5;
  color: white;
}

.status-tag.lendo {
  background: #0099ff;
}

.status-tag.concluido {
  background: #2ecc71;
}

.status-tag.pausado {
  background: #f1c40f;
  color: black;
}

/* --- Botões do Card --- */
.btn-ler {
  flex: 4;
  background: #0099ff;
  color: white;
  text-decoration: none;
  text-align: center;
  padding: 10px 0;
  border-radius: 6px;
  font-weight: bold;
  font-size: 1.1em;
  cursor: pointer;
  border: none;
}

.btn-icon {
  flex: 1;
  background: var(--input-bg);
  border: 1px solid var(--border);
  color: var(--text);
  border-radius: 4px;
  cursor: pointer;
  font-size: 1.3em;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 6px;
}
</style>
