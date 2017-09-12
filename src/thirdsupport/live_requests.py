# coding: utf-8

import json
from tornado.httpclient import HTTPRequest
from yunxin import YunXinRequestBase
from collections import namedtuple
import logging


class LiveJsonTag:
    PushUrl = 'pushUrl'
    HttpPullUrl = 'httpPullUrl'
    HlsPullUrl = 'hlsPullUrl'
    RtmpPullUrl = 'rtmpPullUrl'
    ChannelId = 'cid'
    CreateTime = 'ctime'
    ChannelName = 'name'
    ErrorMsg = 'msg'
    Code = 'code'
    Result = 'ret'


class LiveRequestType(object):
    CreateChannel = 0
    ModifyChannel = 1
    DeleteChannel = 2
    ChannelDetail = 3
    ChannelList = 4
    GetPushAddress = 5
    RecordChannel = 6
    ForbidChannel = 7
    ForbidChannels = 8
    ResumeChannel = 9
    ResumeChannels = 10
    ResetChannel = 11


LiveRequestSetting = namedtuple('LiveRequestSetting', ['url', 'body_ptn'])


class LiveRequests(YunXinRequestBase):
    CHANNEL_TYPE = ('rtmp', 'hls', 'http')
    SORT_TYPE = ('DESC', 'ASC')
    SORT_FIELD = ('ctime', 'cid', 'name', 'status', 'duration')
    '''
    response = yield client.fetch(request, raise_error=False)
    '''

    def __init__(self, app_key, app_secret, host):
        super(LiveRequests, self).__init__(app_key, app_secret, 'application/json;charset=utf-8')
        self.host = host
        self.mapping = {
            LiveRequestType.CreateChannel: LiveRequestSetting('%s/app/channel/create' % self.host,
                                                              '{"name":"%s", "type":%d}'),
            LiveRequestType.ModifyChannel: LiveRequestSetting('%s/app/channel/update' % self.host,
                                                              '{"name":"%s", "cid":"%s", "type":%d}'),
            LiveRequestType.DeleteChannel: LiveRequestSetting('%s/app/channel/delete' % self.host,
                                                              '{"cid":"%s"}'),
            LiveRequestType.ChannelDetail: LiveRequestSetting('%s/app/channelstats' % self.host,
                                                              '{"cid":"%s"}'),
            LiveRequestType.ChannelList: LiveRequestSetting('%s/app/channellist' % self.host,
                                                            '{"records":%d, "pnum":%d, "ofield": "%s", "sort": %d}'),
            LiveRequestType.GetPushAddress: LiveRequestSetting('%s/app/address' % self.host, '{"cid":"%s"}'),
            LiveRequestType.RecordChannel: LiveRequestSetting('%s/app/setAlwaysRecord' % self.host,
                                                              '{"cid": "%s","needRecord":%d,"format":0,"duration":%d, "filename":"%s"}'),
            LiveRequestType.ForbidChannel: LiveRequestSetting('%s/app/channel/pause' % self.host,
                                                              '{"cid":"%s"}'),
            LiveRequestType.ForbidChannels: LiveRequestSetting('%s/app/channellist/pause' % self.host,
                                                               '{"cidList":%s}'),
            LiveRequestType.ResumeChannel: LiveRequestSetting('%s/app/channel/resume' % self.host,
                                                              '{"cid":"%s"}'),
            LiveRequestType.ResumeChannels: LiveRequestSetting('%s/app/channellist/resume' % self.host,
                                                               '{"cidList":%s}'),
            LiveRequestType.ResetChannel: LiveRequestSetting('%s/app/address' % self.host,
                                                             '{"cid":"%s"}'),
        }

    def make_request(self, request_type, tuple_args):
        tmp = self.mapping[request_type]
        headers = self.make_header()
        body = tmp.body_ptn % tuple_args
        logging.debug(
            'curl -X POST "%s" -d\'%s\' %s',
            tmp.url, body, ' '.join(['-H "{}:{}"'.format(key, val) for key, val in headers]))
        return HTTPRequest(url=tmp.url, method='POST', body=body, headers=headers)

    def make_create_channel_request(self, channel_name, channel_type=0):
        return self.make_request(LiveRequestType.CreateChannel, (channel_name, channel_type))

    def make_modify_channel_request(self, channel_id, channel_name, channel_type=0):
        return self.make_request(LiveRequestType.ModifyChannel, (channel_id, channel_name, channel_type))

    def make_delete_channel_request(self, channel_id):
        return self.make_request(LiveRequestType.DeleteChannel, channel_id)

    def make_get_channel_detail_request(self, channel_id):
        return self.make_request(LiveRequestType.ChannelDetail, channel_id)

    def make_get_channel_list_request(self, size=10, page_index=1, order_field='ctime', sort='DESC'):
        return self.make_request(LiveRequestType.ChannelList,
                                 (size, page_index, order_field, self.SORT_TYPE.index(sort)))

    def make_refresh_push_addr_request(self, channel_id):
        return self.make_request(LiveRequestType.GetPushAddress, channel_id)

    def make_record_channel_request(self, channel_id, filename, need_record=False, duration=20):
        return self.make_request(LiveRequestType.RecordChannel,
                                 (channel_id, '1' if need_record else '0', duration, filename))

    def make_forbid_channel_request(self, channel_id):
        return self.make_request(LiveRequestType.ForbidChannel, channel_id)

    def make_forbid_channels_request(self, channel_id_list):
        return self.make_request(LiveRequestType.ForbidChannels, json.dumps(channel_id_list))

    def make_resume_channel_request(self, channel_id):
        return self.make_request(LiveRequestType.ResumeChannel, channel_id)

    def make_resume_channels_request(self, channel_id_list):
        return self.make_request(LiveRequestType.ResumeChannels, json.dumps(channel_id_list))

    def make_reset_channel_request(self, channel_id):
        return self.make_request(LiveRequestType.ResetChannel, channel_id)

    def parse_response(self, response):
        ret = None
        try:
            if response.error:
                logging.warning('receive bad response[%s]' % response.body)
            else:
                ret = json.loads(response.body)
                if ret[LiveJsonTag.Code] != 200:
                    logging.warning('receive bad code for response[%s]' % response.body)
                    return None
        except Exception:
            logging.exception('Decode body[%s] to json failed.' % response.body)
        return ret
