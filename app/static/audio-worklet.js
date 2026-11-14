class Capture extends AudioWorkletProcessor {
  constructor() {
    super();
    this.active = true;
    this.frames = 0;
    this.tailTarget = null;
    this.buffer = new Float32Array(4096);
    this.used = 0;
    this.port.onmessage = ({ data }) => {
      if (data.type === "finish" && this.tailTarget === null) {
        this.tailTarget = this.frames + Math.round(data.seconds * sampleRate);
        this.port.postMessage({ type: "finish-mark", sample: this.frames });
      }
      if (data.type === "abort") this.active = false;
    };
  }
  flush() {
    if (!this.used) return;
    const copy = this.buffer.slice(0, this.used);
    this.port.postMessage({ type: "samples", samples: copy }, [copy.buffer]);
    this.used = 0;
  }
  process(inputs, outputs) {
    for (const output of outputs) for (const channel of output) channel.fill(0);
    if (!this.active) return false;
    const channels = inputs[0];
    if (!channels || !channels.length) return true;
    const length = channels[0].length;
    for (let i = 0; i < length; i++) {
      if (this.tailTarget !== null && this.frames >= this.tailTarget) {
        this.flush();
        this.active = false;
        this.port.postMessage({ type: "done", totalSamples: this.frames });
        return false;
      }
      let sample = 0;
      for (const channel of channels) sample += channel[i] / channels.length;
      this.buffer[this.used++] = sample;
      this.frames++;
      if (this.used === this.buffer.length) this.flush();
    }
    if (this.frames > sampleRate * 85) {
      this.flush();
      this.active = false;
      this.port.postMessage({ type: "limit" });
      return false;
    }
    return true;
  }
}
registerProcessor("eot-capture", Capture);
