/** Web Serial transport (Chrome/Edge). Implements: open(baud), close(), write(bytes), onData(cb), onClose(cb), isOpen. */
export class WebSerialTransport {
  static get supported() { return typeof navigator !== 'undefined' && 'serial' in navigator; }

  /** Shows the browser's port picker. Rejects with NotFoundError if the user cancels. */
  static async request() {
    const port = await navigator.serial.requestPort();
    return new WebSerialTransport(port);
  }

  constructor(port) {
    this.port = port;
    this.isOpen = false;
    this._data = null;
    this._close = null;
    this._reader = null;
    this._loop = null;
    port.addEventListener?.('disconnect', () => this._handleLost());
  }

  onData(cb) { this._data = cb; }
  onClose(cb) { this._close = cb; }

  async open(baud) {
    if (this.isOpen) await this.close();
    await this.port.open({ baudRate: baud, dataBits: 8, stopBits: 1, parity: 'none', flowControl: 'none', bufferSize: 4096 });
    this.isOpen = true;
    this._loop = this._readLoop();
  }

  async _readLoop() {
    this._reader = this.port.readable.getReader();
    try {
      for (;;) {
        const { value, done } = await this._reader.read();
        if (done) break;
        if (value?.length) this._data?.(value);
      }
    } catch {
      this._handleLost(); // device unplugged or fatal read error
    } finally {
      try { this._reader.releaseLock(); } catch { /* already released */ }
    }
  }

  _handleLost() {
    if (!this.isOpen) return;
    this.isOpen = false;
    this._close?.();
  }

  async write(bytes) {
    if (!this.isOpen) throw new Error('port is not open');
    const writer = this.port.writable.getWriter();
    try { await writer.write(bytes); } finally { writer.releaseLock(); }
  }

  async close() {
    const wasOpen = this.isOpen;
    this.isOpen = false;
    try { await this._reader?.cancel(); } catch { /* ignore */ }
    try { await this._loop; } catch { /* ignore */ }
    try { await this.port.close(); } catch { /* ignore */ }
    return wasOpen;
  }
}
