#!/usr/bin/python

import random


class FastCGIProto(object):
    __FCGI_VERSION = 1

    __FCGI_ROLE_RESPONDER = 1
    __FCGI_ROLE_AUTHORIZER = 2
    __FCGI_ROLE_FILTER = 3

    __FCGI_TYPE_BEGIN = 1
    __FCGI_TYPE_ABORT = 2
    __FCGI_TYPE_END = 3
    __FCGI_TYPE_PARAMS = 4
    __FCGI_TYPE_STDIN = 5
    __FCGI_TYPE_STDOUT = 6
    __FCGI_TYPE_STDERR = 7
    __FCGI_TYPE_DATA = 8
    __FCGI_TYPE_GETVALUES = 9
    __FCGI_TYPE_GETVALUES_RESULT = 10
    __FCGI_TYPE_UNKOWNTYPE = 11

    __FCGI_HEADER_SIZE = 8

    # request state
    FCGI_STATE_SEND = 1
    FCGI_STATE_ERROR = 2
    FCGI_STATE_SUCCESS = 3

    def __init__(self, host, port, timeout=5000, keepalive=0):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.keepalive = keepalive

    def __encodeFastCGIRecord(self, fcgi_type, content, requestid):
        length = len(content)
        return chr(self.__FCGI_VERSION) \
               + chr(fcgi_type) \
               + chr((requestid >> 8) & 0xFF) \
               + chr(requestid & 0xFF) \
               + chr((length >> 8) & 0xFF) \
               + chr(length & 0xFF) \
               + chr(0) \
               + chr(0) \
               + content

    def __encodeNameValueParams(self, name, value):
        nLen = len(str(name))
        vLen = len(str(value))
        record = ''
        if nLen < 128:
            record += chr(nLen)
        else:
            record += chr((nLen >> 24) | 0x80) \
                      + chr((nLen >> 16) & 0xFF) \
                      + chr((nLen >> 8) & 0xFF) \
                      + chr(nLen & 0xFF)
        if vLen < 128:
            record += chr(vLen)
        else:
            record += chr((vLen >> 24) | 0x80) \
                      + chr((vLen >> 16) & 0xFF) \
                      + chr((vLen >> 8) & 0xFF) \
                      + chr(vLen & 0xFF)
        return record + str(name) + str(value)

    def __decodeFastCGIHeader(self, stream):
        header = dict()
        header['version'] = ord(stream[0])
        header['type'] = ord(stream[1])
        header['requestId'] = (ord(stream[2]) << 8) + ord(stream[3])
        header['contentLength'] = (ord(stream[4]) << 8) + ord(stream[5])
        header['paddingLength'] = ord(stream[6])
        header['reserved'] = ord(stream[7])
        return header

    def __decodeFastCGIRecord(self):
        header = self.sock.recv(int(self.__FCGI_HEADER_SIZE))
        if not header:
            return False
        else:
            record = self.__decodeFastCGIHeader(header)
            record['content'] = ''
            if 'contentLength' in record.keys():
                contentLength = int(record['contentLength'])
                buffer = self.sock.recv(contentLength)
                while contentLength and buffer:
                    contentLength -= len(buffer)
                    record['content'] += buffer
            if 'paddingLength' in record.keys():
                skiped = self.sock.recv(int(record['paddingLength']))
            return record

    def gen_request(self, nameValuePairs={}, post=''):
        requestId = random.randint(1, (1 << 16) - 1)
        request = ""
        beginFCGIRecordContent = chr(0) \
                                 + chr(self.__FCGI_ROLE_RESPONDER) \
                                 + chr(self.keepalive) \
                                 + chr(0) * 5
        request += self.__encodeFastCGIRecord(self.__FCGI_TYPE_BEGIN,
                                              beginFCGIRecordContent, requestId)
        paramsRecord = ''
        if nameValuePairs:
            for (name, value) in nameValuePairs.iteritems():
                # paramsRecord = self.__encodeNameValueParams(name, value)
                # request += self.__encodeFastCGIRecord(self.__FCGI_TYPE_PARAMS, paramsRecord, requestId)
                paramsRecord += self.__encodeNameValueParams(name, value)

        if paramsRecord:
            request += self.__encodeFastCGIRecord(self.__FCGI_TYPE_PARAMS, paramsRecord, requestId)
        request += self.__encodeFastCGIRecord(self.__FCGI_TYPE_PARAMS, '', requestId)

        if post:
            request += self.__encodeFastCGIRecord(self.__FCGI_TYPE_STDIN, post, requestId)
        request += self.__encodeFastCGIRecord(self.__FCGI_TYPE_STDIN, '', requestId)
        return request

    def __repr__(self):
        return "fastcgi connect host:{} port:{}".format(self.host, self.port)
