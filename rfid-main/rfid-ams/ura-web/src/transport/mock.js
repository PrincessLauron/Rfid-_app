import { buildResponse, parseResponse } from '../protocol/frame.js';

/**
 * Scripted fake reader implementing the transport interface:
 *   open(baud), close(), write(bytes), onData(cb), isOpen
 * `handlers` maps opcode -> (data) => Uint8Array of response data, or { status, data }.
 * The mock only answers when opened at `answerBaud`; otherwise it stays silent (like a baud mismatch).
 */
export class MockReader {
  constructor({ answerBaud = 115200, handlers = {} } = {}) {
    this.answerBaud = answerBaud;
    this.handlers = handlers;
    this.isOpen = false;
    this.baud = null;
    this.openedAt = [];
    this.written = [];
    this._cb = null;
    this._closeCb = null;
  }
  async open(baud) { this.isOpen = true; this.baud = baud; this.openedAt.push(baud); }
  async close() { this.isOpen = false; }
  onData(cb) { this._cb = cb; }
  onClose(cb) { this._closeCb = cb; }
  /** Simulate the USB cable being pulled. */
  unplug() { this.isOpen = false; this._closeCb?.(); }
  /** Push raw bytes to the host as if the module sent them (used for streaming tests). */
  emit(bytes) { this._cb?.(bytes); }
  async write(bytes) {
    this.written.push(Uint8Array.from(bytes));
    if (this.baud !== this.answerBaud) return;
    const { frame } = parseResponse(rebuildAsResponse(bytes));
    const h = this.handlers[frame.opcode];
    if (!h) return this.emit(buildResponse(frame.opcode, 0x0101, []));
    const out = h(frame.data);
    const { status = 0, data = [] } = out instanceof Uint8Array || Array.isArray(out) ? { data: out } : out;
    queueMicrotask(() => this.emit(buildResponse(frame.opcode, status, data)));
  }
}

// A request is FF LEN OP DATA CRC; reuse the response parser by inserting a zero status.
function rebuildAsResponse(req) {
  const len = req[1];
  return buildResponse(req[2], 0, req.slice(3, 3 + len));
}
