/** Status codes returned in bytes 3-4 of every response. 0x0000 = success. Names from the module's fault table. */
export const STATUS_NAMES = {
  0x0100: 'MSG_WRONG_NUMBER_OF_DATA', 0x0101: 'INVALID_OPCODE', 0x0102: 'UNIMPLEMENTED_OPCODE',
  0x0103: 'MSG_POWER_TOO_HIGH', 0x0104: 'MSG_INVALID_FREQ_RECEIVED', 0x0105: 'MSG_INVALID_PARAMETER_VALUE',
  0x0106: 'MSG_POWER_TOO_LOW', 0x0109: 'UNIMPLEMENTED_FEATURE', 0x010a: 'INVALID_BAUD_RATE',
  0x010b: 'INVALID_REGION', 0x010c: 'INVALID_LICENSE_KEY',
  0x0400: 'NO_TAGS_FOUND', 0x0401: 'NO_PROTOCOL_DEFINED', 0x0402: 'INVALID_PROTOCOL_SPECIFIED',
  0x0404: 'PROTOCOL_NO_DATA_READ', 0x0405: 'AFE_NOT_ON', 0x0406: 'PROTOCOL_WRITE_FAILED',
  0x0407: 'NOT_IMPLEMENTED_FOR_THIS_PROTOCOL', 0x0409: 'PROTOCOL_INVALID_ADDRESS', 0x040a: 'GENERAL_TAG_ERROR',
  0x040b: 'DATA_TOO_LARGE', 0x040e: 'PROTOCOL_KILL_FAILED', 0x0410: 'PROTOCOL_INVALID_EPC',
  0x0411: 'PROTOCOL_INVALID_NUM_DATA', 0x0413: 'PROTOCOL_INVALID_TAG_OP',
  0x0420: 'GEN2_PROTOCOL_OTHER_ERROR', 0x0423: 'GEN2_PROTOCOL_MEMORY_OVERRUN_BAD_PC',
  0x0424: 'GEN2_PROTOCOL_MEMORY_LOCKED', 0x042b: 'GEN2_PROTOCOL_INSUFFICIENT_POWER',
  0x042f: 'GEN2_PROTOCOL_NON_SPECIFIC_ERROR', 0x0430: 'GEN2_PROTOCOL_UNKNOWN_ERROR',
  0x0500: 'AHAL_INVALID_FREQ', 0x0501: 'AHAL_CHANNEL_OCCUPIED', 0x0502: 'AHAL_TRANSMITTER_ON',
  0x0503: 'AHAL_ANTENNA_NOT_CONNECTED', 0x0504: 'AHAL_TEMPERATURE_EXCEED_LIMITS',
  0x0505: 'AHAL_HIGH_RETURN_LOSS', 0x0509: 'IPVOLTAGE_EXCEEDED_LIMITS',
  0x0600: 'TAG_ID_BUFFER_NOT_ENOUGH_TAGS_AVAILABLE', 0x0601: 'TAG_ID_BUFFER_FULL',
  0x7f00: 'SYSTEM_UNKNOWN_ERROR', 0x7f01: 'TM_ASSERT_FAILED',
};

const HINTS = {
  0x0504: 'Module is outside its operating temperature. Lower the read power or add a heatsink, then retry.',
  0x0405: 'RF is off because no region is set. Choose one on the Settings tab.',
  0x0503: 'No antenna detected. Check the antenna connector before transmitting.',
  0x0505: 'High return loss detected. Check the antenna and cable.',
  0x010b: 'The module rejected that region.',
  0x0103: 'Power is above what this module supports.',
  0x0106: 'Power is below what this module supports.',
  0x0424: 'The tag memory is locked. Use the access password or unlock it first.',
};

export class ReaderError extends Error {
  constructor(status, opcode) {
    const name = STATUS_NAMES[status] ?? `UNKNOWN_0x${status.toString(16).padStart(4, '0')}`;
    super(`${name} (status 0x${status.toString(16).padStart(4, '0')}, opcode 0x${opcode.toString(16).padStart(2, '0')})`);
    this.name = 'ReaderError';
    this.status = status;
    this.opcode = opcode;
    this.code = name;
    this.hint = HINTS[status] ?? null;
  }
}
