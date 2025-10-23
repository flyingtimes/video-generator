在characters目录下存在多个子目录，每个子目录名称代表一个数字人的名字。例如man
根据用户指定的名字选择不同的数字人的内容执行以下操作
1、检查该子目录，例如characters/man目录下是否存在一个referrence.json文件，如果已经存在则直接从json文件中读取voice、landscape,portrait,short的id，这个json的样例如下：
```
{
    "voice_id": "xxxx.mp3",
    "landscape_id": "xxxxx.png",
    "portrait_id": "xxxxx.png",
    "short_id": "xxxxx.png",
}
```
如果不存在，则调用
```
curl --location --request POST 'https://www.runninghub.cn/task/openapi/ai-app/run' \
--header 'Host: www.runninghub.cn' \
--header 'Content-Type: application/json' \
--data-raw '{
    "webappId": "1981030543280181249",
    "apiKey": "481e7653f5334058bd642478fdca8ddd",
    "nodeInfoList": [
        {
            "nodeId": "48",
            "fieldName": "image",
            "fieldValue": "a0e90e4cc0c85ceb3d9f17012c8ecefb2e7fe3508ab3e09892b1c15c969234f4.png",
            "description": "image"
        },
        {
            "nodeId": "47",
            "fieldName": "audio",
            "fieldValue": "007c991b216f73404eead02468903ce7400ad59e6f3971833556eca51ddb24e7.mp3",
            "description": "audio"
        },
        {
            "nodeId": "38",
            "fieldName": "text",
            "fieldValue": "我的汇报就到这里",
            "description": "text"
        }
    ]
}'
```
每次调用获取的fileName请提取后，用以下格式生成在数字人文件的目录下，名字为reference.json:
```
{
    "voice_id": "xxxx.mp3",
    "landscape_id": "xxxxx.png",
    "portrait_id": "xxxxx.png",
    "short_id": "xxxxx.png",
}
```
请添加lib/runninghub_api.py,实现上述逻辑
请添加batch_process_upload.py 完成数字人man的上传

给lib/runninghub_api.py添加一个gen_short_Video函数，将数字人的short.png,refence.mp3,还有一个字符串传递给下面的接口（curl格式，请改成用requests）：
```
curl --location --request POST 'https://www.runninghub.cn/task/openapi/ai-app/run' \
--header 'Host: www.runninghub.cn' \
--header 'Content-Type: application/json' \
--data-raw '{
    "webappId": "1981030543280181249",
    "apiKey": "481e7653f5334058bd642478fdca8ddd",
    "nodeInfoList": [
        {
            "nodeId": "48",
            "fieldName": "image",
            "fieldValue": "a0e90e4cc0c85ceb3d9f17012c8ecefb2e7fe3508ab3e09892b1c15c969234f4.png",
            "description": "image"
        },
        {
            "nodeId": "47",
            "fieldName": "audio",
            "fieldValue": "007c991b216f73404eead02468903ce7400ad59e6f3971833556eca51ddb24e7.mp3",
            "description": "audio"
        },
        {
            "nodeId": "38",
            "fieldName": "text",
            "fieldValue": "我的汇报就到这里",
            "description": "text"
        }
    ]
}'
```
给lib/runninghub_api.py的gen_short_Video函数添加一个输入参数mode，mode可以是"short","landscape","portrait"中的一种
如果mode是short，则对应的webappId记录在.env文件中的short_webappId
如果mode是portrait，则对应的webappId记录在.env文件中的portrait_webappId
如果mode是landscape，则对应的webappId记录在.env文件中的landscape_webappId


给lib/runninghub_api.py添加一个gen_slide_video函数，第一个输入是一个数字，代表slides中的指定png图片。如slides/{num}.png，第二个输入是字符串，其内容是slides/{num}.txt中的内容。
然后调用gen_short_Video的short模式，生成一个视频生成的任务。记录下这个任务的taskId并将这个id写入slides/{num}.task
通过以下接口，每10秒获取一次这个taskId任务的状态，如果msg的值是success，则调用下载接口将文件写入slides/{num}.mp4。 
上面提到的1是个变量，由gen_slide_video第一个参数决定
下面是taskId查询接口（curl格式，请改成用requests）：
```
curl --location --request POST 'https://www.runninghub.cn/task/openapi/outputs' \
--header 'Host: www.runninghub.cn' \
--header 'Content-Type: application/json' \
--data-raw '{
    "apiKey": "请输入自己的apiKey",
    "taskId": "1904152026220003329"
}'
```
返回的格式是这样的：
```
{
    "code": 0,
    "msg": "success",
    "data": [
        {
            "fileUrl": "https://rh-images.xiaoyaoyou.com/de0db6f2564c8697b07df55a77f07be9/output/ComfyUI_00033_hpgko_1742822929.png",
            "fileType": "png",
            "taskCostTime": "83",
            "nodeId": "12",
            "thirdPartyConsumeMoney": null,
            "consumeMoney": null,
            "consumeCoins": "17"
        }
    ]
}
```
当msg的值是success的时候，代表任务执行成功，解析fileUrl的内容，并调用requests下载到slides/{num}.mp4,并删除slides/{num}.task
当msg的值是APIKEY_TASK_IS_RUNNING的时候,代表任务还在执行，继续等待。
如果msg出现其他值，代表任务失败了，则再执行一次，超过3次程序停止

@batch_process_pdf.py @batch_process_ppt.py @batch_process_slides.py 参考这三个程序的代码。
我希望创建一个main.py程序，完成以下任务：
1、首先向用户提问，是否需要清空slides和output中的所有文件，如果是的话就清除，如果回答否则不做处理。
2、处理input中的第一个pdf，参考@batch_process_pdf.py
3、处理input中的这个pdf同名的ppt或者pptx,参考@batch_process_ppt.py
4、生成silde的video，参考@test_gen_video.py
5、批量处理slides，参考@batch_process_slides.py
我还希望上面的5个步骤可以通过参数单独执行
还有一个上传数字人的操作，参考@batch_process_upload.py,这个操作只能通过参数单独执行