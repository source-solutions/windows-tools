# ZXNumber

ZXNumber is a tool to encode and decode floating point/integer literals used by the calculator in SE Basic IV.

These numbers are stored in 5 bytes (40 bits). A number can either be a floating point number or an integer.

## Floating point
Floating point numbers are represented with an exponent, a sign bit and a mantissa. The value is ±mantissa × 2<sup>exponent</sup>.

The exponent is 8 bits and has a range from -128 to 126 and is stored in the first byte of the 5 byte number with a bias of 129 ($81). -128 ($80) is stored as $01, 0 ($00) is stored as $81 and 126 ($7e) is stored as $ff. The value 0 is reserved for integers.

The sign bit is stored in top bit of the second byte.

The mantissa is a 1.31 fixed point number in the range $8000000 to $ffffffff (1.0 to 1.999999999534339). It is stored as a big endian number in the last 4 bytes. The top bit is always 1 and is not stored. This bit is instead used for the sign bit.

### Examples

Value | Bytes | Normalized
----- | ----- | ----------
1.0 | `81 00 00 00 00` | +1.0 × 2<sup>0</sup>
-1.0 | `81 80 00 00 00` | -1.0 × 2<sup>0</sup>
pi | `82 49 0f da a2` | +1.570796326734126 × 2<sup>1</sup>
sqrt(6144) | `87 1c c4 70 a0` | +1.224744871258736 × 2<sup>6</sup>

## Integers

Integers in the range -65535 to 65535 can also be stored as integers instead of floating point. The first byte is 0, the second byte is the sign indicator ($00 for positive numbers, $ff for negative numbers). The number is stored as a little endian number in the third and fourth byte and the fifth byte is 0. Negative numbers are stored as two's complement numbers.

Zero is always stored as an integer with all 5 bytes set to 0.

### Examples

Value | Bytes
----  | -----
0 | `00 00 00 00 00`
1000 | `00 00 e8 03 00`
-1000 | `00 ff 18 fc 00`

## Encoded literals

When loading literals in the calculator with the $34 opcode, the number is given as an encoded literal. The encoding makes it possible to store numbers in less than 5 bytes by using 1 to 4 bytes for the mantissa.

To achieve this, the top two bits of the first byte contains the number of bytes to use for the mantissa minus 1. This means that there are only 6 bits left for the exponent so some exponents have to be stored in an extra byte.

The exponent is stored with a bias of -$50 (compared to the exponent stored in the 5 byte value). If this value is less than $01 or larger than $3f, the 6 bits are set to 0 and the exponent is stored in the following byte. This value is also encoded with the -$50 bias. This means that floating point values with exponent from -48 to 14 uses one byte for the exponent and all other, including integers, uses two bytes.

If using less than 4 bytes for the mantissa, the remaining bits in the mantissa are set to 0.

### Examples

Value | Precision | Bytes | Stored value
----- | --------- | ----- | ------------
1.0 | 4 | `f1 00 00 00 00` | 1.0
1.0 | 1 | `31 00` | 1.0
pi | 1 | `32 49` | 3.140625
pi | 2 | `72 49 10` | 3.1416015625
pi | 3 | `b2 49 0f db` | 3.141592741
pi | 4 | `f2 49 0f da a2` | 3.1415926535
-1000 | 3 | `80 b0 ff 18 fc` | -1000
100 | 2 | `40 b0 00 64` | 100
