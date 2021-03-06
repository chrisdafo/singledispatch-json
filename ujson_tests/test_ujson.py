# From github.com/ultrajson/ultrajson
# Developed by ESN, an Electronic Arts Inc. studio.
# Copyright (c) 2014, Electronic Arts Inc.
# All rights reserved.
# Licensed under The 3-Clause BSD License

import decimal
import sdjson
import math
import re
import sys
from collections import OrderedDict

import pytest
import six
import sd_ujson


def assert_almost_equal(a, b):
	assert round(abs(a - b), 7) == 0


def test_encode_decimal():
	sut = decimal.Decimal("1337.1337")
	encoded = sd_ujson.encode(sut)
	decoded = sd_ujson.decode(encoded)
	assert decoded == 1337.1337


def test_encode_string_conversion():
	test_input = "A string \\ / \b \f \n \r \t </script> &"
	not_html_encoded = '"A string \\\\ \\/ \\b \\f \\n \\r \\t <\\/script> &"'
	html_encoded = (
		'"A string \\\\ \\/ \\b \\f \\n \\r \\t \\u003c\\/script\\u003e \\u0026"'
	)
	not_slashes_escaped = '"A string \\\\ / \\b \\f \\n \\r \\t </script> &"'

	def helper(expected_output, **encode_kwargs):
		if "escape_forward_slashes" not in encode_kwargs:
			encode_kwargs["escape_forward_slashes"] = True,
		output = sd_ujson.encode(test_input, **encode_kwargs)
		assert output == expected_output
		if encode_kwargs.get("escape_forward_slashes", True):
			assert test_input == sdjson.loads(output)
			assert test_input == sd_ujson.decode(output)

	# Default behavior assumes encode_html_chars=False.
	helper(not_html_encoded, ensure_ascii=True)
	helper(not_html_encoded, ensure_ascii=False)

	# Make sure explicit encode_html_chars=False works.
	helper(not_html_encoded, ensure_ascii=True, encode_html_chars=False)
	helper(not_html_encoded, ensure_ascii=False, encode_html_chars=False)

	# Make sure explicit encode_html_chars=True does the encoding.
	helper(html_encoded, ensure_ascii=True, encode_html_chars=True)
	helper(html_encoded, ensure_ascii=False, encode_html_chars=True)

	# Do escape forward slashes if disabled.
	helper(not_slashes_escaped, escape_forward_slashes=False)


def test_write_escaped_string():
	assert "\"\\u003cimg src='\\u0026amp;'\\/\\u003e\"" == sd_ujson.dumps(
		"<img src='&amp;'/>", encode_html_chars=True, escape_forward_slashes=True,
	)


def test_double_long_issue():
	sut = {"a": -4342969734183514}
	encoded = sdjson.dumps(sut)
	decoded = sdjson.loads(encoded)
	assert sut == decoded
	encoded = sd_ujson.encode(sut)
	decoded = sd_ujson.decode(encoded)
	assert sut == decoded


def test_double_long_decimal_issue():
	sut = {"a": -12345678901234.56789012}
	encoded = sdjson.dumps(sut)
	decoded = sdjson.loads(encoded)
	assert sut == decoded
	encoded = sd_ujson.encode(sut)
	decoded = sd_ujson.decode(encoded)
	assert sut == decoded


def test_encode_decode_long_decimal():
	sut = {"a": -528656961.4399388}
	encoded = sd_ujson.dumps(sut)
	sd_ujson.decode(encoded)


def test_decimal_decode_test():
	sut = {"a": 4.56}
	encoded = sd_ujson.encode(sut)
	decoded = sd_ujson.decode(encoded)
	assert_almost_equal(sut["a"], decoded["a"])


def test_encode_double_conversion():
	test_input = math.pi
	output = sd_ujson.encode(test_input)
	assert round(test_input, 5) == round(sdjson.loads(output), 5)
	assert round(test_input, 5) == round(sd_ujson.decode(output), 5)


def test_encode_double_neg_conversion():
	test_input = -math.pi
	output = sd_ujson.encode(test_input)

	assert round(test_input, 5) == round(sdjson.loads(output), 5)
	assert round(test_input, 5) == round(sd_ujson.decode(output), 5)


def test_encode_array_of_nested_arrays():
	test_input = [[[[]]]] * 20
	output = sd_ujson.encode(test_input)
	assert test_input == sdjson.loads(output)
	# assert output == json.dumps(test_input)
	assert test_input == sd_ujson.decode(output)


def test_encode_array_of_doubles():
	test_input = [31337.31337, 31337.31337, 31337.31337, 31337.31337] * 10
	output = sd_ujson.encode(test_input)
	assert test_input == sdjson.loads(output)
	# assert output == json.dumps(test_input)
	assert test_input == sd_ujson.decode(output)


def test_encode_string_conversion2():
	test_input = "A string \\ / \b \f \n \r \t"
	output = sd_ujson.encode(test_input, escape_forward_slashes=True)
	assert test_input == sdjson.loads(output)
	assert output == '"A string \\\\ \\/ \\b \\f \\n \\r \\t"'
	assert test_input == sd_ujson.decode(output)


def test_encode_control_escaping():
	test_input = "\x19"
	enc = sd_ujson.encode(test_input)
	dec = sd_ujson.decode(enc)
	assert test_input == dec
	assert enc == sdjson.dumps(test_input)


# Characters outside of Basic Multilingual Plane(larger than
# 16 bits) are represented as \UXXXXXXXX in python but should be encoded
# as \uXXXX\uXXXX in json.
def test_encode_unicode_bmp():
	s = "\U0001f42e\U0001f42e\U0001F42D\U0001F42D"  # 🐮🐮🐭🐭
	encoded = sd_ujson.dumps(s)
	encoded_json = sdjson.dumps(s)

	if len(s) == 4:
		assert len(encoded) == len(s) * 12 + 2
	else:
		assert len(encoded) == len(s) * 6 + 2

	assert encoded == encoded_json
	decoded = sd_ujson.loads(encoded)
	assert s == decoded

	# sd_ujson outputs an UTF-8 encoded str object
	encoded = sd_ujson.dumps(s, ensure_ascii=False)

	# json outputs an unicode object
	encoded_json = sdjson.dumps(s, ensure_ascii=False)
	assert len(encoded) == len(s) + 2  # original length + quotes
	assert encoded == encoded_json
	decoded = sd_ujson.loads(encoded)
	assert s == decoded


def test_encode_symbols():
	s = "\u273f\u2661\u273f"  # ✿♡✿
	encoded = sd_ujson.dumps(s)
	encoded_json = sdjson.dumps(s)
	assert len(encoded) == len(s) * 6 + 2  # 6 characters + quotes
	assert encoded == encoded_json
	decoded = sd_ujson.loads(encoded)
	assert s == decoded

	# sd_ujson outputs an UTF-8 encoded str object
	encoded = sd_ujson.dumps(s, ensure_ascii=False)

	# json outputs an unicode object
	encoded_json = sdjson.dumps(s, ensure_ascii=False)
	assert len(encoded) == len(s) + 2  # original length + quotes
	assert encoded == encoded_json
	decoded = sd_ujson.loads(encoded)
	assert s == decoded


def test_encode_long_neg_conversion():
	test_input = -9223372036854775808
	output = sd_ujson.encode(test_input)

	sdjson.loads(output)
	sd_ujson.decode(output)

	assert test_input == sdjson.loads(output)
	assert output == sdjson.dumps(test_input)
	assert test_input == sd_ujson.decode(output)


def test_encode_list_conversion():
	test_input = [1, 2, 3, 4]
	output = sd_ujson.encode(test_input)
	assert test_input == sdjson.loads(output)
	assert test_input == sd_ujson.decode(output)


def test_encode_dict_conversion():
	test_input = {"k1": 1, "k2": 2, "k3": 3, "k4": 4}
	output = sd_ujson.encode(test_input)
	assert test_input == sdjson.loads(output)
	assert test_input == sd_ujson.decode(output)
	assert test_input == sd_ujson.decode(output)


@pytest.mark.xfail
def test_encode_dict_values_ref_counting():
	import gc

	gc.collect()
	value = ["abc"]
	data = {"1": value}
	ref_count = sys.getrefcount(value)
	sd_ujson.dumps(data)
	assert ref_count == sys.getrefcount(value)

@pytest.mark.xfail
def test_encode_dict_key_ref_counting():
	import gc

	gc.collect()
	key = "key"
	data = {key: "abc"}
	ref_count = sys.getrefcount(key)
	sd_ujson.dumps(data)
	assert ref_count == sys.getrefcount(key)


def test_encode_to_utf8():
	test_input = b"\xe6\x97\xa5\xd1\x88"
	test_input = test_input.decode("utf-8")
	enc = sd_ujson.encode(test_input, ensure_ascii=False)
	dec = sd_ujson.decode(enc)
	assert enc == sdjson.dumps(test_input, ensure_ascii=False)
	assert dec == sdjson.loads(enc)


def test_decode_from_unicode():
	test_input = '{"obj": 31337}'
	dec1 = sd_ujson.decode(test_input)
	dec2 = sd_ujson.decode(str(test_input))
	assert dec1 == dec2


def test_encode_recursion_max():
	# 8 is the max recursion depth
	class O2:
		member = 0

		def toDict(self):
			return {"member": self.member}

	class O1:
		member = 0

		def toDict(self):
			return {"member": self.member}

	test_input = O1()
	test_input.member = O2()
	test_input.member.member = test_input
	with pytest.raises(OverflowError):
		sd_ujson.encode(test_input)


def test_decode_dict():
	test_input = "{}"
	obj = sd_ujson.decode(test_input)
	assert {} == obj
	test_input = '{"one": 1, "two": 2, "three": 3}'
	obj = sd_ujson.decode(test_input)
	assert {"one": 1, "two": 2, "three": 3} == obj


def test_encode_unicode_4_bytes_utf8_fail():
	test_input = b"\xfd\xbf\xbf\xbf\xbf\xbf"
	with pytest.raises(OverflowError):
		sd_ujson.encode(test_input)


def test_encode_null_character():
	test_input = "31337 \x00 1337"
	output = sd_ujson.encode(test_input)
	assert test_input == sdjson.loads(output)
	assert output == sdjson.dumps(test_input)
	assert test_input == sd_ujson.decode(output)

	test_input = "\x00"
	output = sd_ujson.encode(test_input)
	assert test_input == sdjson.loads(output)
	assert output == sdjson.dumps(test_input)
	assert test_input == sd_ujson.decode(output)

	assert '"  \\u0000\\r\\n "' == sd_ujson.dumps("  \u0000\r\n ")


def test_decode_null_character():
	test_input = '"31337 \\u0000 31337"'
	assert sd_ujson.decode(test_input) == sdjson.loads(test_input)


def test_dump_to_file():
	f = six.StringIO()
	sd_ujson.dump([1, 2, 3], f)
	assert "[1,2,3]" == f.getvalue()


def test_dump_to_file_like_object():
	class FileLike:
		def __init__(self):
			self.bytes = ""

		def write(self, bytes):
			self.bytes += bytes

	f = FileLike()
	sd_ujson.dump([1, 2, 3], f)
	assert "[1,2,3]" == f.bytes


def test_dump_file_args_error():
	with pytest.raises(AttributeError):
		sd_ujson.dump([], "")


def test_load_file():
	f = six.StringIO("[1,2,3,4]")
	assert [1, 2, 3, 4] == sd_ujson.load(f)


def test_load_file_like_object():
	class FileLike:
		def read(self):
			try:
				self.end
			except AttributeError:
				self.end = True
				return "[1,2,3,4]"

	f = FileLike()
	assert [1, 2, 3, 4] == sd_ujson.load(f)


def test_load_file_args_error():
	with pytest.raises(TypeError):
		sd_ujson.load("[]")


def test_version():
	assert re.search(
		r"^\d+\.\d+(\.\d+)?", sd_ujson.__version__
	), "sd_ujson.__version__ must be a string like '1.4.0'"


def test_decode_number_with32bit_sign_bit():
	# Test that numbers that fit within 32 bits but would have the
	# sign bit set (2**31 <= x < 2**32) are decoded properly.
	docs = (
		'{"id": 3590016419}',
		'{"id": %s}' % 2 ** 31,
		'{"id": %s}' % 2 ** 32,
		'{"id": %s}' % ((2 ** 32) - 1),
	)
	results = (3590016419, 2 ** 31, 2 ** 32, 2 ** 32 - 1)
	for doc, result in zip(docs, results):
		assert sd_ujson.decode(doc)["id"] == result


def test_encode_big_escape():
	for x in range(10):
		base = "\u00e5".encode()
		test_input = base * 1024 * 1024 * 2
		sd_ujson.encode(test_input)


def test_decode_big_escape():
	for x in range(10):
		base = "\u00e5".encode()
		quote = b'"'
		test_input = quote + (base * 1024 * 1024 * 2) + quote
		sd_ujson.decode(test_input)


def test_to_dict():
	d = {"key": 31337}

	class DictTest:
		def toDict(self):
			return d

		def __json__(self):
			return '"json defined"'  # Fallback and shouldn't be called.

	o = DictTest()
	output = sd_ujson.encode(o)
	dec = sd_ujson.decode(output)
	assert dec == d


def test_object_with_json():
	# If __json__ returns a string, then that string
	# will be used as a raw JSON snippet in the object.
	output_text = "this is the correct output"

	class JSONTest:
		def __json__(self):
			return '"' + output_text + '"'

	d = {"key": JSONTest()}
	output = sd_ujson.encode(d)
	dec = sd_ujson.decode(output)
	assert dec == {"key": output_text}


def test_object_with_complex_json():
	# If __json__ returns a string, then that string
	# will be used as a raw JSON snippet in the object.
	obj = {"foo": ["bar", "baz"]}

	class JSONTest:
		def __json__(self):
			return sd_ujson.encode(obj)

	d = {"key": JSONTest()}
	output = sd_ujson.encode(d)
	dec = sd_ujson.decode(output)
	assert dec == {"key": obj}


def test_object_with_json_type_error():
	# __json__ must return a string, otherwise it should raise an error.
	for return_value in (None, 1234, 12.34, True, {}):

		class JSONTest:
			def __json__(self):
				return return_value

		d = {"key": JSONTest()}
		with pytest.raises(TypeError):
			sd_ujson.encode(d)


def test_object_with_json_attribute_error():
	# If __json__ raises an error, make sure python actually raises it.
	class JSONTest:
		def __json__(self):
			raise AttributeError

	d = {"key": JSONTest()}
	with pytest.raises(AttributeError):
		sd_ujson.encode(d)


def test_decode_array_empty():
	test_input = "[]"
	obj = sd_ujson.decode(test_input)
	assert [] == obj


def test_encoding_invalid_unicode_character():
	s = "\udc7f"
	with pytest.raises(UnicodeEncodeError):
		sd_ujson.dumps(s)


def test_sort_keys():
	data = {"a": 1, "c": 1, "b": 1, "e": 1, "f": 1, "d": 1}
	sorted_keys = sd_ujson.dumps(data, sort_keys=True)
	assert sorted_keys == '{"a":1,"b":1,"c":1,"d":1,"e":1,"f":1}'


@pytest.mark.parametrize(
	"test_input",
	[
		"[31337]",  # array one item
		"18446744073709551615",  # long unsigned value
		"9223372036854775807",  # big value
		"-9223372036854775808",  # small value
		"{}\n\t ",  # trailing whitespaces
	],
)
def test_decode_no_assert(test_input):
	sd_ujson.decode(test_input)


@pytest.mark.parametrize(
	"test_input, expected", [("31337", 31337), ("-31337", -31337)],
)
def test_decode(test_input, expected):
	assert sd_ujson.decode(test_input) == expected


@pytest.mark.parametrize(
	"test_input",
	[
		"1337E40",
		"1.337E40",
		"1337E+9",
		"1.337e+40",
		"1337E40",
		"1337e40",
		"1.337E-4",
		"1.337e-4",
	],
)
def test_decode_numeric_int_exp(test_input):
	output = sd_ujson.decode(test_input)
	assert output == sdjson.loads(test_input)


@pytest.mark.parametrize(
	"test_input, expected",
	[
		('{{1337:""}}', ValueError),  # broken dict key type leak test
		('{{"key":"}', ValueError),  # broken dict leak test
		('{{"key":"}', ValueError),  # broken dict leak test
		("[[[true", ValueError),  # broken list leak test
	],
)
def test_decode_range_raises(test_input, expected):
	for x in range(1000):
		with pytest.raises(ValueError):
			sd_ujson.decode(test_input)


@pytest.mark.parametrize(
	"test_input, expected",
	[
		("fdsa sda v9sa fdsa", ValueError),  # jibberish
		("[", ValueError),  # broken array start
		("{", ValueError),  # broken object start
		("]", ValueError),  # broken array end
		("}", ValueError),  # broken object end
		# TODO: ('{"one":1,}', ValueError),  # object trailing comma fail
		('"TESTING', ValueError),  # string unterminated
		('"TESTING\\"', ValueError),  # string bad escape
		("tru", ValueError),  # true broken
		("fa", ValueError),  # false broken
		("n", ValueError),  # null broken
		("{{{{31337}}}}", ValueError),  # dict with no key
		('{{{{"key"}}}}', ValueError),  # dict with no colon or value
		('{{{{"key":}}}}', ValueError),  # dict with no value
		("[31337,]", ValueError),  # array trailing comma fail
		("[,31337]", ValueError),  # array leading comma fail
		("[,]", ValueError),  # array only comma fail
		("[]]", ValueError),  # array unmatched bracket fail
		("18446744073709551616", ValueError),  # too big value
		("-90223372036854775809", ValueError),  # too small value
		("18446744073709551616", ValueError),  # very too big value
		("-90223372036854775809", ValueError),  # very too small value
		("{}\n\t a", ValueError),  # with trailing non whitespaces
		("[18446744073709551616]", ValueError),  # array with big int
		('{"age", 44}', ValueError),  # read bad object syntax
	],
)
def test_decode_raises(test_input, expected):
	with pytest.raises(expected):
		print(test_input)
		sd_ujson.decode(test_input)


@pytest.mark.parametrize(
	"test_input, expected",
	[
		("[", ValueError),  # array depth too big
		("{", ValueError),  # object depth too big
	],
)
def test_decode_raises_for_long_input(test_input, expected):
	with pytest.raises(expected):
		sd_ujson.decode(test_input * (1024 * 1024))


@pytest.mark.parametrize(
	"test_input, expected",
	[
		(True, "true"),
		(False, "false"),
		(None, "null"),
		([True, False, None], "[true,false,null]"),
		((True, False, None), "[true,false,null]"),
	],
)
def test_dumps(test_input, expected):
	assert sd_ujson.dumps(test_input) == expected


class SomeObject:
	def __repr__(self):
		return "Some Object"


EMPTY_SET_ERROR = "set() is not JSON serializable"
FILLED_SET_ERROR = "{1, 2, 3} is not JSON serializable"


@pytest.mark.xfail(reason="Not working as expected")
@pytest.mark.parametrize(
	"test_input, expected_exception, expected_message",
	[
		(set(), TypeError, EMPTY_SET_ERROR),
		({1, 2, 3}, TypeError, FILLED_SET_ERROR),
		(SomeObject(), TypeError, "Some Object is not JSON serializable"),
	],
)
def test_dumps_raises(test_input, expected_exception, expected_message):
	with pytest.raises(expected_exception) as e:
		sd_ujson.dumps(test_input)
	assert str(e.value) == expected_message


@pytest.mark.parametrize(
	"test_input",
	[
		{
			"key1": "value1",
			"key1": "value1",
			"key1": "value1",
			"key1": "value1",
			"key1": "value1",
			"key1": "value1",
		},
		{
			"بن": "value1",
			"بن": "value1",
			"بن": "value1",
			"بن": "value1",
			"بن": "value1",
			"بن": "value1",
			"بن": "value1",
		},
	],
)
def test_encode_no_assert(test_input):
	sd_ujson.encode(test_input)


@pytest.mark.parametrize(
	"test_input, expected",
	[
		(1.0, "1.0"),
		(OrderedDict([(1, 1), (0, 0), (8, 8), (2, 2)]), '{"1":1,"0":0,"8":8,"2":2}'),
	],
)
def test_encode(test_input, expected):
	assert sd_ujson.encode(test_input) == expected


@pytest.mark.parametrize(
	"test_input",
	[
		[
			9223372036854775807,
			9223372036854775807,
			9223372036854775807,
			9223372036854775807,
			9223372036854775807,
			9223372036854775807,
		],
		[18446744073709551615, 18446744073709551615, 18446744073709551615],
	],
)
def test_encode_list_long_conversion(test_input):
	output = sd_ujson.encode(test_input)
	assert test_input == sdjson.loads(output)
	assert test_input == sd_ujson.decode(output)


@pytest.mark.parametrize(
	"test_input", [9223372036854775807, 18446744073709551615],
)
def test_encode_long_conversion(test_input):
	output = sd_ujson.encode(test_input)

	assert test_input == sdjson.loads(output)
	assert output == sdjson.dumps(test_input)
	assert test_input == sd_ujson.decode(output)


@pytest.mark.parametrize(
	"test_input, expected",
	[
		(float("nan"), OverflowError),
		(float("inf"), OverflowError),
		(-float("inf"), OverflowError),
		(12839128391289382193812939, OverflowError),
	],
)
def test_encode_raises(test_input, expected):
	with pytest.raises(expected):
		sd_ujson.encode(test_input)


@pytest.mark.parametrize("test_input", [[[[[]]]], 31337, -31337, None, True, False])
def test_encode_decode(test_input):
	output = sd_ujson.encode(test_input)

	assert test_input == sdjson.loads(output)
	assert output == sdjson.dumps(test_input)
	assert test_input == sd_ujson.decode(output)


@pytest.mark.parametrize(
	"test_input",
	[
		"Räksmörgås اسامة بن محمد بن عوض بن لادن",
		"\xe6\x97\xa5\xd1\x88",
		"\xf0\x90\x8d\x86",  # surrogate pair
		"\xf0\x91\x80\xb0TRAILINGNORMAL",  # 4 bytes UTF8
		"\xf3\xbf\xbf\xbfTRAILINGNORMAL",  # 4 bytes UTF8 highest
	],
)
def test_encode_unicode(test_input):
	enc = sd_ujson.encode(test_input)
	dec = sd_ujson.decode(enc)

	assert enc == sdjson.dumps(test_input)
	assert dec == sdjson.loads(enc)


@pytest.mark.parametrize(
	"test_input, expected",
	[
		("-1.1234567893", -1.1234567893),
		("-1.234567893", -1.234567893),
		("-1.34567893", -1.34567893),
		("-1.4567893", -1.4567893),
		("-1.567893", -1.567893),
		("-1.67893", -1.67893),
		("-1.7893", -1.7893),
		("-1.893", -1.893),
		("-1.3", -1.3),
		("1.1234567893", 1.1234567893),
		("1.234567893", 1.234567893),
		("1.34567893", 1.34567893),
		("1.4567893", 1.4567893),
		("1.567893", 1.567893),
		("1.67893", 1.67893),
		("1.7893", 1.7893),
		("1.893", 1.893),
		("1.3", 1.3),
		("true", True),
		("false", False),
		("null", None),
		(" [ true, false,null] ", [True, False, None]),
	],
)
def test_loads(test_input, expected):
	assert sd_ujson.loads(test_input) == expected


"""
def test_decode_numeric_int_frc_overflow():
input = "X.Y"
raise NotImplementedError("Implement this test!")


def test_decode_string_unicode_escape():
input = "\u3131"
raise NotImplementedError("Implement this test!")

def test_decode_string_unicode_broken_escape():
input = "\u3131"
raise NotImplementedError("Implement this test!")

def test_decode_string_unicode_invalid_escape():
input = "\u3131"
raise NotImplementedError("Implement this test!")

def test_decode_string_utf8():
input = "someutfcharacters"
raise NotImplementedError("Implement this test!")

"""

"""
# Use this to look for memory leaks
if __name__ == '__main__':
	import unittest
	from guppy import hpy
	hp = hpy()
	hp.setrelheap()
	while True:
		try:
			unittest.main()
		except SystemExit:
			pass
		heap = hp.heapu()
		print(heap)
"""