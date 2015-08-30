# -*- coding: utf-8 -*-
__author__ = 'Monkee Magic <magic.monkee.magic@gmail.com>'
__version__ = '1.0.0'

"""Parses log lines from an s3 log file.


Example:



Changelog:


Attributes:


"""
import re
from datetime import datetime, tzinfo, timedelta

import user_agents

class S3LogParserException(Exception): pass

class LineDoesntMatchException(S3LogParserException):
    def __init__(self, log_line=None, regex=None, *args, **kwargs):
        self.log_line = log_line
        self.regex = regex

    def __repr__(self):
        return u"LineDoesntMatchException(log_line={0!r}, regex={1!r})".format(self.log_line, self.regex)

    __str__ = __repr__

def extract_inner_value(output_prefix, input_suffix):
    """
    Given an input format like %{Referer}o return a function that will extract that 'Referer' from a match
    """
    regex = re.compile("^%\{([^\}]+?)\}"+input_suffix+"$")
    def matcher(matched_string):
        match = regex.match(matched_string)
        inner_value = match.groups()[0]
        inner_value = inner_value.strip().lower().replace("-", "_")
        return output_prefix+inner_value
    return matcher

def make_regex(format_template):
    """
    Turn a format_template from %s into something like %[<>]?s
    """
    # FIXME support the return code format
    percent, rest = format_template[0], format_template[1:]
    return percent+"[<>]?"+rest

def extra_request_from_first_line(matched_strings):
    first_line = matched_strings['request_first_line']
    match = re.match("^(?P<method>GET|HEAD|POST|OPTIONS|PUT|CONNECT|PATCH|PROPFIND|DELETE)\s?(?P<url>.{,10000}?)(\s+HTTP/(?P<http_ver>1.[01]))?$", first_line)
    if match is None:
        # Possibly garbage, ignore it
        results = { 'request_first_line': first_line, 'request_method': '', 'request_url': '', 'request_http_ver': ''}
    else:
        results = { 'request_first_line': first_line, 'request_method': match.groupdict()['method'], 'request_url': match.groupdict()['url'], 'request_http_ver': match.groupdict()['http_ver']}
    return results

def parse_user_agent(matched_strings):
    ua = matched_strings['request_header_user_agent']
    parsed_ua = user_agents.parse(ua)
    matched_strings.update({
        'request_header_user_agent__browser__family': parsed_ua.browser.family,
        'request_header_user_agent__browser__version_string': parsed_ua.browser.version_string,
        'request_header_user_agent__os__family': parsed_ua.os.family,
        'request_header_user_agent__os__version_string': parsed_ua.os.version_string,
        'request_header_user_agent__is_mobile': parsed_ua.is_mobile,
    })

    return matched_strings

class FixedOffset(tzinfo):
    """Fixed offset in minutes east from UTC."""

    def __init__(self, string):
        #import pudb ; pudb.set_trace()
        if string[0] == '-':
            direction = -1
            string = string[1:]
        elif string[0] == '+':
            direction = +1
            string = string[1:]
        else:
            direction = +1
            string = string

        hr_offset = int(string[0:2], 10)
        min_offset = int(string[2:3], 10)
        min_offset = hr_offset * 60 + min_offset
        min_offset = direction * min_offset

        self.__offset = timedelta(minutes = min_offset)

        self.__name = string

    def utcoffset(self, dt):
        return self.__offset

    def tzname(self, dt):
        return self.__name

    def dst(self, dt):
        return timedelta(0)

    def __repr__(self):
        return repr(self.__name)


def apachetime(s):
    """
    Given a string representation of a datetime in apache format (e.g.
    "01/Sep/2012:06:05:11 +0000"), return the python datetime for that string, with timezone
    """
    month_map = {'Jan': 1, 'Feb': 2, 'Mar':3, 'Apr':4, 'May':5, 'Jun':6, 'Jul':7,
        'Aug':8,  'Sep': 9, 'Oct':10, 'Nov': 11, 'Dec': 12}
    s = s[1:-1]

    tz_string = s[21:26]
    tz = FixedOffset(tz_string)

    obj = datetime(year=int(s[7:11]), month=month_map[s[3:6]], day=int(s[0:2]),
                hour=int(s[12:14]), minute=int(s[15:17]), second=int(s[18:20]),
                tzinfo=tz )

    return obj

def format_time(matched_strings):
    time_received = matched_strings['time_received']

    # Parse it to a timezone string
    obj = apachetime(time_received)
    
    # For backwards compatibility, time_received_datetimeobj is a naive
    # datetime, so we have to create a timezone less version
    naive_obj = obj.replace(tzinfo=None)

    utc = FixedOffset('0000')
    utc_obj = obj.astimezone(utc)

    return {
        'time_received':time_received,
        'time_received_datetimeobj': naive_obj, 'time_received_isoformat': naive_obj.isoformat(),
        'time_received_tz_datetimeobj': obj, 'time_received_tz_isoformat': obj.isoformat(),
        'time_received_utc_datetimeobj': utc_obj, 'time_received_utc_isoformat': utc_obj.isoformat(),
    }

IPv4_ADDR_REGEX = '(?:\d{1,3}\.){3}\d{1,3}'
IPv6_ADDR_REGEX = r"([0-9A-Fa-f]{0,4}:){2,7}([0-9A-Fa-f]{1,4}|("+IPv4_ADDR_REGEX+"))"
IP_ADDR_REGEX = "("+IPv4_ADDR_REGEX+"|"+IPv6_ADDR_REGEX+")"
FORMAT_STRINGS = [
    ['%%', '%', lambda match: '', lambda matched_strings: matched_strings],
    [make_regex('%BO'), '([0-9a-fA-F]{64})', lambda match: 'bucket_owner', lambda matched_strings: matched_strings], #	The canonical user ID of the owner of the source bucket.
    [make_regex('%B'), '([a-z0-9\-]*)', lambda match: 'bucket', lambda matched_strings: matched_strings], #	The name of the bucket that the request was processed against. If the system receives a malformed request and cannot determine the bucket, the request will not appear in any server access log.
    [make_regex('%t'), '\[.*?\]', lambda match: 'time_received', format_time], #	Time the request was received (standard english format) The time at which the request was received. The format, using strftime() terminology, is [%d/%b/%Y:%H:%M:%S %z]
    [make_regex('%a'), IP_ADDR_REGEX, lambda match: 'remote_ip', lambda matched_strings: matched_strings], #	Remote IP-address The apparent Internet address of the requester. Intermediate proxies and firewalls might obscure the actual address of the machine making the request.
    [make_regex('%r'), '([a-zA-Z0-9\-\_\:\/]*)', lambda match: 'requester_id', lambda matched_strings: matched_strings], #	The canonical user ID of the requester, or the string "Anonymous" for unauthenticated requests. If the requester was an IAM user, this field will return the requester's IAM user name along with the AWS root account that the IAM user belongs to. This identifier is the same one used for access control purposes.
    [make_regex('%si'), '([A-Z0-9]+)', lambda match: 's3_request_id', lambda matched_strings: matched_strings], #The request ID is a string generated by Amazon S3 to uniquely identify each request.
    [make_regex('%o'), '([A-Z\.]*)', lambda match: 'operation', lambda matched_strings: matched_strings], #The operation listed here is declared as SOAP.operation, REST.HTTP_method.resource_type, WEBSITE.HTTP_method.resource_type, or BATCH.DELETE.OBJECT.
    [make_regex('%k'), '([a-zA-Z0-9\.\%\_\-]+|-)', lambda match: 'key', lambda matched_strings: matched_strings], #	The "key" part of the request, URL encoded, or "-" if the operation does not take a key parameter.
    [make_regex('%R'), '.*?', lambda match: 'request_first_line', extra_request_from_first_line], #	First line of request. The Request-URI part of the HTTP request message.
    [make_regex('%s'), '\d+', lambda match: 'status', lambda matched_strings: matched_strings], #	The request method The numeric HTTP status code of the response.
    [make_regex('%e'), '(\w+|-)', lambda match: 'error', lambda matched_strings: matched_strings], #The Amazon S3 Error Code, or "-" if no error occurred.
    [make_regex('%b'), '(\d+|-)', lambda match: 'bytes', lambda matched_strings: matched_strings], #	Size of response in bytes, excluding HTTP headers. The number of response bytes sent, excluding HTTP protocol overhead, or "-" if zero.
    [make_regex('%y'), '(\d+|-)', lambda match: 'total_bytes', lambda matched_strings: matched_strings], #	Size of response in bytes, excluding HTTP headers. In CLF format, i.e. a '-' rather than a 0 when no bytes are sent. The total size of the object in question.
    [make_regex('%m'), '(\d+|-)', lambda match: 'total_time', lambda matched_strings: matched_strings], #	The number of milliseconds the request was in flight from the server's perspective. This value is measured from the time your request is received to the time that the last byte of the response is sent. Measurements made from the client's perspective might be longer due to network latency.
    [make_regex('%n'), '(\d+|-)', lambda match: 'turnaround_time', lambda matched_strings: matched_strings], #	The number of milliseconds that Amazon S3 spent processing your request. This value is measured from the time the last byte of your request was received until the time the first byte of the response was sent.
    [make_regex('%\{[^\}]+?\}i'), '.*?', extract_inner_value("request_header_", "i") , lambda matched_strings: matched_strings], #	The contents of Foobar: header line(s) in the request sent to the server. Changes made by other modules (e.g. mod_headers) affect this. If you're interested in what the request header was prior to when most modules would have modified it, use mod_setenvif to copy the header into an internal environment variable and log that value with the %\{VARNAME}e described above. The value of the HTTP Referrer header, if present. HTTP user-agents (e.g. browsers) typically set this header to the URL of the linking or embedding page when making a request.
    [make_regex('%\{User-Agent\}i'), '.*?', lambda match: "request_header_user_agent" , parse_user_agent],# The value of the HTTP User-Agent header.
    [make_regex('%v'), '(\w+|-)', lambda match: 'version_id', lambda matched_strings: matched_strings], #The version ID in the request, or "-" if the operation does not take a versionId parameter.
]


class Parser:
    def __init__(self, format_string):
        self.names = []

        self.pattern = "("+"|".join(x[0] for x in FORMAT_STRINGS)+")"
        self.parts = re.split(self.pattern, format_string)

        self.functions_to_parse = {}

        self.log_line_regex = ""
        while True:
            if len(self.parts) == 0:
                break
            if len(self.parts) == 1:
                raw, regex = self.parts.pop(0), None
            elif len(self.parts) >= 2:
                raw, regex = self.parts.pop(0), self.parts.pop(0)
            if len(raw) > 0:
                self.log_line_regex += re.escape(raw)
            if regex is not None:
                for format_spec in FORMAT_STRINGS:
                    pattern_regex, log_part_regex, name_func, values_func = format_spec
                    match = re.match("^"+pattern_regex+"$", regex)
                    if match:
                        name = name_func(match.group())
                        self.names.append(name)
                        self.functions_to_parse[name] = values_func
                        self.log_line_regex += "(?P<"+name+">"+log_part_regex+")"
                        break

        self._log_line_regex_raw = self.log_line_regex
        self.log_line_regex = re.compile(self.log_line_regex)
        self.names = tuple(self.names)

    def parse(self, log_line):
        match = self.log_line_regex.match(log_line)
        if match is None:
            raise LineDoesntMatchException(log_line=log_line, regex=self.log_line_regex.pattern)
        else:
            results = {}
            for name in self.functions_to_parse:
                values = {name: match.groupdict()[name]}
                values = self.functions_to_parse[name](values)
                results.update(values)
            return results


def make_parser(format_string):
    return Parser(format_string).parse

def get_fieldnames(format_string):
    return Parser(format_string).names
