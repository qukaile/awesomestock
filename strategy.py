# -*- coding: utf-8 -*-
"""
回测
"""
from futu import *
from talib.abstract import *
import numpy as np 
import pandas as pd
import datetime
import time
import os
import json
import copy
import math
import sqlite3
from re import sub
import itertools

class Tools(object):
    def cuo_die_0(self, inputs, item, hands):
        cd_l_3 = (inputs['close'].values[item]-inputs['close'].values[item-1])/(inputs['close'].values[item-1]*hands)
        cd_m_3 = cd_l_3
        cd_n_3 = cd_m_3
        cd_o_3 = (1+cd_n_3)/(1+cd_m_3)-1
        cd_p_3 = 0
        cd_o_max = [] 
        cd_p_max = []
        cd_o_max.append(cd_o_3)
        cd_p_max.append(cd_p_3)
        return cd_l_3, cd_m_3, cd_n_3, cd_o_3, cd_p_3, cd_o_max, cd_p_max
    def cuo_die(self, inputs, item, hands, cd_m_3, cd_n_3, cd_p_3, cd_o_max, cd_p_max):
        cd_l_3 = (inputs['close'].values[item]-inputs['close'].values[item-1])/(inputs['close'].values[item-1]*hands)
        cd_m_3 = (1+cd_m_3)*(1+cd_l_3)-1
        cd_n_3 = max(cd_n_3, cd_m_3)
        cd_o_3 = (1+cd_n_3)/(1+cd_m_3)-1
        if 0==cd_o_3:
            cd_p_3 = 0
        else:
            cd_p_3 += 1
        cd_o_max.append(cd_o_3)
        cd_p_max.append(cd_p_3)
        return cd_l_3, cd_m_3, cd_n_3, cd_o_3, cd_p_3, cd_o_max, cd_p_max
    def yong_jin(self, cost, cost2):
        cost = cost * 0.00171 + 0.05
        cost2 = cost2 * 0.00171 + 0.05
        return max(cost, 0.1007, cost2)
    hs_300 = ['SZ.000596', 'SZ.000625', 'SZ.002736', 'SZ.002739', 'SZ.002773', 'SZ.300433', 'SZ.000002', 'SZ.000001', 'SZ.000538', 
                'SZ.000568', 'SZ.000425', 'SZ.000627', 'SZ.000651', 'SZ.000656', 'SZ.000671', 'SZ.000708', 'SZ.000703', 'SZ.000709', 'SZ.000723', 
                'SZ.000786', 'SZ.000776', 'SZ.000728', 'SZ.000066', 'SZ.000768', 'SZ.000783', 'SZ.000069', 'SZ.000063', 'SZ.000876', 'SZ.000858', 
                'SZ.000860', 'SZ.000895', 'SZ.000938', 'SZ.000961', 'SZ.000977', 'SZ.000157', 'SH.600570', 'SZ.000100', 'SZ.002001', 'SZ.002008', 
                'SZ.002024', 'SZ.002027', 'SZ.002032', 'SZ.002044', 'SZ.002050', 'SZ.000725', 'SZ.002120', 'SZ.002129', 'SZ.000338', 'SZ.002142', 
                'SZ.002146', 'SZ.002153', 'SZ.002157', 'SZ.002179', 'SZ.002230', 'SZ.002236', 'SZ.002241', 'SZ.002252', 'SZ.002271', 'SH.601888', 
                'SZ.002304', 'SZ.002311', 'SZ.002352', 'SZ.002371', 'SZ.002410', 'SZ.002415', 'SZ.002456', 'SZ.002460', 'SZ.002463', 'SZ.002466', 
                'SZ.002468', 'SZ.002475', 'SZ.002202', 'SZ.002493', 'SZ.002508', 'SH.601992', 'SZ.002555', 'SZ.002558', 'SZ.002601', 'SZ.002602', 
                'SZ.002607', 'SZ.002624', 'SH.601231', 'SZ.002673', 'SZ.000333', 'SZ.002714', 'SZ.002594', 'SZ.000166', 'SZ.001979', 'SZ.002841', 'SZ.002916']

m_tools = Tools()
def strategy(inputs, item_x):
    m_stdev = []
    job = ''
    cost, hands = 0, 0
    num = 0
    for item in range(2, len(inputs)-1):
        stdev = (inputs['close'].values[item]-inputs['close'].values[item-1])/(inputs['close'].values[item-1]*hands)
        if (0!=hands) and (0==num):
            cd_l_3, cd_m_3, cd_n_3, cd_o_3, cd_p_3, cd_o_max, cd_p_max = m_tools.cuo_die_0(inputs=inputs, item=item, hands=hands)
            num += 1
        elif 0!=hands:
            cd_l_3, cd_m_3, cd_n_3, cd_o_3, cd_p_3, cd_o_max, cd_p_max = \
                m_tools.cuo_die(inputs=inputs, item=item, hands=hands, cd_m_3=cd_m_3, cd_n_3=cd_n_3, cd_p_3=cd_p_3, cd_o_max=cd_o_max, cd_p_max=cd_p_max)
            # max(cd_o_max)最大搓跌,max(cd_p_max)最长搓跌期
            if (max(cd_o_max) >= item_x[2]) or (max(cd_p_max) >= item_x[0]): 
                m_stdev.append(stdev)
                cost, hands, num = 0, 0, 0
                job = '搓跌超限,卖空!'
                continue
        if (inputs['cci'].values[item-2]<-100) and (inputs['cci'].values[item-1]>-100):
            job = '开始按日收盘价少量买进，直到出现其他信号'
            cost += inputs['close'].values[item]
            if hands!=0:
                m_stdev.append(stdev)
            hands += 1
            continue
        if ('开始按日收盘价少量买进，直到出现其他信号'==job):
            cost2 = hands*inputs['close'].values[item]
            m_yong_jin = m_tools.yong_jin(cost=cost, cost2=cost2)
            if (cost2-cost-m_yong_jin) >= (cost*item_x[1]):
                if hands!=0:
                    m_stdev.append(stdev)
                cost, hands, num = 0, 0, 0
                job = '止盈,卖空!'
                continue
            else:
                cost += inputs['close'].values[item]
                if hands!=0:
                    m_stdev.append(stdev)
                hands += 1
    return m_stdev

# 建立连接
quote_ctx = OpenQuoteContext(host='127.0.0.1', port=11111)
# 获取用于回测的list，即包含在 (沪深300 - 医药股)，且历史K线额度内
m_list = m_tools.hs_300
now = datetime.date.today()
start = str(now - timedelta(days=3650))
end = str(now - timedelta(days=100))
m_list2 = copy.deepcopy(m_list)
final_dict = {}
while m_list:
    each_hz = m_list[0]
    try:
        inputs = []
        ret, data, page_req_key = quote_ctx.request_history_kline(each_hz, start=start, end=end, max_count=1000)
        inputs.append(data)
        while (page_req_key != None):
            ret, data, page_req_key = quote_ctx.request_history_kline(each_hz, start=start, end=end, max_count=1000,page_req_key=page_req_key) 
            inputs.append(data)
        inputs = pd.concat(inputs)
        # real = CCI(high, low, close, timeperiod=14)
        inputs['cci'] = CCI(inputs, timeperiod=14)
        inputs = inputs[14:]
    except Exception as e:
        time.sleep(31)
        continue
    else:
        final_dict[each_hz] = inputs
        m_list.remove(each_hz)
# 结束后记得关闭当条连接，防止连接条数用尽
quote_ctx.close() 
# 元组进行笛卡尔积：
# 搓跌期
item_cd_day = []
# 止盈
item_num = []
# 搓跌率
item_cd_rate = []
# 3个元组的笛卡尔积非常耗时,可以减少
for each in range(1,50):
    item_cd_day.append(each)
for each in range(1,20):
    item_num.append(0+each*0.02)
for each in range(1,20):
    item_cd_rate.append(0+each*0.02)
item_output = itertools.product(item_cd_day,item_num,item_cd_rate)
conn=sqlite3.connect('to_ali.db')
c=conn.cursor()
for item_x in item_output:
    num_0 = 0
    data = {'code': [],
            '最大搓跌期': [],
            '止盈': [],
            '最大搓跌': [],
            '夏普比率': [],}
    for each_hz, value in final_dict.items(): 
        m_stdev = strategy(inputs=value, item_x=item_x)
        m = []
        for each in m_stdev:
            m.append(each-0.04/250)
        xia_pu = math.sqrt(250)*np.average(m)/np.std(m,ddof = 1)
        if xia_pu>=0.78:
            data['code'].append(each_hz)
            data['最大搓跌期'].append(item_x[0])
            data['止盈'].append(item_x[1])
            data['最大搓跌'].append(item_x[2])
            data['夏普比率'].append(xia_pu)
    if data['code']:
        df = pd.DataFrame(data)
        num_0 += 1
    if num_0:
        df.to_sql(name=f'cd{item_x[0]}-{item_x[1]}-{item_x[2]}-xia_pu', con=conn, if_exists="replace")
    print(f'当前时间: {str(datetime.datetime.now())[:19]}, 最大搓跌期 {item_x[0]} 天, 止盈 = {item_x[1]}, 最大搓跌 {item_x[2]} 已存入数据库\n')
#获取表名，保存在tab_name列表
c.execute("select name from sqlite_master where type='table'")
tab_name=c.fetchall()
tab_name=[line[0] for line in tab_name if ('-xia_pu' in line[0])]
print(f'数据表个数: {len(tab_name)}')
m_max = 0
result = []
m_error = []
for each in tab_name:
    #  re.sub 这个方法将需要的SQL内容替换掉
    sql = "select count(*) from 'pid'"
    try:
        m = pd.read_sql(sub("pid", each, sql), conn).values[0][0]
    except Exception as e:
        m_error.append(each)
        continue
    if m > m_max:
        result = [each, ]
        m_max = m
    elif m==m_max:
        result.append(each)
for each in result:
    sql = "select * from 'pid'"
    m = pd.read_sql(sub("pid", each, sql), conn)
    print(m)
    print(f'夏普比率>=0.78的股票有 {len(m)} 支')
print(f'冠军为:\n')
print(result[0])
print('error:\n')
print(m_error)
conn.close()

