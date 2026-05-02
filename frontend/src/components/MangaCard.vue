<script setup>
defineProps(["manga"]);
defineEmits(["dragstart", "drop", "dragend"]);
// Lógica de computed para a classe de status aqui
</script>

<template>
  <div
    class="card"
    draggable="true"
    @dragstart="$emit('dragstart')"
    @drop="$emit('drop')"
    @dragover.prevent
    @dragend="$emit('dragend')"
  >
    <div :class="['status-tag', statusClass]">
      {{ manga.status }}
    </div>
    <img :src="manga.capa ? `./img/${manga.capa}` : './default.jpg'" />
    <h3>{{ manga.nome_pt }}</h3>
    <!-- Restante do HTML do card -->
  </div>
</template>
