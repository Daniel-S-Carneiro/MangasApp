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
  const path = await (window as any).api.selecionarArquivo();

  if (path) {
    caminhoCompleto.value = path;
    capaArquivo.value = path.split("\\").pop() || path.split("/").pop() || "";
  }
}

async function salvarManga() {
  if (!nomePt.value) return;

  const res = await window.api.callPython({
    action: "insert",
    nome_pt: nomePt.value,
    nome_en: nomeEn.value,
    capitulo: capitulo.value,
    link: linkManga.value,
    status: statusManga.value,
    capa: capaArquivo.value || "default.jpg",
    caminho_completo: caminhoCompleto.value,
  });

  emit("saved", {
    id: res.id,
    nome_pt: nomePt.value,
    nome_en: nomeEn.value,
    capitulo: capitulo.value,
    link: linkManga.value,
    status: statusManga.value,
    capa: res.capa,
  });

  nomePt.value = "";
  nomeEn.value = "";
  capaArquivo.value = "";
}
</script>

<template>
  <div :class="['form-container', { 'form-open': props.isOpen }]">
    <h3>Adicionar Novo Mangá</h3>
    <input v-model="nomePt" placeholder="Nome em Português" />
    <input v-model="nomeEn" placeholder="Nome em Inglês" />
    <input type="number" v-model="capitulo" placeholder="Capítulo atual" />
    <input v-model="linkManga" placeholder="Link do site" />

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

<style scoped>
.form-container {
  display: none;
  background: var(--card);
  padding: 20px;
  border-radius: 8px;
  max-width: 500px;
  margin: 0 auto 30px;
  border: 1px solid var(--border);
  box-sizing: border-box;
}

.form-open {
  display: block;
}

.form-container h3 {
  margin-bottom: 20px;
  font-size: 1.3em;
  text-align: center;
  color: var(--text);
}

.form-container input,
.form-container select {
  width: 100%;
  padding: 10px;
  margin-bottom: 15px;
  border-radius: 4px;
  background: var(--input-bg);
  color: var(--text);
  border: 1px solid var(--border);
  box-sizing: border-box;
  font-size: 1rem;
}

.file-input-container {
  width: 100%;
  margin: 15px 0;
}

/* --- Botões Locais do Formulário --- */
.btn-upload,
.btn-save {
  padding: 10px 15px;
  border-radius: 4px;
  border: none;
  cursor: pointer;
  font-weight: bold;
  font-size: 1rem;
}

.btn-upload {
  width: 100%;
  padding: 12px;
  background-color: #2c2c2c;
  border: 2px dashed #444;
  color: #fff;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
}

.btn-upload:hover {
  border-color: #00ca91;
  background-color: #333;
}

.btn-save {
  width: 100%;
  padding: 12px;
  background: #00b894;
  color: white;
}
.controls {
  display: flex;
  justify-content: center;
  gap: 10px;
  margin-bottom: 20px;
}
</style>
