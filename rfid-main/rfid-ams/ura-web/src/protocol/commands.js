import { buildRequest } from './frame.js';

export const OP = {
  VERSION: 0x03, BOOT_FIRMWARE: 0x04, SET_BAUD: 0x06, HW_VERSION: 0x10,
  READ_TAG_MULTIPLE: 0x22, MULTI_PROTOCOL_TAG_OP: 0x2f, GET_TAG_BUFFER: 0x29, CLEAR_TAG_BUFFER: 0x2a,
  GET_READ_POWER: 0x62, GET_PROTOCOL: 0x63, GET_REGION: 0x67, GET_AVAILABLE_REGIONS: 0x71, GET_TEMPERATURE: 0x72,
  GET_PROTOCOL_CONFIG: 0x6b, SET_READ_POWER: 0x92, SET_PROTOCOL: 0x93, SET_REGION: 0x97, SET_PROTOCOL_CONFIG: 0x9b, SET_READER_CONFIG: 0x9a,
  WRITE_TAG_EPC: 0x23, WRITE_TAG_DATA: 0x24, LOCK_TAG: 0x25, READ_TAG_DATA: 0x28,
  // Never sent by this app (see BLOCKED_OPCODES)
  ERASE_FLASH: 0x07, BOOT_BOOTLOADER: 0x09, WRITE_FLASH: 0x0d, MODIFY_FLASH: 0x0f, KILL_TAG: 0x26,
};

/** Opcodes that can brick the module or destroy tags. buildCommand/session.send refuse them. */
export const BLOCKED_OPCODES = new Set([OP.ERASE_FLASH, OP.BOOT_BOOTLOADER, OP.WRITE_FLASH, OP.MODIFY_FLASH, OP.KILL_TAG]);

export const PROTOCOL_GEN2 = 0x05;

export const REGIONS = {
  1: 'NA', 2: 'EU', 3: 'KR', 4: 'IN', 5: 'JP', 6: 'PRC', 7: 'EU2', 8: 'EU3', 9: 'KR2', 10: 'PRC2', 11: 'AU', 12: 'NZ',
  13: 'NA2', 14: 'NA3', 15: 'IS', 16: 'MY', 17: 'ID', 18: 'PH', 19: 'TW', 20: 'MO', 21: 'RU', 22: 'SG', 23: 'JP2',
  24: 'JP3', 25: 'VN', 26: 'TH', 27: 'AR', 28: 'HK', 29: 'BD', 30: 'EU4', 31: 'UNIVERSAL', 32: 'IS2', 33: 'NA4',
  254: 'OPEN_EXTENDED', 255: 'OPEN',
};

function request(opcode, data = []) {
  if (BLOCKED_OPCODES.has(opcode)) throw new Error(`opcode 0x${opcode.toString(16)} is blocked by the safety allow-list`);
  return { opcode, bytes: buildRequest(opcode, data) };
}

const s16 = (hi, lo) => ((hi << 8) | lo) << 16 >> 16;
const be16 = (v) => [(v >> 8) & 0xff, v & 0xff];

export const cmd = {
  version: () => ({ ...request(OP.VERSION), parse: parseVersion }),
  temperature: () => ({ ...request(OP.GET_TEMPERATURE), parse: (d) => (d[0] << 24) >> 24 }),
  serialNumber: () => ({ ...request(OP.HW_VERSION, [0x00, 0x40]), parse: parseSerial }),
  getRegion: () => ({ ...request(OP.GET_REGION), parse: (d) => d[0] }),
  setRegion: (id) => ({ ...request(OP.SET_REGION, [id]), parse: () => undefined }),
  availableRegions: () => ({ ...request(OP.GET_AVAILABLE_REGIONS), parse: (d) => Array.from(d) }),
  /** Power values are centi-dBm (2700 = 27.00 dBm). */
  getReadPower: () => ({ ...request(OP.GET_READ_POWER, [0x00]), parse: (d) => s16(d[1], d[2]) }),
  getReadPowerLimits: () => ({ ...request(OP.GET_READ_POWER, [0x01]), parse: (d) => ({ current: s16(d[1], d[2]), max: s16(d[3], d[4]), min: s16(d[5], d[6]) }) }),
  setReadPower: (centiDbm) => ({ ...request(OP.SET_READ_POWER, be16(centiDbm & 0xffff)), parse: () => undefined }),
  setProtocol: (id = PROTOCOL_GEN2) => ({ ...request(OP.SET_PROTOCOL, be16(id)), parse: () => undefined }),
  bootFirmware: () => ({ ...request(OP.BOOT_FIRMWARE), parse: parseVersion }),
};

const ver = (d, o) => `${d[o].toString(16).padStart(2, '0')}.${d[o + 1].toString(16).padStart(2, '0')}.${d[o + 2].toString(16).padStart(2, '0')}.${d[o + 3].toString(16).padStart(2, '0')}`.toUpperCase();

export function parseVersion(d) {
  if (d.length < 20) throw new Error(`version response too short (${d.length} bytes)`);
  const mask = ((d[16] << 24) | (d[17] << 16) | (d[18] << 8) | d[19]) >>> 0;
  const protocols = [];
  for (let i = 0; i < 32; i++) if (mask & (1 << i)) protocols.push(i + 1);
  return { bootloader: ver(d, 0), hardware: ver(d, 4), firmwareDate: ver(d, 8), firmware: ver(d, 12), protocols };
}

function parseSerial(d) {
  const n = d[3];
  return String.fromCharCode(...d.slice(4, 4 + n));
}

// ---------------------------------------------------------------------------------------------
// Gen2 settings and tag memory. Payload layouts come from the decompiled MercuryAPI and are
// UNVERIFIED on hardware until Task 11 passes; every write is also followed by a read-back check.
// ---------------------------------------------------------------------------------------------
export const GEN2 = { SESSION: 0, TARGET: 1, ENCODING: 2, TARI: 17 };
export const BANK = { RESERVED: 0, EPC: 1, TID: 2, USER: 3 };
export const TARGETS = { A: [1, 0], B: [1, 1], AB: [0, 0], BA: [0, 1] };

const be32 = (v) => [(v >>> 24) & 0xff, (v >>> 16) & 0xff, (v >>> 8) & 0xff, v & 0xff];

export function hexToBytes(hex) {
  const clean = hex.replace(/\s+/g, '');
  if (clean.length === 0 || clean.length % 2 !== 0 || /[^0-9a-f]/i.test(clean)) throw new Error('hex string must have an even number of hex digits');
  return Array.from({ length: clean.length / 2 }, (_, i) => parseInt(clean.slice(i * 2, i * 2 + 2), 16));
}

/** Singulation by EPC: [bitLength, ...epc]. Required for every tag operation so we never touch the wrong tag. */
function epcSelector(epcHex) {
  if (!epcHex) throw new Error('an EPC is required: tag operations must target one specific tag');
  const bytes = hexToBytes(epcHex);
  if (bytes.length * 8 > 255) throw new Error('EPC selector longer than 255 bits is not supported');
  return [bytes.length * 8, ...bytes];
}

function checkWords(bytes) {
  if (bytes.length === 0 || bytes.length % 2 !== 0) throw new Error('data must be a whole number of 16-bit words');
}

const gen2Value = (d) => d[2];

export const cmdTag = {
  getGen2: (param) => ({ ...request(OP.GET_PROTOCOL_CONFIG, [PROTOCOL_GEN2, param]), parse: (d) => (param === GEN2.TARGET ? [d[2], d[3]] : gen2Value(d)) }),
  setGen2: (param, values) => ({ ...request(OP.SET_PROTOCOL_CONFIG, [PROTOCOL_GEN2, param, ...[].concat(values)]), parse: () => undefined }),

  writeEpc: ({ epc, newEpc, password = 0, timeoutMs = 1000 }) => {
    const next = hexToBytes(newEpc);
    if (next.length % 2 !== 0 || next.length > 62) throw new Error('new EPC must be 2-62 bytes in whole words');
    return { ...request(OP.WRITE_TAG_EPC, [...be16(timeoutMs), 0x01, ...be32(password), ...epcSelector(epc), ...next]), parse: () => undefined };
  },
  writeData: ({ epc, bank, wordAddress, dataHex, password = 0, timeoutMs = 1000 }) => {
    const data = hexToBytes(dataHex);
    checkWords(data);
    return { ...request(OP.WRITE_TAG_DATA, [...be16(timeoutMs), 0x01, ...be32(wordAddress), bank, ...be32(password), ...epcSelector(epc), ...data]), parse: () => undefined };
  },
  /** Reads `wordCount` 16-bit words. Response data starts with a 3-byte echo (option + metadata flags); the rest is memory. */
  readData: ({ epc, bank, wordAddress, wordCount, password = 0, timeoutMs = 1000 }) => ({
    ...request(OP.READ_TAG_DATA, [...be16(timeoutMs), 0x11, 0x00, 0x00, bank, ...be32(wordAddress), wordCount, ...be32(password), ...epcSelector(epc)]),
    parse: (d) => Array.from(d.slice(3), (b) => b.toString(16).padStart(2, '0')).join('').toUpperCase(),
  }),
  lock: ({ epc, area, locked, password, timeoutMs = 1000 }) => {
    const { mask, action } = lockMaskAction(area, locked);
    return { ...request(OP.LOCK_TAG, [...be16(timeoutMs), 0x01, ...be32(password), ...be16(mask), ...be16(action), ...epcSelector(epc)]), parse: () => undefined };
  },
};

const LOCK_SHIFT = { kill: 8, access: 6, epc: 4, tid: 2, user: 0 };

/**
 * Gen2 lock payload: 10-bit mask and action, two bits per area (high = lock, low = permalock).
 * We always set both mask bits (so permalock is explicitly left clear) and never request a permanent lock.
 */
export function lockMaskAction(area, locked) {
  if (!(area in LOCK_SHIFT)) throw new Error(`unknown lock area: ${area}`);
  const shift = LOCK_SHIFT[area];
  return { mask: 0b11 << shift, action: (locked ? 0b10 : 0b00) << shift };
}

/** Clamp a requested power (centi-dBm) to the module's reported limits. */
export function clampPower(requested, { min, max }) {
  return Math.min(max, Math.max(min, Math.round(requested)));
}
