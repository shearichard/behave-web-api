from __future__ import unicode_literals
import os
import re
import requests
from functools import wraps

NULL_SUFFIX = '''_or_null'''

try:
    string_type = basestring
except NameError:  # Python 3, basestring causes NameError
    string_type = str


def make_url(context, endingpoint):
    BASE_URL = dereference_variables(context, '$BASE_URL')
    if 'http' not in BASE_URL:
        BASE_URL = 'http://{0}'.format(BASE_URL)

    return '{0}{1}'.format(BASE_URL, endingpoint)


def dereference_variables(context, value):
    variables = context.variables\
        if hasattr(context, 'variables') else {}

    for key in re.findall('\$+\w+', value):
        var_name = key[1:]
        value = value.replace(
            key,
            variables.get(
                var_name,
                os.environ.get(var_name, key)
            )
        )

    return value


def dereference_arguments(f):
    @wraps(f)
    def wrapper(context, *args, **kwargs):
        new_kwargs = {}
        new_args = []
        for key, value in kwargs.items():
            new_kwargs[key] = dereference_variables(context.text, value)
        for value in args:
            new_args.append(dereference_variables(context.text, value))
        context.processed_text = dereference_variables(context, context.text)\
            if context.text else ''
        return f(context, *new_args, **new_kwargs)
    return wrapper


def compare_lists(expected_list, actual_list, path=None):
    assert type(expected_list) is list,\
        "Expected {0} is not a list".format(repr(expected_list))
    assert type(actual_list) is list,\
        "Actual {0} is not a list".format(repr(actual_list))

    for i, item in enumerate(expected_list):
        path = '{0}.{1}'.format(path, i) if path else str(i)
        try:
            actual_value = actual_list[i]
        except ValueError:
            actual_value = None
        compare_values(item, actual_value, path=path)


def compare_dicts(expected_dict, actual_dict, strict=False, path=None):
    assert type(expected_dict) is dict,\
        "Expected {0} is not a dict".format(repr(expected_dict))
    assert type(actual_dict) is dict,\
        "Actual {0} is not a dict".format(repr(actual_dict))

    if strict:
        assert expected_dict.keys() == actual_dict.keys(), \
            "Keys/Properties of actual values do not match those of expected values"

    for key in expected_dict:
        expected_value = expected_dict[key]
        actual_value = actual_dict.get(key, None)
        path = '{0}.{1}'.format(path, key) if path else key

        compare_values(expected_value, actual_value, strict=False, path=path)


def validate_value_iso_datetime(matchstr):
    '''
    Test whether the 'matchstr' argument matches an
    ISO-8601.2019 format date/time. An example of such
    a date/time is '2021-11-30T14:20:15'
    '''

    rgx_pttn = r"""[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}"""

    # method 1: using a compile object
    compile_obj = re.compile(rgx_pttn)
    match_obj = compile_obj.search(matchstr)

    if match_obj:
        return True
    else:
        return False


def validate_value_iso_datetime_at_eoe(matchstr):
    '''
    Test whether the 'matchstr' argument matches an
    ISO-8601.2019 format date/time and the value of the
    date/time is '2300-01-01T00:00:00'
    '''

    rgx_pttn = r"""(?P<YYYY>[0-9]{4})
    -
    (?P<MM>[0-9]{2})
    -
    (?P<DD>[0-9]{2})
    T
    (?P<HH24>[0-9]{2})
    :
    (?P<MI>[0-9]{2})
    :
    (?P<S>[0-9]{2})"""

    if validate_value_iso_datetime(matchstr):
        compile_obj = re.compile(rgx_pttn,  re.MULTILINE| re.VERBOSE)
        match_obj = compile_obj.search(matchstr)
        #
        if ((match_obj.group('YYYY') == "2300") and
            (match_obj.group('MM') == "01") and
            (match_obj.group('DD') == "01") and
            (match_obj.group('DD') == "01") and
            (match_obj.group('HH24') == "00") and
            (match_obj.group('MI') == "00") and
            (match_obj.group('S') == "00")):
            return True
        else:
            return False
    else:
        return False

def validate_value(validator, value):
    '''
    Test whether the 'value' argument matches one of a set
    of pre-determined situations defined by the value of the
    'validator' argument.

    In addition deal with a special case where the validator
    string is suffixed with a string to indicate that None
    is a valid value 
    '''

    # If the validator string ends with the 'NULL_SUFFIX'
    # then trim the 'NULL_SUFFIX' off the end of the validator
    # so that, for instance, ...
    #
    # 'integer_or_null'
    # 
    # ... becomes ....
    # 
    # 'integer'.
    # 
    # In addition if the value is None (what null from JSON
    # gets converted to) then return True, otherwise just let
    # the normal validation take its course.
    #
    null_sfx_idx = -1 * len(NULL_SUFFIX)

    if validator[null_sfx_idx : ]  == NULL_SUFFIX:
        #Trim the NULL_SUFFIX_ off the 'validator value'
        validator = validator[ : null_sfx_idx]
        #If the value is None, return True
        if value==None:
            return True

    #Having dealt with the 'NULL_SUFFIX' special case now 
    #proceed with normal processing.
    if validator == 'int':
        return type(value) == int
    if validator == 'float':
        return type(value) == float
    if validator == 'number':
        return type(value) == int or type(value) == float
    if validator == 'integer':
        return type(value) == int
    if validator == 'positive_integer':
        return (type(value) == int and (value >= 0))
    if validator == 'string':
        return type(value) == str
    if validator == 'string_and_not_empty':
        return (type(value) == str and (len(value) > 0))
    if validator == 'numeric_true_false':
        return ((type(value) == int) and ((value==0) or (value==1)))
    if validator == 'iso_date_time':
        return validate_value_iso_datetime(value)
    if validator == 'iso_date_time_at_eoe':
        return validate_value_iso_datetime_at_eoe(value)


    raise Exception('Unknown validator: {}'.format(validator))


def compare_values(expected_value, actual_value, strict=False, path=None):
    validator_pattern = r'^<is_(.+)>$'
    regex_pattern = r'^%(.+)%$'

    if type(expected_value) is dict:
        compare_dicts(expected_value, actual_value, strict=strict, path=path)
    elif type(expected_value) is list:
        compare_lists(expected_value, actual_value, path=path)
    elif isinstance(expected_value, string_type) and re.match(regex_pattern, expected_value):
        custom_regex = re.match(regex_pattern, expected_value).groups()[0]
        if not re.match(custom_regex, actual_value or ''):
            message = 'Expected {0} to match regex {1}'
            params = [repr(actual_value), repr(expected_value)]
            if path:
                message = message + ' at path {2}'
                params.append(path)
            raise AssertionError(message.format(*params))
    elif isinstance(expected_value, string_type) and re.match(validator_pattern, expected_value):
        validator_name = re.match(validator_pattern, expected_value).groups()[0]
        is_valid = validate_value(validator_name, actual_value)
        if not is_valid:
            message = 'Expected {0} to match validator {1}'
            params = [repr(actual_value), validator_name]
            if path:
                message = message + ' at path {2}'
                params.append(path)
            raise AssertionError(message.format(*params))
    else:
        try:
            assert expected_value == actual_value
        except AssertionError:
            message = 'Expected {0} to equal {1}'
            params = [repr(actual_value), repr(expected_value)]

            if path:
                message = message + ' at path {2}'
                params.append(path)

            raise AssertionError(message.format(*params))


def compare_contents(expected_value, actual_value):
    if expected_value[0] == '%' and expected_value[-1] == '%':
        assert re.search(expected_value.strip('%'), actual_value or ''),\
            'Expected response to contain regex \'{0}\''.format(expected_value)
    else:
        assert expected_value in actual_value,\
            'Expected response to contain text \'{0}\''.format(expected_value)


def do_request(context, method, endingpoint, body=None):
    fn = getattr(requests, method.lower())
    kwargs = {}

    if hasattr(context, 'request_headers'):
        kwargs['headers'] = context.request_headers

    if body:
        kwargs['data'] = body

    if hasattr(context, 'request_files'):
        kwargs['files'] = context.request_files

    context.response = fn(make_url(context, endingpoint), **kwargs)
