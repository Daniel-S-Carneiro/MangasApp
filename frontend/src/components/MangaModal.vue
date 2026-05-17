<script setup lang="ts">
import { ref, watch } from "vue";

const props = defineProps<{
  manga: {
    id: number;
    nome_pt: string;
    capitulo: number;
    link: string;
    capa: string;
  } | null;
  isOpen: boolean;
}>();

const emit = defineEmits(["close", "save", "delete"]);

const capitulo = ref(1);
const linkManga = ref("");
const capaArquivo = ref("");
const caminhoCompleto = ref("");

watch(
  () => props.manga,
  (novoManga) => {
    caminhoCompleto.value = "";
    if (novoManga) {
      capitulo.value = novoManga.capitulo;
      linkManga.value = novoManga.link;
      capaArquivo.value = novoManga.capa;
    }
  },
  { immediate: true },
);

async function escolherCapa() {
  const path = await (window as any).api.selecionarArquivo();

  if (path) {
    caminhoCompleto.value = path;
    capaArquivo.value = path.split("\\").pop() || path.split("/").pop() || "";
  }
}

async function salvar() {
  if (!props.manga) return;

  try {
    const responseText = await window.api.callPython({
      action: "update_full",
      id: props.manga.id,
      capitulo: capitulo.value,
      link: linkManga.value,
      capa: props.manga.capa,
      caminho_completo: caminhoCompleto.value,
    });

    const res = JSON.parse(responseText.trim());

    if (res && res.status === "OK") {
      props.manga.capitulo = capitulo.value;
      props.manga.link = linkManga.value;
      props.manga.capa = res.capa;
    }

    emit("save");
  } catch (err) {
    console.error("Erro ao salvar alterações no modal:", err);
  }
}
</script>

<template>
  <div v-if="props.isOpen && props.manga" class="modal-overlay">
    <div class="modal-card">
      <h2>Configurar:</h2>
      <h3 class="manga-title">
        {{ props.manga.nome_pt }}
      </h3>

      <div class="form-group">
        <label>Capítulo Atual</label>
        <input v-model.number="capitulo" type="number" />

        <label>Link de Leitura</label>
        <input v-model="linkManga" type="text" />

        <label>Alterar Capa do Mangá</label>
        <div class="file-input-container">
          <button type="button" @click="escolherCapa" class="btn-upload">
            {{
              caminhoCompleto
                ? "✅ Nova: " + capaArquivo
                : "📁 Escolher Nova Capa"
            }}
          </button>
        </div>

        <div class="modal-buttons">
          <button class="btn-save" @click="salvar">Salvar Alterações</button>
          <button class="btn-delete" @click="emit('delete')">
            🗑️ Excluir Mangá
          </button>
          <button class="btn-cancel" @click="emit('close')">Cancelar</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
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
  -webkit-backdrop-filter: blur(4px);
  backdrop-filter: blur(4px);
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

.modal-card h2 {
  margin-bottom: 15px;
  font-size: 1.4em;
  color: var(--text);
}

.manga-title {
  margin-bottom: 20px;
  color: #888;
  font-size: 1.1em;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-group label {
  display: block;
  font-size: 0.9em;
  color: #888;
  font-weight: bold;
  text-align: left;
}

.form-group input {
  width: 100%;
  padding: 12px;
  border-radius: 4px;
  background: var(--input-bg);
  color: var(--text);
  border: 1px solid var(--border);
  font-size: 1rem;
  box-sizing: border-box;
}

.file-input-container {
  width: 100%;
  margin-bottom: 15px;
}

/* --- Botões Locais do Modal --- */
.btn-upload,
.btn-save,
.btn-delete,
.btn-cancel {
  padding: 10px 15px;
  border-radius: 4px;
  border: none;
  cursor: pointer;
  font-weight: bold;
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

.btn-delete {
  background: #e74c3c;
  color: white;
}

.btn-cancel {
  background: #555;
  color: white;
}

.modal-buttons {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 25px;
}
</style>
