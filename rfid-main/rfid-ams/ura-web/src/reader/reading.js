import { buildRequest } from '../protocol/frame.js';
import { OP } from '../protocol/commands.js';
import { parseTagRecord } from '../protocol/tagrecord.js';

// UNVERIFIED until Task 11: the bytes SparkFun's library sends to start/stop continuous reading.
export const START_STREAM = [0x00, 0x00, 0x01, 0x22, 0x00, 0x00, 0x05, 0x07, 0x22, 0x10, 0x00, 0x1b, 0x03, 0xe8, 0x01, 0xff];
export const STOP_STREAM = [0x00, 0x00, 0x02];
/** Offsets inside frame.data (= frame bytes 8 and 11): metadata flags (u16) and the first tag record. */
export const STREAM_LAYOUT = { flagsAt: 3, recordAt: 6 };
export const STREAM_OPCODE = 0x22;

const ackCommand = (data) => ({ opcode: OP.MULTI_PROTOCOL_TAG_OP, bytes: buildRequest(OP.MULTI_PROTOCOL_TAG_OP, data), parse: () => undefined });

/** Turn one unsolicited frame into a tag, or null if it is a keep-alive/status/garbage frame. */
export function decodeStreamFrame(frame) {
  const { flagsAt, recordAt } = STREAM_LAYOUT;
  if (frame.opcode !== STREAM_OPCODE || frame.status !== 0 || frame.data.length < recordAt + 6) return null;
  const flags = (frame.data[flagsAt] << 8) | frame.data[flagsAt + 1];
  try { return parseTagRecord(frame.data, recordAt, flags).tag; } catch { return null; }
}

export class TagReader {
  constructor(session) {
    this.session = session;
    this.running = false;
    this._off = null;
    this._listeners = new Set();
  }
  onTag(fn) { this._listeners.add(fn); return () => this._listeners.delete(fn); }

  async start() {
    if (this.running) return;
    this._off = this.session.on('frame', (frame) => {
      const tag = decodeStreamFrame(frame);
      if (tag) this._listeners.forEach((fn) => fn(tag));
    });
    this.running = true;
    try { await this.session.send(ackCommand(START_STREAM)); } catch (e) { this._cleanup(); throw e; }
  }

  async stop() {
    if (!this.running) return;
    this._cleanup();
    await this.session.send(ackCommand(STOP_STREAM)).catch(() => {});
  }

  /** "Read once": run the stream for a fixed window, then stop. */
  async readFor(ms) {
    await this.start();
    await new Promise((r) => setTimeout(r, ms));
    await this.stop();
  }

  _cleanup() { this.running = false; this._off?.(); this._off = null; }
}

const MAX_ROWS = 5000;

/** Aggregates reads by EPC. */
export class TagTable {
  constructor() { this.rows = new Map(); this.dropped = 0; }
  add(tag, now = Date.now()) {
    let row = this.rows.get(tag.epc);
    if (!row) {
      if (this.rows.size >= MAX_ROWS) { this.dropped++; return; }
      row = { epc: tag.epc, count: 0, firstSeen: now, bestRssi: -Infinity };
      this.rows.set(tag.epc, row);
    }
    row.count += tag.readCount ?? 1;
    if (tag.rssi !== undefined) { row.rssi = tag.rssi; row.bestRssi = Math.max(row.bestRssi, tag.rssi); }
    if (tag.antenna !== undefined) row.antenna = tag.antenna;
    if (tag.frequencyKhz !== undefined) row.frequencyKhz = tag.frequencyKhz;
    row.lastSeen = now;
  }
  list() { return [...this.rows.values()].sort((a, b) => b.lastSeen - a.lastSeen); }
  clear() { this.rows.clear(); this.dropped = 0; }
  toCsv() {
    const head = 'epc,count,rssi_dbm,best_rssi_dbm,antenna,frequency_khz,first_seen,last_seen';
    const lines = this.list().map((r) => [r.epc, r.count, r.rssi ?? '', Number.isFinite(r.bestRssi) ? r.bestRssi : '', r.antenna ?? '', r.frequencyKhz ?? '', new Date(r.firstSeen).toISOString(), new Date(r.lastSeen).toISOString()].join(','));
    return [head, ...lines].join('\n') + '\n';
  }
}
