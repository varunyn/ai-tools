class PCMProcessor extends AudioWorkletProcessor {
  constructor(options) {
    super();
    this.minAudioLevel = options?.processorOptions?.minAudioLevel ?? 0.005;
  }

  process(inputs) {
    const input = inputs[0];
    if (!input || input.length === 0) {
      return true;
    }

    const channel = input[0];
    if (!channel || channel.length === 0) {
      return true;
    }

    let sum = 0;
    let hasAudio = false;
    const pcm = new Int16Array(channel.length);

    for (let i = 0; i < channel.length; i += 1) {
      const sample = channel[i];
      const absValue = Math.abs(sample);
      sum += absValue;
      if (!hasAudio && absValue > this.minAudioLevel) {
        hasAudio = true;
      }

      const clamped = Math.max(-1, Math.min(1, sample));
      pcm[i] = clamped < 0 ? clamped * 0x8000 : clamped * 0x7fff;
    }

    const level = sum / channel.length;

    if (hasAudio) {
      this.port.postMessage(
        {
          level,
          hasAudio,
          audioBuffer: pcm.buffer,
        },
        [pcm.buffer]
      );
    } else {
      this.port.postMessage({ level, hasAudio: false });
    }

    return true;
  }
}

registerProcessor("pcm-processor", PCMProcessor);
