import { hex } from './protocol/frame.js';

/** Ring buffer of every TX/RX chunk, downloadable as text. */
export class TransportLog {
  constructor(max = 5000) { this.entries = []; this.max = max; this._listeners = new Set(); }
  add({ dir, bytes, note = '' }) {
    this.entries.push({ t: Date.now(), dir, hex: hex(bytes), note });
    if (this.entries.length > this.max) this.entries.splice(0, this.entries.length - this.max);
    this._listeners.forEach((fn) => fn());
  }
  onChange(fn) { this._listeners.add(fn); return () => this._listeners.delete(fn); }
  clear() { this.entries.length = 0; this._listeners.forEach((fn) => fn()); }
  toText() { return this.entries.map((e) => `${new Date(e.t).toISOString()} ${e.dir.toUpperCase()} ${e.hex}${e.note ? '  # ' + e.note : ''}`).join('\n') + '\n'; }
}
