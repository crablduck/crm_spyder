# 福建省政府采购网爬虫

这是一个专门用于爬取福建省政府采购网（https://zfcg.czt.fujian.gov.cn）公告信息的Python爬虫程序。

## 功能特性

### 核心功能
- ✅ **自动验证码识别**: 使用ddddocr库自动识别并输入验证码
- ✅ **智能搜索**: 支持按采购单位名称搜索（如"医院"）
- ✅ **数据提取**: 提取搜索结果列表和详情页面内容
- ✅ **分页处理**: 自动处理多页搜索结果
- ✅ **合同信息解析**: 专门解析合同公告的结构化信息
- ✅ **附件下载**: 识别并记录PDF、DOC等附件链接
- ✅ **多格式输出**: 支持JSON和CSV格式数据导出

### 数据字段

#### 搜索结果数据
- `district`: 区划
- `procurement_method`: 采购方式
- `procurement_unit`: 采购单位
- `title`: 公告标题
- `detail_url`: 详情页链接
- `publish_time`: 发布时间
- `crawl_time`: 爬取时间

#### 详情页数据
- `url`: 详情页URL
- `title`: 公告标题
- `publish_time`: 发布时间
- `content`: 正文内容
- `contract_info`: 合同信息（如果是合同公告）
- `attachments`: 附件列表
- `crawl_time`: 爬取时间

#### 合同信息字段
- `contract_number`: 合同编号
- `contract_name`: 合同名称
- `project_number`: 项目编号
- `buyer`: 采购人（甲方）
- `supplier`: 供应商（乙方）
- `contract_amount`: 合同金额
- `performance_period`: 履约期限

## 安装依赖

```bash
pip install -r requirements.txt
```

### 依赖说明
- `selenium`: 网页自动化操作
- `beautifulsoup4`: HTML解析
- `ddddocr`: 验证码识别
- `requests`: HTTP请求
- `tqdm`: 进度条显示
- `lxml`: XML/HTML解析器

## 使用方法

### 基本使用

```bash
python fujian_procurement_crawler.py
```

程序会提示输入以下参数：
- 采购单位名称（默认：医院）
- 最大爬取页数（默认：全部）
- 是否提取详情页面（默认：是）
- 是否使用无头模式（默认：否）

### 编程调用

```python
from fujian_procurement_crawler import FujianProcurementCrawler

# 创建爬虫实例
crawler = FujianProcurementCrawler(
    headless=False,  # 是否无头模式
    max_pages=10     # 最大页数限制
)

# 运行爬虫
crawler.run(
    unit_name="医院",        # 搜索关键词
    extract_details=True    # 是否提取详情
)

# 手动关闭
crawler.close()
```

## 输出文件

程序会在当前目录创建以时间戳命名的文件夹，包含：

```
fujian_procurement_20241021_143022/
├── search_results.json    # 搜索结果JSON格式
├── search_results.csv     # 搜索结果CSV格式
└── detail_data.json       # 详情页数据JSON格式
```

## 配置说明

### Chrome浏览器设置
程序使用Chrome浏览器，需要确保：
1. 已安装Chrome浏览器
2. ChromeDriver在PATH中或与脚本同目录

### 验证码处理
- 程序会自动尝试识别验证码
- 如果自动识别失败，会提示手动输入
- 支持最多5次重试

### 反爬虫策略
- 请求间隔：每个详情页间隔1秒
- User-Agent伪装
- 自动处理验证码
- 定期保存数据防止丢失

## 注意事项

1. **合规使用**: 请遵守网站robots.txt和使用条款
2. **频率控制**: 避免过于频繁的请求
3. **数据用途**: 仅用于学习研究，不得用于商业用途
4. **网络环境**: 确保网络连接稳定
5. **浏览器版本**: 保持Chrome浏览器为最新版本

## 错误处理

程序包含完善的错误处理机制：
- 网络超时重试
- 验证码识别失败重试
- 页面加载异常处理
- 数据提取异常跳过
- 定期数据保存防止丢失

## 扩展功能

### 自定义搜索条件
可以修改`search_procurement_unit`方法添加更多搜索条件：
- 标题关键词
- 采购方式
- 项目编号
- 发布时间范围

### 数据过滤
可以在`extract_search_results`方法中添加数据过滤逻辑：
- 按金额范围过滤
- 按时间范围过滤
- 按采购方式过滤

### 导出格式
可以扩展`save_data`方法支持更多格式：
- Excel格式
- 数据库存储
- API推送

## 技术架构

```
FujianProcurementCrawler
├── __init__()           # 初始化浏览器和配置
├── solve_captcha()      # 验证码识别和输入
├── search_procurement_unit()  # 搜索功能
├── extract_search_results()   # 提取搜索结果
├── extract_detail_page()      # 提取详情页
├── extract_contract_info()    # 提取合同信息
├── get_total_pages()          # 获取总页数
├── go_to_next_page()          # 翻页操作
├── save_data()               # 数据保存
└── run()                     # 主运行流程
```

## 更新日志

### v1.0.0 (2024-10-21)
- 初始版本发布
- 支持基本的搜索和数据提取功能
- 自动验证码识别
- 多格式数据导出

## 许可证

本项目仅供学习研究使用，请遵守相关法律法规和网站使用条款。

## 联系方式

如有问题或建议，请通过以下方式联系：
- 提交Issue
- 发送邮件

---

**免责声明**: 本工具仅用于学习和研究目的，使用者需自行承担使用风险，并遵守相关法律法规。