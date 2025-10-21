#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
福建省政府采购网爬虫
Fujian Provincial Government Procurement Network Crawler

功能：
1. 自动识别和处理验证码
2. 搜索指定采购单位（如"医院"）的公告信息
3. 提取搜索结果列表数据
4. 爬取详情页面内容
5. 支持分页处理
6. 数据保存为JSON和CSV格式
"""

import time
import json
import csv
import os
import re
from datetime import datetime
from urllib.parse import urljoin, urlparse
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
from tqdm import tqdm


class FujianProcurementCrawler:
    def __init__(self, headless=False, max_pages=None):
        """
        初始化爬虫
        
        Args:
            headless (bool): 是否使用无头模式
            max_pages (int): 最大爬取页数，None表示爬取所有页面
        """
        self.base_url = "https://zfcg.czt.fujian.gov.cn"
        self.search_url = "https://zfcg.czt.fujian.gov.cn/maincms-web/xmgg?titleType=xmgg"
        self.detail_url_pattern = "https://zfcg.czt.fujian.gov.cn/maincms-web/articleDetail"  # 详情页URL模式
        self.max_pages = max_pages
        self.session = requests.Session()
        
        # 会话状态管理
        self.captcha_filled = False  # 验证码填写状态
        self.session_active = False  # 会话状态
        
        # 设置Chrome选项
        chrome_options = Options()
        if headless:
            chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 10)
        

        
        # 数据存储
        self.results = []
        self.detail_data = []
        
        # 创建输出目录
        self.output_dir = f"fujian_procurement_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        os.makedirs(self.output_dir, exist_ok=True)
        
        print(f"输出目录: {self.output_dir}")

    def check_captcha_status(self):
        """
        检查验证码状态
        
        Returns:
            str: 'filled' - 已填写, 'empty' - 未填写, 'error' - 检查失败
        """
        try:
            # 查找验证码输入框
            captcha_input = self.driver.find_element(By.XPATH, "//input[@placeholder='请输入验证码']")
            captcha_value = captcha_input.get_attribute('value')
            
            if captcha_value and captcha_value.strip():
                print(f"✅ 检测到已填写的验证码: {captcha_value}")
                return 'filled'
            else:
                print("⚠️  验证码输入框为空")
                return 'empty'
                
        except Exception as e:
            print(f"检查验证码状态失败: {e}")
            return 'error'

    def wait_for_captcha_input(self, force_input=False):
        """
        等待用户输入验证码
        
        Args:
            force_input (bool): 是否强制重新输入验证码
        """
        # 检查是否已经填写过验证码且会话仍然活跃
        if self.captcha_filled and self.session_active and not force_input:
            print("✅ 验证码已填写且会话活跃，跳过验证码输入")
            return
        
        print("\n" + "="*50)
        print("🔐 验证码输入")
        print("="*50)
        
        # 通过终端获取用户输入的验证码
        captcha_code = input("请输入4位验证码: ").strip()
        
        if len(captcha_code) != 4 or not captcha_code.isdigit():
            print("❌ 验证码格式错误，请输入4位数字")
            return self.wait_for_captcha_input(force_input=True)
        
        try:
            # 查找验证码输入框并输入验证码
            captcha_input = self.wait.until(
                EC.presence_of_element_located((By.XPATH, "//input[contains(@placeholder, '验证码') or contains(@name, 'captcha') or contains(@id, 'captcha')]"))
            )
            
            # 清空输入框并输入验证码
            captcha_input.clear()
            captcha_input.send_keys(captcha_code)
            print(f"✅ 验证码 {captcha_code} 已输入")
            
            # 点击查询按钮 - 使用更灵活的选择器
            print("🔍 正在查找查询按钮...")
            search_button = None
            
            # 尝试多种选择器，针对Element UI框架的按钮结构
            selectors = [
                "//button[contains(.//span, '查询')]",  # 查找包含span且span文本包含"查询"的button
                "//button[.//span[text()='查询']]",     # 查找包含span且span文本等于"查询"的button
                "//button[contains(@class, 'el-button') and contains(.//span, '查询')]",  # Element UI按钮
                "//button[contains(text(), '查询')]",
                "//button[contains(normalize-space(text()), '查询')]",
                "//button[text()='查询 ']",
                "//button[normalize-space(text())='查询']",
                "//input[@type='button' and @value='查询']",
                "//input[@type='submit' and contains(@value, '查询')]"
            ]
            
            for i, selector in enumerate(selectors):
                try:
                    print(f"🔍 尝试选择器 {i+1}: {selector}")
                    search_button = self.driver.find_element(By.XPATH, selector)
                    print(f"✅ 找到查询按钮，使用选择器 {i+1}")
                    break
                except NoSuchElementException:
                    print(f"❌ 选择器 {i+1} 未找到按钮")
                    continue
            
            if search_button is None:
                print("❌ 所有选择器都未找到查询按钮，打印页面源码进行调试...")
                # 打印按钮相关的HTML
                buttons = self.driver.find_elements(By.TAG_NAME, "button")
                print(f"页面上找到 {len(buttons)} 个按钮:")
                for i, btn in enumerate(buttons):
                    print(f"按钮 {i+1}: text='{btn.text}', innerHTML='{btn.get_attribute('innerHTML')}'")
                raise Exception("无法找到查询按钮")
            
            # 点击按钮
            print("🖱️ 正在点击查询按钮...")
            search_button.click()
            print("✅ 已点击查询按钮")
            
            # 等待一下让页面响应
            time.sleep(2)
            
            # 检查是否有验证码错误提示
            try:
                error_msg = self.driver.find_element(By.XPATH, "//*[contains(text(), '验证码错误') or contains(text(), '验证码失效')]")
                if error_msg.is_displayed():
                    print("❌ 验证码错误或失效，请重新输入")
                    return self.wait_for_captcha_input(force_input=True)
            except NoSuchElementException:
                pass  # 没有错误提示，继续
            
            # 标记验证码已填写和会话活跃
            self.captcha_filled = True
            self.session_active = True
            
            print("✅ 验证码输入成功，继续执行...")
            return True
            
        except Exception as e:
            print(f"❌ 验证码输入失败: {e}")
            return self.wait_for_captcha_input(force_input=True)

    def search_procurement_unit(self, unit_name="医院"):
        """
        搜索指定采购单位
        
        Args:
            unit_name (str): 采购单位名称
            
        Returns:
            bool: 是否搜索成功
        """
        try:
            print(f"搜索采购单位: {unit_name}")
            
            # 打开搜索页面
            self.driver.get(self.search_url)
            time.sleep(3)
            
            # 输入采购单位
            unit_input = self.wait.until(
                EC.presence_of_element_located((By.XPATH, "//input[@placeholder='请输入采购单位']"))
            )
            unit_input.clear()
            unit_input.send_keys(unit_name)
            
            # 等待用户手动输入验证码（智能检测）
            if not self.wait_for_captcha_input():
                print("用户取消验证码输入")
                return False
            
            # 点击查询按钮 - 修复按钮定位
            try:
                # 尝试多种定位方式
                search_btn = None
                
                # 方式1：通过文本内容（包含空格）
                try:
                    search_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), '查询')]")
                except:
                    pass
                
                # 方式2：通过更精确的文本匹配
                if not search_btn:
                    try:
                        search_btn = self.driver.find_element(By.XPATH, "//button[normalize-space(text())='查询']")
                    except:
                        pass
                
                # 方式3：通过按钮类型和位置
                if not search_btn:
                    try:
                        buttons = self.driver.find_elements(By.TAG_NAME, "button")
                        for btn in buttons:
                            if "查询" in btn.text:
                                search_btn = btn
                                break
                    except:
                        pass
                
                if search_btn:
                    search_btn.click()
                    print("成功点击查询按钮")
                else:
                    print("未找到查询按钮")
                    return False
                    
            except Exception as e:
                print(f"点击查询按钮失败: {e}")
                return False
            
            # 等待搜索结果加载
            time.sleep(5)
            
            # 检查是否有搜索结果
            try:
                # 检查页面是否显示"请完成上方验证码操作"
                if "请完成上方验证码操作" in self.driver.page_source:
                    print("❌ 验证码验证失败，页面仍显示验证码提示")
                    return False
                
                # 检查是否有搜索结果表格
                result_table = self.wait.until(
                    EC.presence_of_element_located((By.XPATH, "//table//tbody//tr"))
                )
                print("✅ 搜索成功，找到结果表格")
                return True
                
            except TimeoutException:
                print("❌ 未找到搜索结果表格或页面加载超时")
                return False
                    
        except Exception as e:
            print(f"搜索失败: {e}")
            return False

    def extract_search_results(self):
        """
        提取当前页面的搜索结果
        
        Returns:
            list: 搜索结果列表
        """
        results = []
        
        try:
            # 首先检查是否有验证码错误提示
            try:
                captcha_error = self.driver.find_element(By.XPATH, "//*[contains(text(), '请完成上方验证码操作')]")
                if captcha_error.is_displayed():
                    print("❌ 检测到验证码错误：请完成上方验证码操作")
                    print("请在浏览器中重新输入验证码并点击查询按钮")
                    return []
            except NoSuchElementException:
                pass  # 没有验证码错误，继续执行
            
            # 等待表格加载
            try:
                table = self.wait.until(
                    EC.presence_of_element_located((By.XPATH, "//table//tbody"))
                )
            except TimeoutException:
                print("未找到搜索结果表格，可能需要重新搜索")
                return []
            
            # 提取表格行
            rows = table.find_elements(By.TAG_NAME, "tr")
            
            if not rows:
                print("表格中没有数据行")
                return []
            
            # 检查是否只有表头没有数据
            if len(rows) == 1:
                # 检查第一行是否包含表头信息
                first_row_text = rows[0].text.strip()
                if any(header in first_row_text for header in ['区划', '采购方式', '采购单位', '公告标题', '发布时间']):
                    print("⚠️  表格只有表头，没有实际数据。可能的原因：")
                    print("   1. 验证码未正确输入")
                    print("   2. 搜索条件没有匹配的结果")
                    print("   3. 页面加载不完整")
                    return []
            
            print(f"找到 {len(rows)} 条搜索结果")
            
            for i, row in enumerate(rows, 1):
                try:
                    cells = row.find_elements(By.TAG_NAME, "td")
                    if len(cells) >= 5:
                        # 提取基本信息
                        district = cells[0].text.strip()
                        procurement_method = cells[1].text.strip()
                        procurement_unit = cells[2].text.strip()
                        
                        # 提取公告标题和链接
                        title_cell = cells[3]
                        
                        # 尝试多种方式查找链接
                        title_link = None
                        title = ""
                        detail_url = ""
                        
                        # 方法1: 查找 <a> 标签
                        try:
                            title_link = title_cell.find_element(By.TAG_NAME, "a")
                            title = title_link.text.strip()
                            detail_url = title_link.get_attribute('href')
                            print(f"✅ 第{i}行找到链接: {title[:30]}...")
                        except NoSuchElementException:
                            # 方法2: 查找可点击的元素
                            try:
                                clickable_elements = title_cell.find_elements(By.XPATH, ".//*[@onclick or @href or contains(@class, 'link') or contains(@class, 'clickable')]")
                                if clickable_elements:
                                    element = clickable_elements[0]
                                    title = element.text.strip()
                                    detail_url = element.get_attribute('href') or element.get_attribute('onclick')
                                    print(f"🔗 第{i}行找到可点击元素: {title[:30]}...")
                                else:
                                    # 方法3: 检查单元格是否本身可点击
                                    onclick = title_cell.get_attribute('onclick')
                                    if onclick:
                                        title = title_cell.text.strip()
                                        detail_url = self.extract_url_from_onclick(onclick)
                                        print(f"📱 第{i}行单元格可点击: {title[:30]}...")
                                    else:
                                        # 方法4: 查找所有子元素，看是否有隐藏的链接
                                        all_children = title_cell.find_elements(By.XPATH, ".//*")
                                        cell_text = title_cell.text.strip()
                                        
                                        print(f"🔍 第{i}行详细分析:")
                                        print(f"   - 单元格文本: {cell_text[:50]}...")
                                        print(f"   - 子元素数量: {len(all_children)}")
                                        print(f"   - 单元格HTML: {title_cell.get_attribute('outerHTML')[:200]}...")
                                        
                                        # 检查是否有data属性包含链接信息
                                        for attr in ['data-url', 'data-href', 'data-link', 'data-id']:
                                            attr_value = title_cell.get_attribute(attr)
                                            if attr_value:
                                                print(f"   - 找到属性 {attr}: {attr_value}")
                                                title = cell_text
                                                detail_url = attr_value
                                                break
                                        
                                        # 方法5: 基于JavaScript事件构建链接
                                        if not detail_url and cell_text:
                                            # 尝试从onclick事件中提取参数
                                            onclick_attr = title_cell.get_attribute('onclick')
                                            if onclick_attr and 'articleDetail' in onclick_attr:
                                                detail_url = self.extract_url_from_onclick(onclick_attr)
                                                title = cell_text
                                                print(f"🔧 第{i}行从onclick构建链接: {title[:30]}...")
                                            
                                            # 方法6: 检查是否有data-*属性可以构建链接
                                            if not detail_url:
                                                data_attrs = self.extract_data_attributes(title_cell)
                                                if data_attrs:
                                                    detail_url = self.build_detail_url_from_data_attrs(data_attrs)
                                                    title = cell_text
                                                    print(f"🏗️ 第{i}行从data属性构建链接: {title[:30]}...")
                                        
                                        if not detail_url and cell_text:
                                            print(f"⚠️  第{i}行标题列有内容但无链接: {cell_text[:30]}... 尝试点击打开详情")
                                            try:
                                                # 滚动到该单元格并尝试点击
                                                self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", title_cell)
                                                orig_url = self.driver.current_url
                                                orig_handles = self.driver.window_handles
                                                try:
                                                    title_cell.click()
                                                except Exception:
                                                    ActionChains(self.driver).move_to_element(title_cell).click().perform()
                                                
                                                # 等待新窗口或URL变化
                                                new_handle = None
                                                try:
                                                    WebDriverWait(self.driver, 5).until(lambda d: len(d.window_handles) > len(orig_handles))
                                                    new_handle = [h for h in self.driver.window_handles if h not in orig_handles][0]
                                                    self.driver.switch_to.window(new_handle)
                                                except TimeoutException:
                                                    WebDriverWait(self.driver, 8).until(lambda d: d.current_url != orig_url)
                                                
                                                detail_url = self.driver.current_url
                                                title = cell_text
                                                print(f"🧭 第{i}行点击后进入详情: {detail_url}")
                                                
                                                # 提取详情数据
                                                detail_data = self.extract_detail_page(detail_url)
                                                if detail_data:
                                                    self.detail_data.append(detail_data)
                                                
                                                # 返回列表页
                                                if new_handle:
                                                    self.driver.close()
                                                    self.driver.switch_to.window(orig_handles[0])
                                                else:
                                                    self.driver.back()
                                                    self.wait.until(EC.presence_of_element_located((By.XPATH, "//table//tbody")))
                                                time.sleep(1)
                                                
                                                # 构造结果项并加入列表
                                                publish_time = cells[4].text.strip()
                                                result = {
                                                    'district': district,
                                                    'procurement_method': procurement_method,
                                                    'procurement_unit': procurement_unit,
                                                    'title': title,
                                                    'detail_url': detail_url,
                                                    'publish_time': publish_time,
                                                    'crawl_time': datetime.now().isoformat()
                                                }
                                                results.append(result)
                                                print(f"✅ 通过点击提取第{i}行详情: {title[:50]}...")
                                                
                                            except Exception as click_err:
                                                print(f"❌ 第{i}行点击打开详情失败: {click_err}")
                                                continue
                                        elif not cell_text:
                                            print(f"❌ 第{i}行标题列为空")
                                            continue
                            except Exception as e:
                                cell_text = title_cell.text.strip()
                                if cell_text:
                                    print(f"⚠️  第{i}行标题列有内容但无链接: {cell_text[:30]}...")
                                else:
                                    print(f"❌ 第{i}行标题列为空")
                                continue
                        
                        # 验证提取的数据
                        if not title or not detail_url:
                            print(f"❌ 第{i}行标题或链接为空，跳过")
                            continue
                        
                        publish_time = cells[4].text.strip()
                        
                        result = {
                            'district': district,
                            'procurement_method': procurement_method,
                            'procurement_unit': procurement_unit,
                            'title': title,
                            'detail_url': detail_url,
                            'publish_time': publish_time,
                            'crawl_time': datetime.now().isoformat()
                        }
                        
                        results.append(result)
                        print(f"✅ 成功提取第{i}行: {title[:50]}...")
                        
                    else:
                        print(f"❌ 第{i}行列数不足({len(cells)}列)，跳过")
                        
                except Exception as e:
                    print(f"❌ 处理第{i}行时出错: {e}")
                    continue
            
            if results:
                print(f"✅ 成功提取 {len(results)} 条搜索结果")
            else:
                print("⚠️  未提取到任何有效的搜索结果")
                print("建议检查：")
                print("   1. 验证码是否正确输入")
                print("   2. 搜索条件是否合适")
                print("   3. 网络连接是否正常")
                    
        except Exception as e:
            print(f"❌ 提取搜索结果失败: {e}")
            
        return results
    
    def extract_url_from_onclick(self, onclick_attr):
        """
        从onclick属性中提取URL
        
        Args:
            onclick_attr (str): onclick属性值
            
        Returns:
            str: 构建的详情页URL
        """
        try:
            if 'articleDetail' in onclick_attr:
                # 解析onclick中的参数
                match = re.search(r"articleDetail\('([^']+)','([^']+)','([^']+)','([^']+)','([^']+)'\)", onclick_attr)
                if match:
                    type_param, id_param, plan_id, channel, source = match.groups()
                    return f"{self.detail_url_pattern}?type={type_param}&id={id_param}&planId={plan_id}&channel={channel}&soure={source}"
        except Exception as e:
            print(f"❌ 解析onclick失败: {e}")
        return None
    
    def extract_data_attributes(self, element):
        """
        提取元素的data属性
        
        Args:
            element: WebElement
            
        Returns:
            dict: data属性字典
        """
        data_attrs = {}
        try:
            for attr in ['data-id', 'data-type', 'data-plan-id', 'data-channel']:
                value = element.get_attribute(attr)
                if value:
                    data_attrs[attr.replace('data-', '')] = value
        except Exception as e:
            print(f"❌ 提取data属性失败: {e}")
        return data_attrs
    
    def build_detail_url_from_data_attrs(self, data_attrs):
        """
        从data属性构建详情页URL
        
        Args:
            data_attrs (dict): data属性字典
            
        Returns:
            str: 构建的详情页URL
        """
        try:
            if 'id' in data_attrs and 'type' in data_attrs:
                params = f"type={data_attrs['type']}&id={data_attrs['id']}"
                if 'plan-id' in data_attrs:
                    params += f"&planId={data_attrs['plan-id']}"
                if 'channel' in data_attrs:
                    params += f"&channel={data_attrs['channel']}"
                params += "&soure=ggxx"  # 默认来源
                return f"{self.detail_url_pattern}?{params}"
        except Exception as e:
            print(f"❌ 构建URL失败: {e}")
        return None

    def extract_detail_page(self, detail_url):
        """
        提取详情页面内容
        
        Args:
            detail_url (str): 详情页面URL
            
        Returns:
            dict: 详情页面数据
        """
        try:
            print(f"正在提取详情页: {detail_url}")
            
            # 打开详情页
            self.driver.get(detail_url)
            time.sleep(3)
            
            # 获取页面HTML
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # 提取基本信息
            detail_data = {
                'url': detail_url,
                'title': '',
                'publish_time': '',
                'content': '',
                'contract_info': {},
                'attachments': [],
                'crawl_time': datetime.now().isoformat()
            }
            
            # 提取标题
            title_elements = soup.find_all(['h1', 'h2', 'h3', 'h4'], string=re.compile(r'.*公告.*'))
            if title_elements:
                detail_data['title'] = title_elements[0].get_text().strip()
            
            # 提取发布时间
            time_pattern = r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})'
            time_match = re.search(time_pattern, soup.get_text())
            if time_match:
                detail_data['publish_time'] = time_match.group(1)
            
            # 提取正文内容
            content_div = soup.find('div', class_=re.compile(r'content|article|detail'))
            if content_div:
                detail_data['content'] = content_div.get_text().strip()
            else:
                detail_data['content'] = soup.get_text().strip()
            
            # 提取合同信息（如果是合同公告）
            if '合同' in detail_data.get('title', ''):
                contract_info = self.extract_contract_info(soup)
                detail_data['contract_info'] = contract_info
            
            # 提取附件链接
            attachments = []
            for link in soup.find_all('a', href=True):
                href = link.get('href')
                if href and (href.endswith('.pdf') or href.endswith('.doc') or href.endswith('.docx')):
                    if not href.startswith('http'):
                        href = urljoin(self.base_url, href)
                    attachments.append({
                        'name': link.get_text().strip(),
                        'url': href
                    })
            detail_data['attachments'] = attachments
            
            return detail_data
            
        except Exception as e:
            print(f"提取详情页失败: {e}")
            return None

    def extract_contract_info(self, soup):
        """
        提取合同信息
        
        Args:
            soup: BeautifulSoup对象
            
        Returns:
            dict: 合同信息
        """
        contract_info = {}
        
        try:
            text = soup.get_text()
            
            # 提取合同编号
            contract_no_match = re.search(r'合同编号[：:]\s*([^\n\r]+)', text)
            if contract_no_match:
                contract_info['contract_number'] = contract_no_match.group(1).strip()
            
            # 提取合同名称
            contract_name_match = re.search(r'合同名称[：:]\s*([^\n\r]+)', text)
            if contract_name_match:
                contract_info['contract_name'] = contract_name_match.group(1).strip()
            
            # 提取项目编号
            project_no_match = re.search(r'项目编号[：:]\s*([^\n\r]+)', text)
            if project_no_match:
                contract_info['project_number'] = project_no_match.group(1).strip()
            
            # 提取采购人信息
            buyer_match = re.search(r'采购人\(甲方\)[：:]\s*([^\n\r]+)', text)
            if buyer_match:
                contract_info['buyer'] = buyer_match.group(1).strip()
            
            # 提取供应商信息
            supplier_match = re.search(r'供应商\(乙方\)[：:]\s*([^\n\r]+)', text)
            if supplier_match:
                contract_info['supplier'] = supplier_match.group(1).strip()
            
            # 提取合同金额
            amount_match = re.search(r'合同金额[：:]\s*([^\n\r]+)', text)
            if amount_match:
                contract_info['contract_amount'] = amount_match.group(1).strip()
            
            # 提取履约期限
            period_match = re.search(r'履约期限[：:]\s*([^\n\r]+)', text)
            if period_match:
                contract_info['performance_period'] = period_match.group(1).strip()
            
        except Exception as e:
            print(f"提取合同信息失败: {e}")
            
        return contract_info

    def get_total_pages(self):
        """
        获取总页数
        
        Returns:
            int: 总页数
        """
        try:
            # 查找分页信息
            page_info = self.driver.find_element(By.XPATH, "//span[contains(text(), '页')]")
            page_text = page_info.text
            
            # 提取总页数
            page_match = re.search(r'共\s*(\d+)\s*页', page_text)
            if page_match:
                return int(page_match.group(1))
            
            # 备用方法：查找最后一页的页码
            page_numbers = self.driver.find_elements(By.XPATH, "//ul[@class='el-pager']//li")
            if page_numbers:
                last_page = page_numbers[-1].text
                if last_page.isdigit():
                    return int(last_page)
                    
        except Exception as e:
            print(f"获取总页数失败: {e}")
            
        return 1

    def go_to_next_page(self):
        """
        跳转到下一页
        
        Returns:
            bool: 是否成功跳转
        """
        try:
            # 查找下一页按钮
            next_btn = self.driver.find_element(By.XPATH, "//button[contains(@class, 'btn-next')]")
            
            if 'is-disabled' in next_btn.get_attribute('class'):
                print("已到达最后一页")
                return False
                
            next_btn.click()
            time.sleep(3)
            
            # 等待新页面加载
            self.wait.until(
                EC.presence_of_element_located((By.XPATH, "//table//tbody//tr"))
            )
            
            return True
            
        except Exception as e:
            print(f"跳转下一页失败: {e}")
            return False

    def go_to_page(self, page_num):
        """
        跳转到指定页面
        
        Args:
            page_num (int): 页面号码
            
        Returns:
            bool: 是否跳转成功
        """
        try:
            print(f"跳转到第 {page_num} 页")
            
            # 查找页码输入框
            page_input = self.wait.until(
                EC.presence_of_element_located((By.XPATH, "//input[@placeholder='页码']"))
            )
            page_input.clear()
            page_input.send_keys(str(page_num))
            
            # 点击前往按钮
            go_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), '前往')]")
            go_btn.click()
            
            # 等待页面加载
            time.sleep(3)
            
            # 验证是否跳转成功
            try:
                self.wait.until(
                    EC.presence_of_element_located((By.XPATH, "//table//tbody//tr"))
                )
                print(f"成功跳转到第 {page_num} 页")
                return True
            except TimeoutException:
                print(f"跳转到第 {page_num} 页失败")
                return False
                
        except Exception as e:
            print(f"页面跳转失败: {e}")
            return False

    def save_data(self):
        """
        保存数据到文件
        """
        try:
            # 保存搜索结果为JSON
            results_file = os.path.join(self.output_dir, 'search_results.json')
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, ensure_ascii=False, indent=2)
            
            # 保存搜索结果为CSV
            if self.results:
                csv_file = os.path.join(self.output_dir, 'search_results.csv')
                with open(csv_file, 'w', newline='', encoding='utf-8-sig') as f:
                    writer = csv.DictWriter(f, fieldnames=self.results[0].keys())
                    writer.writeheader()
                    writer.writerows(self.results)
            
            # 保存详情数据为JSON
            if self.detail_data:
                detail_file = os.path.join(self.output_dir, 'detail_data.json')
                with open(detail_file, 'w', encoding='utf-8') as f:
                    json.dump(self.detail_data, f, ensure_ascii=False, indent=2)
            
            print(f"数据已保存到: {self.output_dir}")
            print(f"搜索结果: {len(self.results)} 条")
            print(f"详情数据: {len(self.detail_data)} 条")
            
        except Exception as e:
            print(f"保存数据失败: {e}")

    def run(self, unit_name="医院", extract_details=True):
        """
        运行爬虫
        
        Args:
            unit_name (str): 采购单位名称
            extract_details (bool): 是否提取详情页面
        """
        try:
            print("开始运行福建省政府采购网爬虫...")
            
            # 搜索采购单位
            if not self.search_procurement_unit(unit_name):
                print("搜索失败，程序退出")
                return
            
            # 获取总页数
            total_pages = self.get_total_pages()
            print(f"总页数: {total_pages}")
            
            if self.max_pages:
                total_pages = min(total_pages, self.max_pages)
                print(f"限制爬取页数: {total_pages}")
            
            # 逐页提取数据
            current_page = 1
            
            with tqdm(total=total_pages, desc="爬取进度") as pbar:
                while current_page <= total_pages:
                    print(f"\n正在处理第 {current_page} 页...")
                    
                    # 提取当前页搜索结果
                    page_results = self.extract_search_results()
                    self.results.extend(page_results)
                    
                    print(f"第 {current_page} 页提取到 {len(page_results)} 条记录")
                    
                    # 提取详情页面（可选）
                    if extract_details:
                        for result in page_results:
                            detail_data = self.extract_detail_page(result['detail_url'])
                            if detail_data:
                                self.detail_data.append(detail_data)
                            time.sleep(1)  # 避免请求过快
                    
                    # 跳转到下一页
                    if current_page < total_pages:
                        if not self.go_to_next_page():
                            break
                    
                    current_page += 1
                    pbar.update(1)
                    
                    # 定期保存数据
                    if current_page % 10 == 0:
                        self.save_data()
            
            # 最终保存数据
            self.save_data()
            
            print("\n爬取完成！")
            
        except Exception as e:
            print(f"运行出错: {e}")
        finally:
            self.close()

    def close(self):
        """
        关闭浏览器
        """
        try:
            self.driver.quit()
        except:
            pass


def main():
    """
    主函数
    """
    print("福建省政府采购网爬虫")
    print("=" * 50)
    
    # 配置参数
    unit_name = input("请输入采购单位名称 (默认: 医院): ").strip() or "医院"
    
    max_pages_input = input("请输入最大爬取页数 (默认: 全部): ").strip()
    max_pages = int(max_pages_input) if max_pages_input.isdigit() else None
    
    extract_details = input("是否提取详情页面? (y/n, 默认: y): ").strip().lower() != 'n'
    
    headless = input("是否使用无头模式? (y/n, 默认: n): ").strip().lower() == 'y'
    
    # 创建爬虫实例
    crawler = FujianProcurementCrawler(headless=headless, max_pages=max_pages)
    
    try:
        # 运行爬虫
        crawler.run(unit_name=unit_name, extract_details=extract_details)
    except KeyboardInterrupt:
        print("\n用户中断程序")
    except Exception as e:
        print(f"程序异常: {e}")
    finally:
        crawler.close()


if __name__ == "__main__":
    main()