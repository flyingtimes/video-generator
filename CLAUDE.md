我喜欢使用uv管理python程序
所有的说明文档和注释请使用中文，和我的对话尽量使用中文
所有的工具类程序，包括mcp server，都放在项目根目录的tools目录下
所有的程序的输出路径为项目根目录的outputs目录
我使用本项目根目录下的.mcp.json作为所有mcp服务的配置文件，尽量不使用个人配置文件来配置mcp服务
我使用本项目根目录下的.env文件管理所有的apikey，其他程序对于配置的访问均使用这个.env文件

## 路径兼容性修复记录

**2025-10-30**: 完成跨平台路径兼容性修复
- 修复了lib/runninghub_api.py中的硬编码Windows路径问题
- 修复了配置文件assets/biliconfig.yaml中的路径格式
- 优化了多个Python文件中的路径拼接方式，改用Path对象
- 创建了lib/utils.py统一路径处理工具函数
- 确保项目在Windows和macOS/Linux系统上都能正常工作

### 主要修改内容
1. **硬编码路径修复**: 将Windows特定的双反斜杠路径格式改为跨平台兼容的正斜杠格式
2. **Path对象使用**: 在路径拼接时使用pathlib.Path对象替代字符串拼接
3. **工具函数创建**: 新建lib/utils.py提供safe_path、ensure_dir等跨平台路径处理函数
4. **配置文件标准化**: 统一配置文件中的路径格式，使用正斜杠分隔符