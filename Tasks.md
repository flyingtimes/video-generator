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


创建lib\gamma_api.py实现下述功能：
根据用户给出的input/prompt.txt文件的内容，调用下面的接口生成pptx
下面是接口的示例文档
```
import requests

url = "https://public-api.gamma.app/v0.2/generations"

payload = {
    "inputText": "string",
    "textMode": "generate",
    "format": "presentation",
    "themeName": "企业汇报模版",
    "numCards": 10,
    "cardSplit": "auto",
    "additionalInstructions": "Make the titles catchy",
    "exportAs": "pptx",
    "textOptions": {
        "amount": "brief",
        "tone": "professional",
        "audience": "college students",
        "language": "zh-cn"
    },
    "imageOptions": {
        "source": "aiGenerated",
        "model": "",
        "style": "插画风格"
    },
    "cardOptions": { "dimensions": "16*9" },
    "sharingOptions": {
        "workspaceAccess": "string",
        "externalAccess": "string"
    }
}
headers = {
    "accept": "application/json",
    "Content-Type": "application/json",
    "X-API-KEY": "you gamma api key"
}

response = requests.post(url, json=payload, headers=headers)

print(response.text)
```
其中inputText是prompts.txt的内容，X-API_KEY从.env环境文件读取
@main.py 添加一个可以通过参数单独调用的功能，使用lib\gamma_api.py生成pptx。


@lib\gamma_api.py generate_pptx函数会获得接口的返回值，里面有个generationId代表待下载的pptx文件的id，返回值示例如下：
```
{
  "generationId": "xxxxxxxxxxx"
}
```
通过以下接口调用可以获得这个任务当前的状态：
```
import requests

url = "https://public-api.gamma.app/v0.2/generations"

headers = {
    "accept": "application/json",
    "Content-Type": "application/json",
    "X-API-KEY": "123"
}

response = requests.post(url, headers=headers)

print(response.text)
```
返回的内容格式如下：
```
{
  "generationId": "XXXXXXXXXXX",
  "status": "completed",
  "gammaUrl": "https://gamma.app/docs/yyyyyyyyyy",
  "credits": {
    "deducted": 150,
    "remaining": 3000
  }
}
```
@lib\gamma_api.py 每30秒调用一次这个接口获取状态，如果status是completed，那么就使用requests从gammaUrl中下载这个pptx到input/文件夹中

@input\prompt.txt @lib\gamma_api.py _download_file函数在下载完pptx以后，在下载完的pptx文件中添加备注文字。备注文字中的内容来自于prompt.txt中的内容。prompt.txt文件中用"\n---\n"分隔每一页的内容，请解析并将内容分别插入每一页pptx中
```

```

请仿照一下内容，创建一个lib\glm_api.py 文件，提供基于prompt和用户输入返回大模型调用结果的功能
```
from openai import OpenAI
from dotenv import load_dotenv
import os
from pathlib import Path
load_dotenv()

def talk_to_ai(prompt_file,user_input):

    client = OpenAI(
        api_key=os.getenv("GLM_API_KEY") ,
        base_url="https://open.bigmodel.cn/api/paas/v4/"
    )

    file_path = Path(prompt_file)
        if not file_path.exists():
            raise FileNotFoundError(f"提示词文件不存在: {file_path}")

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()

            if not content:
                raise ValueError(f"提示词文件为空: {file_path}")
            completion = client.chat.completions.create(
                model="GLM-4.5-Flash",
                messages=[
                    {"role": "system", "content": "你是一个聪明且富有创造力的小说作家"},
                    {"role": "user", "content": "请你作为童话故事大王，写一篇短篇童话故事"}
                ],
                top_p=0.7,
                temperature=0.9
            )

            return completion.choices[0].message.content
        except Exception as e:
            raise Exception(f"读取提示词文件时发生错误: {str(e)}")

    
```
请给@lib\runninghub_api.py添加一个create_cover(title)的功能，根据标题内容创建一个图片，并调用@lib\running_hub_api.py的查询、轮询、下载功能（参照已有的实现方式来做），将图片保存在input\cover.jpg(如果已存在则覆盖),然后更新assets\biliconfig.yaml中cover字段为"..\input\cover.jpg"。这个功能的调用方式参考下面curl的代码，其中webappid和apikey请在.env文件中cover_webappId和RUNNINGHUB_API_KEY读取，请用requests方式来实现：
```
curl --location --request POST 'https://www.runninghub.cn/task/openapi/quick-ai-app/run' \
--header 'Host: www.runninghub.cn' \
--header 'Content-Type: application/json' \
--data-raw '{
    "webappId": "1959831828515467265",
    "apiKey": "481e7653f5334058bd642478fdca8ddd",
    "quickCreateCode": "006",
    "nodeInfoList": [
        {
            "nodeId": "889",
            "nodeName": "EmptyLatentImage",
            "fieldName": "batch_size",
            "fieldType": "INT",
            "fieldValue": "1",
            "description": "生成张数"
        },
        {
            "nodeId": "887",
            "nodeName": "ImpactSwitch",
            "fieldName": "select",
            "fieldType": "SWITCH",
            "fieldValue": "2",
            "description": "设置比例"
        },
        {
            "nodeId": "923",
            "nodeName": "easy anythingIndexSwitch",
            "fieldName": "index",
            "fieldType": "SWITCH",
            "fieldValue": "1",
            "description": "文本输入方式"
        },
        {
            "nodeId": "876",
            "nodeName": "JjkText",
            "fieldName": "text",
            "fieldType": "STRING",
            "fieldValue": "为一个视频制作封面,视频的标题为：{title},背景图案显示标题内容相关的画面，前景是一个45度旋转的黄色矩形框，里面写着{title}"
        }
    ]
}'
```
给@lib\glm_api.py中的talk_to_ai功能添加一个model参数，默认是GLM-4.5-Flash
给@main.py添加一个命令行功能prepare，功能如下：
使用@lib\glm_api.py中的talk_to_ai功能，使用assets\gen_title_prompt.prompt
作为prompt，input\essay.txt作为用户输入，获取标题，并将标题内容写入input\
title.txt,并调用@lib_runninghub_api.py的create_cover(title)功能创建封面。

将@main.py的prepare_title_and_cover改名为prepare_title_and_cover_and_content,增加一个page参数
在生成title和cover以后，增加以下功能：
1、使用@lib\glm_api.py中的talk_to_ai功能，使用assets\split_content.prompt作为prompt，将参数page填入split_content.prompt中。
input\essay.txt作为用户输入，将一篇长的文章拆分成多页内容，并将内容写入input\prompt.txt
2、使用@lib\glm_api.py中的talk_to_ai功能，指定模型使用glm-4.6，使用assets\gen_scripts.prompt作为prompt，
input\prompt.txt作为用户输入，获得每一页的讲稿，并将内容写入input\scripts.txt