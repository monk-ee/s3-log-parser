
import unittest
import s3_log_parser

class S3LogParserTestCase(unittest.TestCase):
    maxDiff = None

    def test_simple(self):
        format_string ="%BO %B %t %a %r %si %o %k \"%R\" %s %e %b %y %m %n \"%{Referer}i\" \"%{User-Agent}i\" %v"
        parser = s3_log_parser.make_parser(format_string)
        sample = '2b336b437385372703f3b090372adfd0f412c4ff290d502294f681a29b9fd5fc payload [18/Aug/2015:06:10:29 +0000] 22.22.22.22 arn:aws:sts::11111111111:assumed-role/lambda/awslambda_738_20150817233633493 462724543131D25B REST.GET.OBJECT FREE.zip "GET /FREE.zip?AWSAccessKeyId=ASIAIVW2OAE7OBZF4REQ&Expires=1439881105&Signature=DW5c3gIGTTN3soASLzd0zHw5UJA%3D&x-amz-security-token=AQoDYXdzEFEasAJ6n6m0x8GdQRc3Vib26N9Q%2B4qZjRl2rxv3SMUo588qtSl5%2F5ojYDgn08AzhKFT%2FoYU8PzuPUdmsZuSavxlgwBZd81tu5PSG1Qn2V9DcvvCU%2BTIyYzpcyKm5Tt9kxam%2FpdGIT6C8ScZ4ydGgZQ3ft9NRGe5rddY1%2FEzkRYZiM0ALvvDy3yl4Ib7M8NZ0rC3wN8JhKVgvEAn4D7zjmV5YqbOZ0MM6oqFRbEAzlt2PqX%2FVyn6P0ktujgoLlND4KQJoDCmk1WRFMIw47rFND1fswhoNoBsYoiP21dUc4al64Obk%2BInwjWF%2BbITLQViyWgJgNWBxFYAvrvcT1jvEQFcFsb6sDnFq5xet%2FVofNJg4f%2F%2BB36ih7NndrDW%2FDNFsh%2BOgu%2BnbMtnx2xcNmRFMBoq%2FJuoIIHgya4F HTTP/1.1" 200 - 164963168 164963168 8730 32 "-" "python-requests/2.7.0 CPython/2.7.9 Linux/3.14.35-28.38.amzn1.x86_64" -'
        log_data = parser(sample)
        self.assertNotEqual(log_data, None)
        self.assertEqual(log_data['bucket_owner'], '2b336b437385372703f3b090372adfd0f412c4ff290d502294f681a29b9fd5fc')
        self.assertEqual(log_data['bucket'], 'payload')
        self.assertEqual(log_data['remote_ip'], '22.22.22.22')
        self.assertEqual(log_data['requester_id'], 'arn:aws:sts::11111111111:assumed-role/lambda/awslambda_738_20150817233633493')
        self.assertEqual(log_data['s3_request_id'], '462724543131D25B')
        self.assertEqual(log_data['operation'], 'REST.GET.OBJECT')
        self.assertEqual(log_data['key'], 'FREE.zip')
        self.assertEqual(log_data['request_first_line'],'GET /FREE.zip?AWSAccessKeyId=ASIAIVW2OAE7OBZF4REQ&Expires=1439881105&Signature=DW5c3gIGTTN3soASLzd0zHw5UJA%3D&x-amz-security-token=AQoDYXdzEFEasAJ6n6m0x8GdQRc3Vib26N9Q%2B4qZjRl2rxv3SMUo588qtSl5%2F5ojYDgn08AzhKFT%2FoYU8PzuPUdmsZuSavxlgwBZd81tu5PSG1Qn2V9DcvvCU%2BTIyYzpcyKm5Tt9kxam%2FpdGIT6C8ScZ4ydGgZQ3ft9NRGe5rddY1%2FEzkRYZiM0ALvvDy3yl4Ib7M8NZ0rC3wN8JhKVgvEAn4D7zjmV5YqbOZ0MM6oqFRbEAzlt2PqX%2FVyn6P0ktujgoLlND4KQJoDCmk1WRFMIw47rFND1fswhoNoBsYoiP21dUc4al64Obk%2BInwjWF%2BbITLQViyWgJgNWBxFYAvrvcT1jvEQFcFsb6sDnFq5xet%2FVofNJg4f%2F%2BB36ih7NndrDW%2FDNFsh%2BOgu%2BnbMtnx2xcNmRFMBoq%2FJuoIIHgya4F HTTP/1.1')
        self.assertEqual(log_data['status'], '200')
        self.assertEqual(log_data['error'], '-')
        self.assertEqual(log_data['bytes'], '164963168')
        self.assertEqual(log_data['total_bytes'], '164963168')
        self.assertEqual(log_data['total_time'], '8730')
        self.assertEqual(log_data['turnaround_time'], '32')
        self.assertEqual(log_data['request_header_referer'], '-')
        self.assertEqual(log_data['request_http_ver'], '1.1')
        self.assertEqual(log_data['request_method'], 'GET')
        self.assertEqual(log_data['request_header_user_agent'], 'python-requests/2.7.0 CPython/2.7.9 Linux/3.14.35-28.38.amzn1.x86_64')
        self.assertEqual(log_data['version_id'], '-')


if __name__ == '__main__':
    unittest.main()
