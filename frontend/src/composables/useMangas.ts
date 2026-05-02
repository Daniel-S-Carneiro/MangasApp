import { ref } from "vue";

export function useMangas() {
  const listaMangas = ref<any[]>([]);
  const darkTheme = ref(true);

  async function listarMangas() {
    const rawResponse = await window.api.callPython({ action: "list" });
    listaMangas.value = JSON.parse(rawResponse);
  }

  async function mudarStatus(id: number, atual: string) {
    const ordem = ["Lendo", "Concluído", "Pausado"];
    const novo = ordem[(ordem.indexOf(atual) + 1) % ordem.length];
    await window.api.callPython({ action: "update_status", id, status: novo });
    await listarMangas();
  }

  // ... Adicione as outras funções (salvar, excluir, reordenar) aqui

  return {
    listaMangas,
    darkTheme,
    listarMangas,
    mudarStatus,
  };
}
