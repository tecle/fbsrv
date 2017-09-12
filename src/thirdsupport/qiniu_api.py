# coding: utf-8

import logging
from qiniu import Auth, put_file, etag


class QiniuApi(object):
    def __init__(self, key, secret, bucket_info, invalid_time=30):
        '''
        :param key: app_key
        :param secret: app_secret
        :param bucket_info: [(bucket_name, bucket_url), ...], notice: first tuple is set to default upload bucket
        :param invalid_time: max use time(s).
        '''
        self.auth = Auth(key, secret)
        self.qiniu_upload_policy = {
            'returnBody': '{"origin_name": $(fname),"cloud_name":$(key),"bucket":$(bucket)}',
            "detectMime": 3,
            "mimeLimit": 'image/*'
        }
        self.bucket_mapping = {}
        for item in bucket_info:
            self.bucket_mapping[item[0]] = item[1]
        self.upload_bucket = bucket_info[0][0]
        self.invalid_time = invalid_time

    def upload_file(self, f, bucket, key):
        logging.debug('upload file:[%s]->[%s]' % (f, key))
        # 生成上传 Token，可以指定过期时间等
        token = self.auth.upload_token(bucket, key, 3600)
        out = "{}:{}".format(bucket, key)
        # 要上传文件的本地路径
        ret, info = put_file(token, key, f)
        logging.debug('upload result:[{}],[{}]'.format(ret, info))
        if ret['key'] != key or ret['hash'] != etag(f):
            logging.warning('upload failed.')
            return None
        return out

    def get_download_url(self, bucket, pic, style=None):
        '''
        :param bucket: bucket name
        :param pic: pic name
        :param style: (mode, width, height), if width/height is 0 or None, then it will not set to url.
        :return: url
        '''
        if not style:
            url = '%s/%s?imageslim' % (self.bucket_mapping[bucket], pic)
        elif not style[1]:
            url = '%s/%s?imageView2/%d/h/%d' % (self.bucket_mapping[bucket], pic, style[0], style[2])
        elif not style[2]:
            url = '%s/%s?imageView2/%d/w/%d' % (self.bucket_mapping[bucket], pic, style[0], style[1])
        else:
            url = '%s/%s?imageView2/%d/w/%d/h/%d' % (self.bucket_mapping[bucket], pic, style[0], style[1], style[2])
        return self.auth.private_download_url(url, self.invalid_time)

    def get_upload_url(self, file_name):
        return self.auth.upload_token(
            self.upload_bucket, key=file_name, expires=self.invalid_time, policy=self.qiniu_upload_policy)

    def get_pub_url(self, avatar_str):
        if not avatar_str:
            return ''
        if avatar_str.startswith('http:/'):
            return avatar_str
        parts = avatar_str.split(':')
        if len(parts) != 2:
            logging.warning('Invalid pic str[{}]'.format(avatar_str))
            return ''
        return '{}/{}'.format(self.bucket_mapping.get(parts[0], 'http://unknown.com'), parts[1])

    def get_pub_urls(self, pics_str, default=tuple()):
        '''
        :param pics_str: x:y.jpg,x1:y1.jpg
        :return: ['url', 'url1]
        '''
        if not pics_str:
            return default
        pics = pics_str.split(',')
        return [self.get_pub_url(pic) for pic in pics]
