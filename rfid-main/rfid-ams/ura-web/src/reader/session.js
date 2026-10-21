import { parseResponse, FrameError, hex } from '../protocol/frame.js';
import { BLOCKED_OPCODES, cmd } from '../protocol/commands.js';
import { ReaderError } from '../protocol/status.js';

/** Baud rates in the order the URA tries them: default twice, then the rest. */
export const PROBE_BAUDS = [115200, 9600, 921600, 19200, 38400, 57600, 230400, 460800];

export class NoResponseError extends Error {
  constructor(kind, tried) {
    super(kind === 'silent'
      ? 'The module sent no bytes at any baud rate. Check power, the UART/USB switch, and especially the RX wire or USB data cable.'
      : 'The module sent bytes but none formed a valid reply. Check baud rate and noise.');
    this.name = 'NoResponseError';
    this.kind = kind; // 'silent' = zero bytes received, 'garbled' = bytes but no valid frame
    this.tried = tried;
  }
}

export class ReaderSession {
  /** @param transport open/close/write/onData/isOpen  @param log {add(entry)} optional */
  constructor(transport, { log = null, probeTimeoutMs = 400, commandTimeoutMs = 1500 } = {}) {
    this.transport = transport;
    this.log = log;
    this.probeTimeoutMs = probeTimeoutMs;
    this.commandTimeoutMs = commandTimeoutMs;
    this.info = null;
    this.baud = null;
    this.writesEnabled = false;
    this._rx = new Uint8Array(0);
    this._waiter = null;
    this._queue = Promise.resolve();
    this._listeners = {};
    this._bytesSeen = 0;
    transport.onData((chunk) => this._onData(chunk));
    transport.onClose?.(() => this._onTransportClosed());
  }

  on(event, fn) { (this._listeners[event] ??= new Set()).add(fn); return () => this._listeners[event].delete(fn); }
  _emit(event, payload) { this._listeners[event]?.forEach((fn) => fn(payload)); }

  _onTransportClosed() {
    this.info = null;
    this.baud = null;
    this._waiter?.reject?.(new Error('disconnected'));
    this._emit('disconnect');
  }

  _onData(chunk) {
    this._bytesSeen += chunk.length;
    this.log?.add({ dir: 'rx', bytes: chunk });
    const merged = new Uint8Array(this._rx.length + chunk.length);
    merged.set(this._rx); merged.set(chunk, this._rx.length);
    this._rx = merged;
    this._drain();
  }

  _drain() {
    for (;;) {
      // resync to the next start byte
      const i = this._rx.indexOf(0xff);
      if (i < 0) { this._rx = new Uint8Array(0); return; }
      if (i > 0) this._rx = this._rx.slice(i);
      let parsed;
      try { parsed = parseResponse(this._rx); } catch (e) {
        if (e instanceof FrameError) { this._rx = this._rx.slice(1); this._emit('frame-error', e); continue; }
        throw e;
      }
      if (!parsed) return;
      this._rx = this._rx.slice(parsed.consumed);
      if (this._waiter && this._waiter.opcode === parsed.frame.opcode) this._waiter.resolve(parsed.frame);
      else this._emit('frame', parsed.frame);
    }
  }

  /** Send one command and wait for its reply. Calls are serialized. */
  send(command, { timeoutMs = this.commandTimeoutMs } = {}) {
    if (BLOCKED_OPCODES.has(command.opcode)) return Promise.reject(new Error('blocked opcode'));
    const run = async () => {
      if (!this.transport.isOpen) throw new Error('disconnected');
      const reply = new Promise((resolve, reject) => {
        const timer = setTimeout(() => { this._waiter = null; reject(new Error(`timeout waiting for opcode 0x${command.opcode.toString(16)}`)); }, timeoutMs);
        this._waiter = {
          opcode: command.opcode,
          resolve: (f) => { clearTimeout(timer); this._waiter = null; resolve(f); },
          reject: (e) => { clearTimeout(timer); this._waiter = null; reject(e); },
        };
      });
      reply.catch(() => {});
      this.log?.add({ dir: 'tx', bytes: command.bytes });
      await this.transport.write(command.bytes);
      const frame = await reply;
      if (frame.status !== 0) throw new ReaderError(frame.status, frame.opcode);
      return command.parse(frame.data);
    };
    const next = this._queue.then(run, run);
    this._queue = next.catch(() => {});
    return next;
  }

  /** Probe baud rates until the version query succeeds, then load identity. */
  async connect({ bauds = PROBE_BAUDS } = {}) {
    const tried = [];
    this._bytesSeen = 0;
    for (const baud of bauds) {
      await this.transport.open(baud);
      tried.push(baud);
      try {
        this.info = await this.send(cmd.version(), { timeoutMs: this.probeTimeoutMs });
        this.baud = baud;
        break;
      } catch (e) {
        if (e instanceof ReaderError) { this.baud = baud; this.info = null; throw e; }
        await this.transport.close();
      }
    }
    if (this.baud === null) throw new NoResponseError(this._bytesSeen === 0 ? 'silent' : 'garbled', tried);
    this.info.serial = await this.send(cmd.serialNumber()).catch(() => null);
    await this.send(cmd.setProtocol()).catch(() => {});
    return this.info;
  }

  async disconnect() { await this.transport.close(); this.baud = null; this.info = null; }
}
