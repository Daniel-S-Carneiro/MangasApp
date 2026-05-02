<script setup lang="ts">
import { ref } from "vue";
const props = defineProps(["isOpen"]);
const emit = defineEmits(["saved"]);

const nomePt = ref("");
const nomeEn = ref("");
const capitulo = ref(1);
const linkManga = ref("");
const statusManga = ref("Lendo");
const capaArquivo = ref("");
const caminhoCompleto = ref("");

async function escolherCapa() {
  // Usamos (window as any) para o TypeScript ignorar a falta da definição de tipo
  const path = await (window as any).api.selecionarArquivo();

  if (path) {
    caminhoCompleto.value = path;
    // Pega só o nome para mostrar na tela (Logística de strings)
    capaArquivo.value = path.split("\\").pop() || path.split("/").pop() || "";
    // console.log("Caminho real capturado pelo Main:", caminhoCompleto.value);
  }
}

async function salvarManga() {
  if (!nomePt.value) return;
  // console.log("Caminho enviado ao Python:", caminhoCompleto.value);
  await window.api.callPython({
    action: "insert",
    nome_pt: nomePt.value,
    nome_en: nomeEn.value,
    capitulo: capitulo.value,
    link: linkManga.value,
    status: statusManga.value,
    capa: capaArquivo.value || "default.jpg",
    caminho_completo: caminhoCompleto.value,
  });
  nomePt.value = "";
  nomeEn.value = "";
  capaArquivo.value = "";
  emit("saved");
}
</script>

<template>
  <div :class="['form-container', { 'form-open': props.isOpen }]">
    <h3>Adicionar Novo Mangá</h3>
    <input v-model="nomePt" placeholder="Nome em Português" />
    <input v-model="nomeEn" placeholder="Nome em Inglês" />
    <input type="number" v-model="capitulo" placeholder="Capítulo atual" />
    <input v-model="linkManga" placeholder="Link do site" />

    <!-- Input de Capa -->
    <div class="file-input-container">
      <button type="button" @click="escolherCapa" class="btn-upload">
        {{ capaArquivo ? "✅ " + capaArquivo : "📁 Escolher Capa" }}
      </button>
    </div>

    <select v-model="statusManga">
      <option value="Lendo">📖 Lendo</option>
      <option value="Concluído">✅ Concluído</option>
      <option value="Pausado">⏳ Pausado</option>
    </select>
    <button @click="salvarManga" class="btn-save">Salvar Mangá</button>
  </div>
</template>
