export class Recorder {
  constructor(onUpdate, onDone, onError) {
    this.onUpdate = onUpdate;
    this.onDone = onDone;
    this.onError = onError;
    this.active = false;
  }
  async start() {
    if (this.active) return;
    this.active = true;
    this.parts = [];
    this.rate = 0;
    this.finishSample = null;
    try {
      if (!navigator.mediaDevices?.getUserMedia)
        throw new Error(
          "Mikrofonaufnahme ist hier nicht verfügbar. Bitte localhost und einen aktuellen Browser verwenden.",
        );
      this.stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          echoCancellation: false,
          noiseSuppression: false,
          autoGainControl: false,
        },
      });
      this.settings = this.stream.getAudioTracks()[0].getSettings();
      this.context = new AudioContext();
      await this.context.resume();
      this.rate = this.context.sampleRate;
      await this.context.audioWorklet.addModule("/audio-worklet.js");
      if (!this.active) {
        await this.cleanup();
        return;
      }
      this.node = new AudioWorkletNode(this.context, "eot-capture");
      this.source = this.context.createMediaStreamSource(this.stream);
      this.node.port.onmessage = async ({ data }) => {
        if (data.type === "samples") {
          this.parts.push(data.samples);
          let sum = 0;
          for (const n of data.samples) sum += n * n;
          this.onUpdate({
            seconds: this.parts.reduce((n, a) => n + a.length, 0) / this.rate,
            level: Math.sqrt(sum / data.samples.length),
            tail: this.finishSample !== null,
          });
        }
        if (data.type === "finish-mark") this.finishSample = data.sample;
        if (data.type === "limit") {
          await this.cleanup();
          this.onError(
            new Error(
              "Aufnahmelimit erreicht. Bitte die Karte erneut aufnehmen.",
            ),
          );
        }
        if (data.type === "done") {
          const count = this.parts.reduce((n, a) => n + a.length, 0);
          if (count !== data.totalSamples) {
            await this.cleanup();
            this.onError(
              new Error(
                "Unvollständige Audioübertragung. Bitte erneut aufnehmen.",
              ),
            );
            return;
          }
          const samples = new Float32Array(count);
          let offset = 0;
          for (const part of this.parts) {
            samples.set(part, offset);
            offset += part.length;
          }
          const metadata = {
            browser: navigator.userAgent,
            source_sample_rate: this.rate,
            settings: this.settings,
            finish_click_sample: this.finishSample,
            recorded_samples: count,
            tail_seconds: 6,
          };
          const blob = wav(samples, this.rate);
          await this.cleanup();
          this.onDone(blob, metadata);
        }
      };
      this.source.connect(this.node);
      this.node.connect(this.context.destination);
    } catch (error) {
      await this.cleanup();
      this.onError(error);
    }
  }
  finish() {
    if (this.node && this.active && this.finishSample === null)
      this.node.port.postMessage({ type: "finish", seconds: 6 });
  }
  async abort() {
    this.node?.port.postMessage({ type: "abort" });
    await this.cleanup();
  }
  async cleanup() {
    this.active = false;
    this.stream?.getTracks().forEach((track) => track.stop());
    this.source?.disconnect();
    this.node?.disconnect();
    if (this.context && this.context.state !== "closed")
      await this.context.close();
  }
}

export function wav(samples, rate) {
  const buffer = new ArrayBuffer(44 + samples.length * 2),
    view = new DataView(buffer);
  function text(at, value) {
    for (let i = 0; i < value.length; i++)
      view.setUint8(at + i, value.charCodeAt(i));
  }
  text(0, "RIFF");
  view.setUint32(4, buffer.byteLength - 8, true);
  text(8, "WAVE");
  text(12, "fmt ");
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true);
  view.setUint16(22, 1, true);
  view.setUint32(24, rate, true);
  view.setUint32(28, rate * 2, true);
  view.setUint16(32, 2, true);
  view.setUint16(34, 16, true);
  text(36, "data");
  view.setUint32(40, samples.length * 2, true);
  for (let i = 0; i < samples.length; i++) {
    const x = Math.max(-1, Math.min(1, samples[i]));
    view.setInt16(44 + 2 * i, Math.round(x < 0 ? x * 32768 : x * 32767), true);
  }
  return new Blob([buffer], { type: "audio/wav" });
}
