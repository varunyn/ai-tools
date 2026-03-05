import { create } from "zustand";

export const useTranscriptionStore = create((set) => ({
  recording: false,
  transcript: "",
  partialTranscript: "",
  audioDevices: [],
  selectedDevice: "",
  audioLevel: 0,
  startupError: "",
  starting: false,

  setRecording: (recording) => set({ recording }),
  setTranscript: (transcript) => set({ transcript }),
  setPartialTranscript: (partialTranscript) => set({ partialTranscript }),
  setAudioDevices: (audioDevices) => set({ audioDevices }),
  setSelectedDevice: (selectedDevice) => set({ selectedDevice }),
  setAudioLevel: (audioLevel) => set({ audioLevel }),
  setStartupError: (startupError) => set({ startupError }),
  setStarting: (starting) => set({ starting }),

  resetTranscripts: () => set({ transcript: "", partialTranscript: "" }),
}));
