import { ElectronAPI } from "../../electron/preload";

declare global {
  interface Window {
    api: {
      callPython: (data: any) => Promise<string>;
    };
  }
}
