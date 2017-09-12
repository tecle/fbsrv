## 变更记录

### v1.5.9

#### 新功能

1. 排行榜, 需要配置定时任务每日凌晨跑srvjobs.py

#### 新增配置
个推相关配置项

1. getui.host, 个推API网关
2. getui.app_id
3. getui.app_key
4. getui.app_secret
5. getui.master_secret

#### 数据库修改
1. 增加FailedOperation数据库, 记录服务器一些失败的操作
2. GameRoundsLogs表增加列sys_tax, 记录系统抽水
3. user_info_new表增加列location, 记录用户登录
4. Reaction表增加列status和ctime

#### 其它
1. 工程结构调整，celery app位置调整

### V1.5

#### 新增配置项
1. robot.opinion.token, 意见通知的钉钉机器人
2. robot.support.token, 客服支持的钉钉机器人
3. robot.url, 客服机器人的接口地址

#### 数据库修改
1. 新增Consultion数据库, 保存用户咨询信息
2. 修改Suggestion数据库, 保存用户建议


### V1.4

#### 增加配置项
1. app.cargo_cfg_file, 商品配置文件(当Redis中不存在时读取)
1. app.banner_cfg_file, 横幅配置文件(当Redis中不存在时读取)
1. app.ver_cfg_file, 版本配置文件(当Redis中不存在时读取)
1. living.game.rpc_host, 游戏rpc地址
1. 不再使用的配置:
<del>pay.cargo.cfg_field_name</del>,
<del>redis.cfg_channel</del>,
<del>redis.cfg_key</del>

#### 功能修改
1. /login/ver 返回数据结构修改，同时增加banner配置信息
2. 使用发布订阅模式更新banner配置以及version配置

### V1.3_0810

### 功能变化
1. 部分API不再需要两次请求，一次到位
2. 增加websocket模块，直播间游戏消息使用websocket，而不是云信的聊天室接口
3. 修改下注接口，可以同时对多个slot进行下注

### V1.3_0731

#### 增加配置项
1. db.poolsize, 多线程数据库操作的线程池大小
2. pay.cargo.cfg_field_name, 商品配置在Redis哈希key中的field名称
3. redis.cfg_key, Redis中业务相关配置的哈希key名称

#### 增加功能
1. 业务配置不再从本地读取, 而是从Redis中读取
2. 服务器使用Redis的发布订阅模式处理商品配置的修改, 做到一处修改, 同时生效
3. 推荐用户生成逻辑将过滤资料不完整的用户
4. 可以使用运维接口控制游戏冻结和解冻
5. 增加获取游戏列表接口