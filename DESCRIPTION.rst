S3 Log Parser
=============

Parses log lines from an s3 log file

Usage:

    import s3_log_parser
    line_parser = s3_log_parser.make_parser("%BO %B %t %a %r %si %o %k \"%R\" %s %e %b %y %m %n \"%{Referer}i\" \"%{User-Agent}i\" %v")

This creates & returns a function, ``line_parser``, which accepts a line from an apache log file in that format, and will return the parsed values in a dictionary.
