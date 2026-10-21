/** CRC-16, polynomial 0x1021, init 0xFFFF, bit-serial "augmented" form used by the M7E (no final zero append). */
export function crc16(bytes) {
  let crc = 0xffff;
  for (const byte of bytes) {
    for (let bit = 0; bit < 8; bit++) {
      const top = crc & 0x8000;
      crc = (crc << 1) & 0xffff;
      if (byte & (0x80 >> bit)) crc |= 1;
      if (top) crc ^= 0x1021;
    }
  }
  return crc;
}
