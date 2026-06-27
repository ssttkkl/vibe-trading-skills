# IMF PortWatch API 参考

> 用于验证 Strait of Hormuz / Bab el-Mandeb 等规则依赖的通行量数据

## 官网

```
https://portwatch.imf.org/
```

## 已知端点（均限制访问）

PortWatch 基于 ArcGIS Hub，无公开 REST API。页面是 ArcGIS SPA，数据通过 ArcGIS Feature Service 渲染。

## 规则确认

Strait of Hormuz 相关 Polymarket 的规则：

> "Yes if IMF Portwatch publishes a 7-day moving average of transit calls ('Arrivals of Ships') for the Strait of Hormuz equal to or above 60 for any date"

包含的船型：container, dry bulk, roll-on/roll-off, general cargo, tanker

## 无法直接获取数据时的推论

### 跨到期日价格反推（核心技巧）

同一事件，不同到期日，价格差 = 时间价值。

例：Strait of Hormuz 通行恢复正常
- 6/30到期: Yes @ 4.75¢ -> 2.5天内>=60的概率约5%
- 7/31到期: Yes @ 49.5¢ -> 33天内>=60的概率约50%

推理：如果当前7日均线接近60，6/30价格不会只有5%。
当前远低于60，估30-40艘/天，2.5天内翻倍几乎不可能。

适用：任何有多个到期日子市场的事件系列
不适用：不同到期日子市场规则不同的事件

### 与其他相关市场交叉验证

可以结合同一地理区域的多个市场判断局势：

Bab el-Mandeb 海峡有效关闭（<=10艘/天）
- 6/30到期: No @ 99.2¢ -> 几乎不可能
- 这佐证了红海区域局势没有急剧恶化

## Bab el-Mandeb 海峡

类似规则：IMF PortWatch 7日均线 <= 10 -> Yes

月度和季度的到期子市场都有，价格同样反映了当前通行状态。
