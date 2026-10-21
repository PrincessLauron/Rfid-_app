import { crc16 } from './crc.js';

export class FrameError extends Error {
  constructor(message, kind) { super(message); this.name = 'FrameError'; this.kind = kind; }
}

/** Request: FF | LEN | OPCODE | DATA... | CRC16(BE). LEN counts DATA bytes only. */
export function buildRequest(opcode, data = []) {
  if (data.length > 250) throw new FrameError('payload too large', 'too-large');
  const body = [data.length, opcode, ...data];
  const crc = crc16(body);
  return Uint8Array.from([0xff, ...body, crc >> 8, crc & 0xff]);
}

/**
 * Try to parse one response frame at the start of `buf`.
 * Response: FF | LEN | OPCODE | STATUS(2,BE) | DATA(LEN bytes) | CRC16(BE).
 * Returns { frame, consumed } or null when more bytes are needed.
 * Throws FrameError('no-sof' | 'crc') for garbage.
 */
export function parseResponse(buf) {
  if (buf.length === 0) return null;
  if (buf[0] !== 0xff) throw new FrameError('start byte 0xFF not found', 'no-sof');
  if (buf.length < 2) return null;
  const len = buf[1];
  const total = 1 + 1 + 1 + 2 + len + 2;
  if (buf.length < total) return null;
  const crcExpected = crc16(buf.subarray(1, total - 2));
  const crcActual = (buf[total - 2] << 8) | buf[total - 1];
  if (crcExpected !== crcActual) throw new FrameError('CRC mismatch', 'crc');
  return {
    frame: {
      opcode: buf[2],
      status: (buf[3] << 8) | buf[4],
      data: buf.slice(5, 5 + len),
    },
    consumed: total,
  };
}

/** Build a response (used by the mock reader and tests). */
export function buildResponse(opcode, status, data = []) {
  const body = [data.length, opcode, status >> 8, status & 0xff, ...data];
  const crc = crc16(body);
  return Uint8Array.from([0xff, ...body, crc >> 8, crc & 0xff]);
}

export const hex = (bytes) => Array.from(bytes, (b) => b.toString(16).padStart(2, '0')).join(' ').toUpperCase();
export const fromHex = (s) => Uint8Array.from(s.trim().split(/\s+/).filter(Boolean).map((h) => parseInt(h, 16)));
