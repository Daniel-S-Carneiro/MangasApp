export {};

declare global {
  interface Window {
    api: {
      callPython: (data: any) => Promise<any>;
      selecionarArquivo: () => Promise<string[]>;
      openLink: (url: string) => Promise<void>;
    };
  }
  // Esta linha é CRUCIAL para o erro no <template> sumir
  const api: Window["api"];
}
