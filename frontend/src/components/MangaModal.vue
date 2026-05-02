<script setup lang="ts">
const props = defineProps(["manga", "isOpen"]);
const emit = defineEmits(["close", "save", "delete"]);

async function salvar() {
  await window.api.callPython({
    action: "update_full",
    id: props.manga.id,
    capitulo: props.manga.capitulo,
    link: props.manga.link,
  });
  emit("save");
}

async function excluir() {
  await window.api.callPython({ action: "delete", id: props.manga.id });
  emit("delete");
}
</script>

<template>
  <div v-if="props.isOpen" class="modal-overlay">
    <div class="modal-card">
      <h2>Configurar:</h2>
      <h3 style="margin-bottom: 20px; color: #888">
        {{ props.manga?.nome_pt }}
      </h3>

      <div class="form-group" v-if="props.manga">
        <label>Capítulo Atual</label>
        <input v-model.number="props.manga.capitulo" type="number" />

        <label>Link de Leitura</label>
        <input v-model="props.manga.link" type="text" />

        <div class="modal-buttons">
          <button class="btn-save" @click="salvar">Salvar Alterações</button>
          <button class="btn-delete" @click="excluir">🗑️ Excluir Mangá</button>
          <button class="btn-cancel" @click="emit('close')">Cancelar</button>
        </div>
      </div>
    </div>
  </div>
</template>
