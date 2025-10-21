# 医院客户信息自动采集系统 - 快速启动指南

## 📋 系统简介

这是一个自动化采集医院系统软硬件建设信息的工具，主要数据来源包括：
- 福建省政府采购网
- 医院官网和公众号
- 供应商公众号
- 其他公开渠道

**核心功能**：
1. ✅ 自动采集政府采购公告
2. ✅ 提取系统建设信息
3. ✅ 整合到客户档案Excel
4. ✅ AI辅助信息结构化（可选）
5. ✅ 定时自动更新

---

## 🚀 快速开始（5分钟上手）

### 第一步：环境准备

```bash
# 1. 确保安装了 Python 3.8+
python --version

# 2. 创建虚拟环境（推荐）
python -m venv venv

# Windows激活
venv\Scripts\activate

# Mac/Linux激活
source venv/bin/activate

# 3. 安装依赖（核心包）
pip install pandas openpyxl requests beautifulsoup4 lxml
```

### 第二步：运行采集程序

```bash
# 运行政府采购网爬虫
python gov_procurement_crawler.py
```

程序会自动：
1. 从你的客户档案Excel读取医院列表
2. 搜索每家医院的采购信息（近1年）
3. 保存结果到 `政府采购数据_日期.xlsx`

**预计耗时**: 10-30分钟（取决于医院数量）

### 第三步：数据整合

```bash
# 将采集的数据整合到客户档案
python data_integrator.py
```

程序会自动：
1. 读取采集的政府采购数据
2. 更新客户档案中的"软硬件建设情况"字段
3. 生成更新报告
4. 保存为新的Excel文件（原文件不会被覆盖）

---

## 📁 项目文件说明

```
医院客户信息自动采集系统/
│
├── gov_procurement_crawler.py      # 核心爬虫程序
├── data_integrator.py             # 数据整合程序
├── requirements.txt               # 依赖包列表
├── 医院客户信息自动化收集方案.md  # 完整方案文档
└── README.md                      # 本文件
```

---

## 🔧 详细配置

### 配置1：修改搜索时间范围

编辑 `gov_procurement_crawler.py`，找到 `main()` 函数：

```python
# 默认搜索最近365天
crawler.search_hospital_procurement(hospital, days_back=365)

# 改为搜索最近2年
crawler.search_hospital_procurement(hospital, days_back=730)
```

### 配置2：调整系统关键词

在 `gov_procurement_crawler.py` 中找到 `system_keywords`：

```python
self.system_keywords = {
    'OA系统': ['OA', '办公自动化', '协同办公'],
    'HIS系统': ['HIS', '医院信息系统'],
    # 添加更多关键词
    '检验系统': ['LIS', '检验信息系统'],
}
```

### 配置3：启用AI增强功能（可选）

```bash
# 1. 安装AI库
pip install anthropic

# 2. 设置API Key
export ANTHROPIC_API_KEY='your-key-here'  # Mac/Linux
set ANTHROPIC_API_KEY=your-key-here       # Windows

# 3. 在代码中启用AI
# 编辑 gov_procurement_crawler.py，在 main() 中设置 use_ai = True
```

---

## 📊 实际网站适配指南

⚠️ **重要提示**: 提供的代码是**示例框架**，需要根据实际网站的HTML结构进行调整。

### 适配步骤

#### 1. 分析目标网站结构

```bash
# 访问福建省政府采购网
# 观察搜索结果页面的HTML结构
# 使用浏览器开发者工具（F12）查看元素
```

#### 2. 修改解析代码

在 `gov_procurement_crawler.py` 中找到 `_parse_procurement_item()` 函数：

```python
def _parse_procurement_item(self, item):
    # 根据实际HTML修改以下选择器
    title = item.find('a', class_='实际的class名称').text.strip()
    link = item.find('a', class_='实际的class名称')['href']
    pub_date = item.find('span', class_='实际的class名称').text.strip()
    # ...
```

#### 3. 测试单个医院

```python
# 在 main() 中只测试一家医院
hospitals = ['福州大学附属省立医院']
crawler.search_hospital_procurement(hospitals[0], days_back=30)
```

#### 4. 逐步扩展

确认单个医院采集成功后，再扩展到更多医院。

---

## 🌐 支持的数据源

### 已实现
- ✅ 福建省政府采购网（需适配）

### 待实现（参考完整方案文档）
- ⭐ 中国政府采购网
- ⭐ 各地市政府采购网
- ⭐ 医院官网
- ⭐ 微信公众号（通过搜狗微信搜索）

---

## 🤖 AI功能说明

### 基础版（无需AI）
- ✅ 自动采集采购公告
- ✅ 提取基本信息（标题、金额、供应商）
- ✅ 整合到Excel

### AI增强版（需要API Key）
- ✅ 智能理解采购内容
- ✅ 自动提取软硬件配置
- ✅ 识别技术架构
- ✅ 结构化输出

**成本预估**: 每条采购公告约 0.01-0.03 元（Claude API）

---

## 📅 定时任务设置

### 方式1：使用 schedule 库（推荐初学者）

在 `gov_procurement_crawler.py` 最后添加：

```python
import schedule
import time

def daily_job():
    print(f"开始定时任务: {datetime.now()}")
    main()

# 每天凌晨2点运行
schedule.every().day.at("02:00").do(daily_job)

# 或者每周一运行
# schedule.every().monday.at("02:00").do(daily_job)

print("定时任务已启动，每天2点自动运行...")
while True:
    schedule.run_pending()
    time.sleep(3600)  # 每小时检查一次
```

### 方式2：使用系统定时任务

**Linux/Mac (cron)**:
```bash
# 编辑 crontab
crontab -e

# 添加任务（每天2点运行）
0 2 * * * cd /path/to/project && /path/to/python gov_procurement_crawler.py >> crawler.log 2>&1
```

**Windows (任务计划程序)**:
1. 打开"任务计划程序"
2. 创建基本任务
3. 设置触发器（每天2点）
4. 操作：启动程序 `python.exe`
5. 参数：`gov_procurement_crawler.py`

---

## 🐛 常见问题

### Q1: 运行报错 "No module named 'xxx'"
```bash
# 安装缺失的库
pip install xxx
```

### Q2: 采集不到数据
1. 检查网站是否可访问
2. 查看网站HTML结构是否变化
3. 调整 `_parse_procurement_item()` 中的选择器

### Q3: Excel打不开或格式错误
```bash
# 重新安装 openpyxl
pip uninstall openpyxl
pip install openpyxl==3.1.2
```

### Q4: 请求被阻止（403/429错误）
```python
# 增加请求间隔
time.sleep(5)  # 从2秒改为5秒

# 使用代理IP（需额外配置）
proxies = {'http': 'http://proxy:port'}
requests.get(url, proxies=proxies)
```

### Q5: AI提取失败
1. 检查API Key是否正确
2. 检查网络连接
3. 查看API使用额度

---

## 💡 使用技巧

### 技巧1：分批采集
如果医院数量很多，建议分批采集：

```python
# 每次采集10家
for i in range(0, len(hospitals), 10):
    batch = hospitals[i:i+10]
    for hospital in batch:
        crawler.search_hospital_procurement(hospital)
    # 批次间休息10分钟
    time.sleep(600)
```

### 技巧2：增量更新
只采集最近的数据：

```python
# 只搜索最近7天
crawler.search_hospital_procurement(hospital, days_back=7)
```

### 技巧3：数据去重
在 `data_integrator.py` 中添加去重逻辑：

```python
def remove_duplicates(data):
    seen = set()
    unique_data = []
    for item in data:
        key = (item['title'], item['pub_date'])
        if key not in seen:
            seen.add(key)
            unique_data.append(item)
    return unique_data
```

### 技巧4：监控日志
添加详细日志记录：

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('crawler.log'),
        logging.StreamHandler()
    ]
)
```

---

## 📈 性能优化

### 优化1：并发采集
使用多线程加速：

```python
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=3) as executor:
    executor.map(crawler.search_hospital_procurement, hospitals)
```

### 优化2：缓存机制
避免重复采集：

```python
import hashlib
import json

def cache_result(url, data):
    cache_key = hashlib.md5(url.encode()).hexdigest()
    with open(f'cache/{cache_key}.json', 'w') as f:
        json.dump(data, f)
```

### 优化3：数据库存储
对于大量数据，使用数据库：

```python
import sqlite3

conn = sqlite3.connect('procurement.db')
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS procurement (
        id INTEGER PRIMARY KEY,
        hospital TEXT,
        title TEXT,
        amount TEXT,
        pub_date TEXT
    )
''')
```

---

## 🔒 安全与合规

### 遵守 robots.txt
```bash
# 检查网站是否允许爬取
curl http://ccgp-fujian.gov.cn/robots.txt
```

### 控制请求频率
```python
# 建议每个请求间隔3-5秒
time.sleep(3)
```

### 设置超时
```python
response = requests.get(url, timeout=10)
```

### 使用User-Agent
```python
headers = {
    'User-Agent': 'Mozilla/5.0 ...'
}
```

---

## 📧 获取帮助

如果遇到问题：
1. 查看完整方案文档：`医院客户信息自动化收集方案.md`
2. 检查错误日志：`crawler.log`
3. 测试单个医院是否正常工作
4. 验证网站是否可访问

---

## 📝 更新日志

### v1.0 (2025-10-19)
- ✅ 初始版本发布
- ✅ 实现政府采购网爬虫框架
- ✅ 实现数据整合功能
- ✅ 支持AI增强提取（可选）

---

## 🎯 下一步计划

1. 添加更多数据源（医院官网、公众号）
2. 实现Web可视化界面
3. 增加数据验证和去重
4. 优化AI提取准确度
5. 添加移动端提醒功能

---

## ⚖️ 免责声明

本工具仅供学习和内部使用。使用时请：
- 遵守网站服务条款
- 控制访问频率
- 不要用于商业目的
- 数据仅供参考

---

**祝使用愉快！有问题欢迎反馈。**
# crm_spyder
