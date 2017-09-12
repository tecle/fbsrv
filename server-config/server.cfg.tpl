# third config
access.weixin.app_id=
access.weixin.app_secret=
access.weixin.api_domain=https://api.weixin.qq.com


# common config
common.db_layer.host=
common.server.mode=
common.max_async_client=35
common.pay_secret=

# celery config
celery.broker=redis://:password@ipv4:port/db
celery.concurrency=2
celery.loglevel=INFO
celery.logfile=/var/log/celery/celery.log

# business config
business.login_config_file=reward_cfg.json
business.daily_task_config_file=daily_task_cfg.json

# db config
db.host=
db.port=3306
db.name=
db.user=
db.password=
db.pollsize=8

# redis config
redis.host=
redis.port=
redis.pwd=
redis.db=
redis.cfg_channel=CONFIG_CHANNEL
redis.cfg_key=Srv.Cfg

# yunxin config
yx.app_key=
yx.app_secret=
yx.host=https://api.netease.im
yx.super_user=0

# yunxin video
yx.video.app_key=
yx.video.secret=
yx.video.host=https://vcloud.163.com

# credits settings
credits.publish_reward=2/10
credits.comment_reward=1/10
credits.chat_reward=2/10
credits.watch_reward=4/40
credits.login_reward=10/10

# qiniu setting
qiniu.app.key=
qiniu.app.secret=
# bucket conf starts with 1, default upload bucket is qiniu.bucket.name.1
qiniu.bucket.name.1=
qiniu.bucket.url.1=
qiniu.pic.timeout=300

# living
living.broadcast_interval=90000
living.special_user_count=3
living.special_user_level_limit=20
living.check_heartbeat_interval=60
living.live_alive_time=180
living.ws.host=
living.game.cfg_file=game_list.json
living.gift.cfg_file=gifts_config.json

# pay
pay.server.host=
pay.handler.max_db_thread=12
pay.alipay.pub_key_file=ali_pub_key.pem
pay.alipay.prv_key_file=ali_prv_key.pem
pay.alipay.app_id=
pay.alipay.api_gate=https://openapi.alipaydev.com/gateway.do
pay.weixin.app_id=
pay.weixin.mch_id=
pay.weixin.secret=
pay.weixin.api_addr=https://api.mch.weixin.qq.com
pay.cargo.config_file=cargo_cfg.json
pay.cargo.cfg_field_name=cargo
