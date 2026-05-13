<script setup lang="ts">
// Definimos as propriedades que o card recebe
defineProps<{
  manga: any;
  isDragging?: boolean;
}>();

// Definimos os eventos que o card pode disparar para o App.vue
const emit = defineEmits([
  "mudarStatus",
  "abrirModal",
  "dragStart",
  "drop",
  "dragEnd",
]);

const api = (window as any).api;

// Handlers locais para emitir os eventos
const handleStatus = (id: number, status: string) =>
  emit("mudarStatus", id, status);
const handleEdit = (manga: any) => emit("abrirModal", manga);
</script>

<template>
  <div
    class="card"
    :class="{ dragging: isDragging }"
    draggable="true"
    @dragstart="emit('dragStart')"
    @dragover.prevent
    @drop="emit('drop')"
    @dragend="emit('dragEnd')"
  >
    <!-- Tag de Status -->
    <div
      :class="[
        'status-tag',
        manga.status
          .toLowerCase()
          .normalize('NFD')
          .replace(/[\u0300-\u036f]/g, '')
          .replace(' ', ''),
      ]"
    >
      {{ manga.status }}
    </div>

    <!-- Imagem com o Protocolo Customizado -->
    <img
      :src="
        manga.capa.startsWith('capa_') || manga.capa.startsWith('manga_')
          ? `capas://${manga.capa}`
          : `./img/${manga.capa}`
      "
      class="capa-manga"
    />

    <h3>{{ manga.nome_pt }}</h3>
    <small>{{ manga.nome_en }}</small>
    <p>
      Capítulo: <strong>{{ manga.capitulo }}</strong>
    </p>

    <!-- Rodapé -->
    <div class="card-footer">
      <a
        :href="manga.link"
        class="btn-ler"
        @click.prevent="api.openLink(manga.link)"
      >
        Ler
      </a>

      <button
        @click="handleStatus(manga.id, manga.status)"
        class="btn-icon"
        title="Trocar Status"
      >
        🔄
      </button>

      <button @click="handleEdit(manga)" class="btn-icon" title="Editar Dados">
        ⚙️
      </button>
    </div>
  </div>
</template>
