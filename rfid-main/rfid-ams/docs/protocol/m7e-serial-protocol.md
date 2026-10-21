# M7E serial protocol (from MercuryAPI 1.37.3.29 SerialReader.cs, decompiled with ilspycmd)
Request : FF | LEN(data bytes after opcode) | OPCODE | DATA... | CRC16(BE)
Response: FF | LEN | OPCODE | STATUS(2, BE; 0x0000 ok) | DATA... | CRC16(BE)
CRC: CRC-16 poly 0x1021, init 0xFFFF, bitwise-augmented (no final zero append); computed over LEN, OPCODE, DATA (response: LEN..end of data). Verified: [00 03] -> 1D0C.
Opcodes: 03 version, 04 boot fw, 06 set baud(u32), 09 boot bootloader, 0C current program, 10 hw version/serial,
 22 read tag multiple, 24 write tag data, 25 lock, 26 kill, 28 read tag data, 29 get tag buffer, 2A clear tag buffer, 2D block write, 2E block permalock,
 2F stop/streaming, 61 get ant cfg, 62 get read power, 63 get protocol, 64 get write power, 65 get freq hop, 66 get gpio, 67 get region,
 68 get power mode, 69 get user mode, 6C reader stats, 70 avail protocols, 71 avail regions, 72 temperature,
 91 set ant, 92 set read power, 93 set protocol, 94 set write power, 95 set freq hop, 97 set region/LBT/dwell, 9A set reader cfg, 9D user profile.
Baud probe order: 115200 (x2), then 9600, 921600, 19200, 38400, 57600, 230400, 460800. Default 115200.
Regions: NA=1 EU=2 KR=3 IN=4 JP=5 PRC=6 EU3=8 AU=11 NZ=12 ... UNIVERSAL=31 OPEN=255. Gen2 protocol id=5.
Streaming reads: responses with opcode 0x22/0x2F; autonomous mode -> opcode 0x9D.
Source: scratchpad/src_mercury/out/ThingMagic/SerialReader.cs (12.7k lines)

## Additional findings (second pass)
Version response (opcode 03) data: bootloader[4], hardware[4], fwDate[4], firmware[4], protocolBitmask u32 (bit i => protocol id i+1; Gen2 = id 5).
Tag record metadata order (flags u16 sent in streaming start): READCOUNT 0x01 (u8), RSSI 0x02 (s8), ANTENNA 0x04 (u8), FREQUENCY 0x08 (u24 kHz),
 TIMESTAMP 0x10 (u32 ms), PHASE 0x20 (u16), PROTOCOL 0x40 (u8), DATA 0x80 (u16 bitlen + bytes; bit15 = error), GPIO 0x100 (u8), GEN2_Q 0x200, GEN2_LF 0x400, GEN2_TARGET 0x800, BRAND_ID 0x1000, TAGTYPE 0x2000 (EBV).
 Then tag data: u16 EPC bit length, Gen2 PC word (2B, +XPC if bit set), EPC bytes, EPC CRC16 (2B).
Streaming start: 2F | 0000 | 01 | 22 ... ; stop: 2F ... ; autonomous = 0x9D. Embedded memory-bank data: nibble hdr (bank<<4|err), word count, data.
Gen2 tag ops: 23 write EPC, 24 write data, 25 lock, 26 kill, 28 read data, 2D block write. Banks: 0 reserved,1 EPC,2 TID,3 USER.
Gen2 config via 6B (get)/9B (set): [proto=5, param]. Session S0-S3, Target A/B/AB/BA, Tari 25/12.5/6.25us, BLF 250/320/640, encoding FM0/M2/M4/M8.
Temperature: opcode 72 -> s8 degC. Serial number via 10 (hw version) option 0 flags 0x40.
Streaming/write/lock exact payload bytes are NOT yet cross-verified: verify against SparkFun Arduino library + hardware.
