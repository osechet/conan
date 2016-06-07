import unittest, random, string
from io import BufferedReader, BytesIO
from itertools import islice
from conans.client.rest.uploader_downloader import Downloader 

class DownloaderTest(unittest.TestCase):

    def __init__(self, methodName='runTest'):
        super(DownloaderTest, self).__init__(methodName)
        self.ENCODING = "utf-8"

    def download_test(self):
        url = "http://hello/conan"
        content = "Hello Conan"
        requester = RequestsMock()
        requester.mock(url, Response(bytearray(content, self.ENCODING)))
        downloader = Downloader(requester, output=None, verify=True)
        result = downloader.download(url)
        self.assertEqual(content, result.decode(self.ENCODING))

    def download_io_test(self):
        url = "http://hello/conan"
        content = "Hello Conan"
        requester = RequestsMock()
        requester.mock(url, Response(bytearray(content, self.ENCODING)))
        downloader = Downloader(requester, output=None, verify=True)
        buf = BytesIO()
        downloader.download_io(url, buf)
        self.assertEqual(content, buf.getvalue().decode(self.ENCODING))

    def download_empty_test(self):
        url = "http://empty/file"
        requester = RequestsMock()
        requester.mock(url, Response(bytearray("", self.ENCODING)))
        downloader = Downloader(requester, output=None, verify=True)
        buf = BytesIO()
        downloader.download_io(url, buf)
        self.assertFalse(buf.getvalue())

    def download_no_header_test(self):
        url = "http://no/header"
        content = "No Header"
        requester = RequestsMock()
        requester.mock(url, Response(bytearray(content, self.ENCODING), 0))
        downloader = Downloader(requester, output=None, verify=True)
        buf = BytesIO()
        downloader.download_io(url, buf)
        self.assertEqual(content, buf.getvalue().decode(self.ENCODING))

    def download_need_buffer_test(self):
        url = "http://need/buffer"
        content = ""
        for i in range(10):
            content += "".join(random.choice(string.ascii_letters) for _ in range(1024))
        requester = RequestsMock()
        requester.mock(url, Response(bytearray(content, self.ENCODING), 0))
        downloader = Downloader(requester, output=None, verify=True)
        buf = BytesIO()
        downloader.download_io(url, buf)
        self.assertEqual(content, buf.getvalue().decode(self.ENCODING))


class RequestsMock(object):
    
    def __init__(self):
        self._responses = {}

    def mock(self, url, response):
        self._responses[url] = response

    def get(self, url, stream, verify):
        return self._responses[url]


class Response(object):

    def __init__(self, content, length=None):
        self._ok = True
        if not length:
            length = len(content)
        self._headers = Header(length)
        self._content = content

    @property
    def ok(self):
        return self._ok

    @property
    def headers(self):
        return self._headers

    @property
    def content(self):
        return self._content
    
    def iter_content(self, chunk_size):
        return Content(self._content, chunk_size)

class Content(object):

    def __init__(self, data, chunk_size):
        self._data = data
        self._chunk_size = chunk_size
        self._current = 0

    def __iter__(self):
        return self

    def next(self):
        return self.__next__()

    def __next__(self):
        if self._current >= len(self._data):
            raise StopIteration

        begin = self._current
        end = min(len(self._data), self._current + self._chunk_size)
        self._current = end
        return self._data[begin:end]

class Header(object):

    def __init__(self, length):
        self._ok = True
        self._length = length

    def get(self, attr):
        if attr == "content-length":
            return self._length
        return None

