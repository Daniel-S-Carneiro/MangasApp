<script setup lang="ts">
import { ref } from "vue";

const feedback = ref("");
const inputNome = ref("");
const itensNoBanco = ref<{ id: number; name: string }[]>([]);

// Função para SALVAR
async function salvarNoBanco() {
  if (!inputNome.value) return;

  try {
    const rawResponse = await window.api.callPython({
      action: "insert",
      name: inputNome.value,
    });

    const response = JSON.parse(rawResponse);
    feedback.value = `Sucesso: ${response.message}`;
    inputNome.value = ""; // Limpa o campo
    listarDoBanco(); // Atualiza a lista automaticamente
  } catch (error) {
    feedback.value = `Erro ao salvar: ${error}`;
  }
}

// Função para LISTAR
async function listarDoBanco() {
  try {
    const rawResponse = await window.api.callPython({
      action: "list",
    });

    itensNoBanco.value = JSON.parse(rawResponse);
    feedback.value = "Lista atualizada!";
  } catch (error) {
    feedback.value = `Erro ao listar: ${error}`;
  }
}
</script>

<template>
  <div style="padding: 20px; font-family: sans-serif">
    <h1>Electron + Vue + Python + SQLite</h1>

    <div style="margin-bottom: 20px">
      <input v-model="inputNome" placeholder="Digite um nome" />
      <button @click="salvarNoBanco">Salvar no SQLite</button>
    </div>

    <button @click="listarDoBanco">Atualizar Lista</button>

    <p><strong>Status:</strong> {{ feedback }}</p>

    <hr />

    <h3>Itens no Banco:</h3>
    <ul>
      <li v-for="item in itensNoBanco" :key="item.id">
        ID: {{ item.id }} - Nome: {{ item.name }}
      </li>
    </ul>
  </div>
</template>
