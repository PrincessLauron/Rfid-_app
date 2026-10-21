/** Metadata flag bits, in the order their fields appear in a tag record. */
export const FLAG = {
  READCOUNT: 0x0001, RSSI: 0x0002, ANTENNA: 0x0004, FREQUENCY: 0x0008, TIMESTAMP: 0x0010, PHASE: 0x0020,
  PROTOCOL: 0x0040, DATA: 0x0080, GPIO: 0x0100, GEN2_Q: 0x0200, GEN2_LF: 0x0400, GEN2_TARGET: 0x0800,
  BRAND_ID: 0x1000, TAGTYPE: 0x2000,
};
export const DEFAULT_FLAGS = FLAG.READCOUNT | FLAG.RSSI | FLAG.ANTENNA | FLAG.FREQUENCY | FLAG.TIMESTAMP | FLAG.PROTOCOL;

const hexOf = (bytes) => Array.from(bytes, (b) => b.toString(16).padStart(2, '0')).join('').toUpperCase();

/**
 * Parse one tag record starting at `offset`. Returns { tag, next }.
 * Throws if the flags include fields this app does not decode (TAGTYPE, BRAND_ID) or the buffer is short.
 */
export function parseTagRecord(buf, offset, flags) {
  if (flags & (FLAG.TAGTYPE | FLAG.BRAND_ID)) throw new Error('TAGTYPE and BRAND_ID metadata are not supported');
  let o = offset;
  const need = (n) => { if (o + n > buf.length) throw new Error('tag record truncated'); };
  const u8 = () => { need(1); return buf[o++]; };
  const u16 = () => { need(2); const v = (buf[o] << 8) | buf[o + 1]; o += 2; return v; };
  const take = (n) => { need(n); const v = buf.slice(o, o + n); o += n; return v; };

  const tag = {};
  let protocol = 0x05;
  if (flags & FLAG.READCOUNT) tag.readCount = u8();
  if (flags & FLAG.RSSI) tag.rssi = (u8() << 24) >> 24;
  if (flags & FLAG.ANTENNA) tag.antenna = u8();
  if (flags & FLAG.FREQUENCY) tag.frequencyKhz = (u8() << 16) | (u8() << 8) | u8();
  if (flags & FLAG.TIMESTAMP) tag.timestampMs = ((u8() << 24) | (u8() << 16) | (u8() << 8) | u8()) >>> 0;
  if (flags & FLAG.PHASE) tag.phase = u16();
  if (flags & FLAG.PROTOCOL) protocol = u8();
  tag.protocol = protocol;
  if (flags & FLAG.DATA) {
    const bits = u16();
    if (bits & 0x8000) { tag.dataError = hexOf(take(2)); } else { tag.data = take((bits + 7) >> 3); }
  }
  if (flags & FLAG.GPIO) tag.gpio = u8();
  if (protocol === 0x05) {
    if (flags & FLAG.GEN2_Q) tag.q = u8();
    if (flags & FLAG.GEN2_LF) tag.linkFrequency = u8();
    if (flags & FLAG.GEN2_TARGET) tag.target = u8();
  }

  const epcBits = u16();
  if (epcBits % 8 !== 0) throw new Error('EPC length not a multiple of 8 bits');
  let epcLen = epcBits / 8;
  if (epcLen >= 2) epcLen -= 2; // trailing EPC CRC
  if (protocol === 0x05) {
    const pc = take(2);
    if (epcLen >= 2) epcLen -= 2;
    tag.pc = hexOf(pc);
    if (pc[0] & 0x02) { // XPC present
      const xpc = take(2);
      epcLen -= 2;
      if (xpc[0] & 0x80) { take(2); epcLen -= 2; }
    }
  }
  if (epcLen < 0) throw new Error('EPC length inconsistent');
  tag.epc = hexOf(take(epcLen));
  tag.epcCrc = hexOf(take(2));
  return { tag, next: o };
}
