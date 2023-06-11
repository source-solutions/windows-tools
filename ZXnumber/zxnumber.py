#!/usr/bin/env python3

from math import *
import sys
import argparse
import re

class ZXNumber:
    NEAREST = 0
    DOWN = 1
    UP = 2
    
    # ZXNumber constructor. The input can be either an int, a float or
    # a sequence of byte values.
    #
    # If the input is an integer, the value is stored as an
    # integer. If the value is too large it is converted to a float.
    # Example: ZXNumber(123)
    #
    # If the input is a float it is stored as a float. If the value is
    # too large or too small, an exception is raised.
    # Example: ZXNumber(3.14)
    # 
    # Zero is always stored as an integer
    #
    # If input is a sequence of byte values it is interpreted as a
    # literal as used by calculator opcode 0x34. If raw is set
    # to True, it is interpreted as the internal 5 byte value.
    # Example: ZXNumber( [0xf1,0x49,0x0F,0xDA,0xA2] ) (pi/2)
    #          ZXNumber( [0x81,0x49,0x0F,0xDA,0xA2], raw=True) (pi/2)
    #
    def __init__(self, value, **kwargs):
        if isinstance(value, int):
            self.data = _convert_from_int(value)
        elif isinstance(value, float):
            self.data = _convert_from_float(value)
        else:
            if kwargs.get('raw', False):
                assert(len(value) == 5)
                self.data = tuple(value)
            else:
                self.data = _decode_literal(value)
            if self.data[0] == 0:
                # Some sanity checks
                assert(self.data[1] == 0 or self.data[1] == 0xff)
                assert(self.data[4] == 0)

    # Returns a new ZXNumber object with the int value converted to
    # floating point. If it already is a floating point, a copy of
    # the number is returned.
    def to_float(self):
        if self.is_float():
            return ZXNumber(self.data, raw = True)
        else:
            return ZXNumber(float(self.int_value()))

    # Returns the value either as an int or a float
    def value(self):
        if self.is_int():
            return self.int_value()
        else:
            return self.float_value()

    # Returns True if the number is an int
    def is_int(self):
        return self.data[0] == 0

    # Returns the int value if it is an int. Will fail if the number
    # is not an integer.
    def int_value(self):
        assert(self.is_int())
        value = self.data[2] | (self.data[3] << 8)
        if self.data[1] == 0xff:
            value = (-value) & 0xffff
        return value

    # Returns True if the number is a float
    def is_float(self):
        return self.data[0] != 0

    # Returns the sign, exponent and mantissa. Will fail if the number
    # is not a float.
    # The sign is either -1 or 1, the exponent is adjusted for bias and
    # the mantissa is an integer between 0x80000000 and 0xffffffff.
    def float_components(self):
        assert(self.is_float())
        exponent = self.data[0] - 0x81
        mantissa = \
            (self.data[1]<<24) | \
            (self.data[2]<<16) | \
            (self.data[3]<<8) | \
            (self.data[4])
        sign_bit = mantissa >> 31
        mantissa |= 0x80000000
        sign = 1-sign_bit*2
        return sign,exponent,mantissa

    # Returns the float value if it is a float. Will fail if the number
    # is not a float.
    def float_value(self):
        sign,exponent,mantissa = self.float_components()
        return sign * pow(2,exponent) * mantissa / 0x80000000

    # Enocdes the number as a literal with the selected precision
    # (from 1 to 4). Will fail if the number is not a float.
    def _encode_literal_nearest(self, precision):
        assert(precision >= 1 and precision <= 4)
        assert(self.is_float())

        # In most cases the first bit of the mantissa that is omitted
        # can be used for rounding, but not when all bits in the
        # encoded mantissa are 1. Instead this function just rounds
        # both up and down and uses the nearest one.
        
        # Get encoded values for rounding up and down
        encoded_down = self.encode_literal(precision, rounding = ZXNumber.DOWN)
        encoded_up = self.encode_literal(precision, rounding = ZXNumber.UP)

        # Get the values after encoding
        value_down = ZXNumber(encoded_down).float_value()
        value_up = ZXNumber(encoded_up).float_value()

        # Find the rounding errors
        error_down = abs(value_down - self.float_value())
        error_up = abs(value_up - self.float_value())

        # Select the one with the smallest error
        if error_down < error_up:
            return encoded_down
        else:
            return encoded_up

    # Encodes the number as a literal with the selected precision and
    # rounding. Precision and rounding is ignored if the number is an
    # integer.
    def encode_literal(self, precision = 4, **kwargs):
        assert(precision >= 1 and precision <= 4)
        
        if self.is_int():
            # ignore precision and rounding for integers
            if self.data[3] == 0:
                return (0x40, 0xb0, self.data[1], self.data[2])
            else:
                return (0x80, 0xb0, self.data[1], self.data[2], self.data[3])
        else:
            rounding = kwargs.get('rounding', ZXNumber.NEAREST)
            assert(rounding == ZXNumber.NEAREST or \
                   rounding == ZXNumber.DOWN or \
                   rounding == ZXNumber.UP)

            # Handle nearest rounding in a separate function
            if rounding == ZXNumber.NEAREST:
                return self._encode_literal_nearest(precision)

            # Calculate the reduced mantissa
            shift = 8*(4-precision)
            sign,exponent,mantissa = self.float_components()
            reduced_mantissa = mantissa >> shift
            mantissa_top_bit = 0x80000000 >> shift
            mantissa_max = 0xffffffff >> shift

            if rounding == ZXNumber.UP and precision < 4:
                if reduced_mantissa == mantissa_max:
                    # No rounding if the exponent will overflow. Also
                    # do not round the number if the exponent will go
                    # from 14 to 15, since this will require an extra
                    # byte for the exponent and you can just as well
                    # use the extra byte for higher precision.
                    if exponent < 126 and exponent != 14:
                        reduced_mantissa = 0
                        exponent += 1
                else:
                    reduced_mantissa += 1

            # Clear implicit top bit 
            encoded_mantissa = reduced_mantissa & (~mantissa_top_bit)

            # Set sign bit
            if sign == -1:
                encoded_mantissa |= mantissa_top_bit

            # Encode exponent
            encoded_exponent = (exponent + 0x81 - 0x50) & 255

            # Create the output
            output = []
            if encoded_exponent > 0x00 and encoded_exponent < 0x40:
                # Encode exponent as one byte
                output.append(encoded_exponent | ((precision-1) << 6) )
            else:
                # Encode exponent as two bytes
                output.append((precision-1) << 6)
                output.append(encoded_exponent)

            # Encode mantissa
            for i in range(precision):
                output.append( (encoded_mantissa >> (8*(precision-i-1))) & 255 )

        return tuple(output)
            
    def __repr__(self):
        if self.is_float():
            return "%.11g (%s)" % (self.float_value(), _hex_str(self.data))
        else:
            return "%d (%s)" % (self.int_value(), _hex_str(self.data))
            

def _convert_from_int(value):
    # If the value is too large, store it as float
    if value < -65535 or value > 65535:
        return _convert_from_float(float(value))

    if value < 0:
        return (0, 0xff, value & 255, (value >> 8) & 255, 0)
    else:
        return (0, 0, value & 255, (value >> 8) & 255, 0)

def _convert_from_float(value):
    # Zero is just stored as 0
    if value == 0:
        return (0,0,0,0,0)
    exponent = int(floor(log2(abs(value))))

    # Just store zero
    if exponent < -128:
        return (0,0,0,0,0)

    if exponent > 126:
        raise Exception("The value %.20g is too large" % value)
    
    # Adjust the mantissa to a number in the range [1,2>
    mantissa = abs(value) / (pow(2,exponent))

    # Convert the mantissa to 1.31 fixed point
    mantissa_scaled = mantissa * (1<<31)
    mantissa_int = int(mantissa_scaled)
    
    # Round the mantissa
    if mantissa_scaled - mantissa_int >= 0.5:
        mantissa_int += 1
        if mantissa_int == 0x100000000:
            # It overflowed, so divide it by 2 and increment the
            # exponent
            mantissa_int //= 2
            exponent += 1
            assert(exponent <= 126)

    # Replace first bit with sign bit
    mantissa_int &= 0x7fffffff
    if value < 0:
        mantissa_int |= 0x80000000

    # Add exponent bias
    exponent_biased = exponent + 0x81
    
    byte_0 = exponent_biased
    byte_1 = (mantissa_int >> 24) & 255
    byte_2 = (mantissa_int >> 16) & 255
    byte_3 = (mantissa_int >> 8) & 255
    byte_4 = (mantissa_int) & 255

    return (byte_0, byte_1, byte_2, byte_3, byte_4)

def _decode_literal(values):
    # Find the number of bytes used for the mantissa
    num_bytes = 1 + ((values[0] & 0xc0) >> 6)

    # Get the exponent
    exponent = values[0] & 0x3f
    
    if exponent == 0:
        # A second byte is needed for the exponent
        exponent = values[1]
        mantissa = values[2:]
    else:
        mantissa = values[1:]

    # Adjust exponent, since it is stored with bias of -0x50
    exponent = (exponent + 0x50) & 255

    if len(mantissa) != num_bytes:
        raise Exception("Expected %d byte%s in the mantissa, but it has %d." %
                        (num_bytes, ["s",""][num_bytes == 1], len(mantissa)))
    
    # Calulcate the 5 bytes
    data = (exponent,) + tuple(mantissa) + (0,) * (4-num_bytes)
    assert(len(data) == 5)
    
    return data
    
def _hex_str(values):
    return " ".join(map(lambda x : "%02x" % x, values))
                     
    s = "0x%02x" % values[0]
    for v in values[1:]:
        s += ", 0x%02x" % v
    return s

def _parse_hex_input(input_list):
    input_str = ' '.join(input_list)

    temp = input_str
    output = []
    while len(temp) > 0:
        # Quite liberal hex string matching
        m = re.match('\s*(?:0x|\$|&H)?([a-fA-F0-9]{2})h?\s*,?\s*(.*)', temp)
        if not m:
            raise Exception("Invalid hex string '%s'" % input_str)
        output.append(int(m.group(1),16))
        temp = m.group(2)

    return output
    
# Decode a variable length number
def _decode(args):
    # Get hex values
    hex_values = _parse_hex_input(args.input)

    # Create a number
    number = ZXNumber(hex_values)

    # Print it
    if args.verbose > 0:
        print("Input: %s" % _hex_str(hex_values))
        print(number)
    else:
        print(number.value())

# Decode a raw 5 byte number
def _decode_raw(args):
    # Get hex values
    hex_values = _parse_hex_input(args.input)
    if len(hex_values) != 5:
        raise Exception("Invalid raw number string, the length must be 5")

    # Create a number
    number = ZXNumber(hex_values, raw=True)
    
    # Print it
    if args.verbose > 0:
        print("Input: %s" % _hex_str(hex_values))
        print(number)
    else:
        print(number.value())
    

def _print_encoded_int(number, detailed = False):
    encoded = number.encode_literal()
    encoded_number = ZXNumber(encoded)
    if detailed:
        print("%s (value = %d)" % (_hex_str(encoded), encoded_number.int_value()))
    else:
        print("%s" % _hex_str(encoded))

def _print_encoded_float(number, precision, rounding, detailed = False):
    encoded = number.encode_literal(precision, rounding = rounding)
    encoded_number = ZXNumber(encoded)
    error = (encoded_number.float_value() - number.float_value()) / number.float_value()
    
    if detailed:
        print("%-17s (value = %.11g, error = %.2g%%)" % (
            _hex_str(encoded), encoded_number.value(), error*100.0))
    else:
        print("%s" % _hex_str(encoded))

# Encode a number 
def _encode(args):
    # Get argument expression
    expr = ' '.join(args.input)
    try:
        value = eval(expr)
    except Exception as e:
        raise Exception("Error evaluating '%s': %s" % (expr, e))

    if not isinstance(value, int) and not isinstance(value, float):
        raise Exception("'%s' does not evaluate to an int or a float" % expr)

    number = ZXNumber(value)

    if args.verbose > 0:
        if isinstance(value, int):
            print("Input (int): %d (%s)" % (value, number))
        else:
            print("Input (float): %.20g (%s)" % (value, number))

    if number.is_int():
        _print_encoded_int(number, args.verbose > 0)
    else:
        # If precision is not specified, encode all 4
        if args.precision is None:
            for precision in [4,3,2,1]:
                _print_encoded_float(number, precision,
                                     args.rounding, args.verbose > 0)
        else:
            _print_encoded_float(number, int(args.precision),
                                 args.rounding, args.verbose > 0)

example_text = """
examples:
  Encode 8 (integer):
    %(prog)s 8

  Encode 8.0 (float):
    %(prog)s 8.0

  Encode pi/64 with precision 1:
    %(prog)s -p 1 pi / 64

  Encode sin(1.0) with verbose output rounding down:
    %(prog)s -D -v 'sin(1.0)'

  Encode sqrt(2) with verbose output rounding up:
    %(prog)s -U -v 'sqrt(2)'

  Decode a literal:
    %(prog)s -d '$F1,$49,$0F,$DA,$A2'

  Decode a literal with verbose output:
    %(prog)s -v -d 0x30 0x00

  Decode a raw 5 byte value 
    %(prog)s -r f1 35 04 f3 34
"""

def main():
    ap = argparse.ArgumentParser(
        epilog=example_text,
        formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument('-e', '--encode', dest='func', action='store_const',
                    const=_encode, default=_encode,
                    help='Encode a value (default)')
    ap.add_argument('-d', '--decode', dest='func', action='store_const',
                    const=_decode, default=_encode,
                    help='Decode a constant')
    ap.add_argument('-r', '--decode-raw', dest='func', action='store_const',
                    const=_decode_raw, default=_encode,
                    help='Decode a raw 5 byte value')
    ap.add_argument('-D', '--round-down', dest='rounding', action='store_const',
                    const=ZXNumber.DOWN, default=ZXNumber.NEAREST,
                    help='Round down when encoding a literal')
    ap.add_argument('-U', '--round-up', dest='rounding', action='store_const',
                    const=ZXNumber.UP, default=ZXNumber.NEAREST,
                    help='Round up when encoding a literal')
    ap.add_argument('-p', '--precision', choices=['1','2','3','4'],
                    help='Encoding precision (number of bytes for the mantissa)')
    ap.add_argument('-v', '--verbose', action='count', default=0,
                    help='Verbose mode')
    ap.add_argument('input', nargs='+')

    args = ap.parse_args()

    try:
        args.func(args)
    except Exception as e:
        print(e)
        sys.exit(1)
    
if __name__ == '__main__':
    main()
