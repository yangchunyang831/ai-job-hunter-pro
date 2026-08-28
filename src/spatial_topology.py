"""Nationwide spatial topology, metro clusters, and 4-tier spatial auto-derivation engine."""
import math
from typing import Dict, Any, List, Optional, Tuple

# 全国核心城市与经济圈邻近地级市拓扑数据库
METRO_CLUSTER_TOPOLOGY: Dict[str, Dict[str, Any]] = {
    "杭州": {
        "province": "浙江",
        "default_lat": 30.2796,
        "default_lon": 120.0253,
        "default_district": "余杭区",
        "default_address": "未来科技城/阿里西溪园区",
        "adjacent_cities": ["绍兴", "嘉兴", "湖州", "宁波"],
        "province_cities": ["金华", "温州", "台州", "衢州", "丽水", "舟山"]
    },
    "上海": {
        "province": "上海",
        "default_lat": 31.2008,
        "default_lon": 121.5977,
        "default_district": "浦东新区",
        "default_address": "张江高科技园区",
        "adjacent_cities": ["苏州", "昆山", "嘉兴", "太仓", "南通"],
        "province_cities": ["无锡", "常州", "杭州", "宁波"]
    },
    "深圳": {
        "province": "广东",
        "default_lat": 22.5401,
        "default_lon": 113.9534,
        "default_district": "南山区",
        "default_address": "南山科技园/高新园",
        "adjacent_cities": ["东莞", "惠州", "广州", "中山", "珠海"],
        "province_cities": ["佛山", "江门", "汕头", "湛江", "肇庆"]
    },
    "广州": {
        "province": "广东",
        "default_lat": 23.1245,
        "default_lon": 113.3611,
        "default_district": "天河区",
        "default_address": "天河软件园/珠江新城",
        "adjacent_cities": ["佛山", "东莞", "深圳", "中山", "清远"],
        "province_cities": ["惠州", "珠海", "江门", "汕头"]
    },
    "北京": {
        "province": "北京",
        "default_lat": 39.9833,
        "default_lon": 116.3167,
        "default_district": "海淀区",
        "default_address": "中关村软件园/西二旗",
        "adjacent_cities": ["廊坊", "天津", "保定", "唐山"],
        "province_cities": ["石家庄", "张家口", "承德", "沧州"]
    },
    "成都": {
        "province": "四川",
        "default_lat": 30.5728,
        "default_lon": 104.0668,
        "default_district": "武侯区",
        "default_address": "天府软件园/高新南区",
        "adjacent_cities": ["德阳", "眉山", "资阳", "绵阳"],
        "province_cities": ["宜宾", "南充", "泸州", "乐山", "达州"]
    },
    "武汉": {
        "province": "湖北",
        "default_lat": 30.4998,
        "default_lon": 114.4158,
        "default_district": "洪山区",
        "default_address": "光谷软件园/东湖高新区",
        "adjacent_cities": ["鄂州", "黄石", "孝感", "咸宁"],
        "province_cities": ["襄阳", "宜昌", "荆州", "黄冈", "十堰"]
    },
    "南京": {
        "province": "江苏",
        "default_lat": 31.9922,
        "default_lon": 118.7788,
        "default_district": "雨花台区",
        "default_address": "中国(南京)软件谷",
        "adjacent_cities": ["镇江", "扬州", "滁州", "马鞍山", "常州"],
        "province_cities": ["苏州", "无锡", "南通", "徐州", "泰州", "盐城"]
    },
    "苏州": {
        "province": "江苏",
        "default_lat": 31.3195,
        "default_lon": 120.7302,
        "default_district": "吴中区",
        "default_address": "苏州工业园区/生物医药产业园",
        "adjacent_cities": ["无锡", "上海", "常州", "嘉兴", "南通"],
        "province_cities": ["南京", "扬州", "镇江", "泰州", "盐城"]
    },
    "怀化": {
        "province": "湖南",
        "default_lat": 27.5601,
        "default_lon": 109.9985,
        "default_district": "安江镇",
        "default_address": "安江镇裕湘花园",
        "adjacent_cities": ["湘西", "邵阳", "娄底", "铜仁", "吉首"],
        "province_cities": ["长沙", "株洲", "湘潭", "衡阳", "岳阳", "常德", "益阳", "郴州", "永州", "张家界"]
    },
    "长沙": {
        "province": "湖南",
        "default_lat": 28.2282,
        "default_lon": 112.9388,
        "default_district": "岳麓区",
        "default_address": "麓谷高新区/中电软件园",
        "adjacent_cities": ["株洲", "湘潭", "益阳", "岳阳", "娄底"],
        "province_cities": ["衡阳", "常德", "邵阳", "郴州", "怀化", "永州", "张家界", "湘西"]
    },
    "重庆": {
        "province": "重庆",
        "default_lat": 29.5630,
        "default_lon": 106.5516,
        "default_district": "渝北区",
        "default_address": "光电园/照母山",
        "adjacent_cities": ["广安", "达州", "遵义", "泸州"],
        "province_cities": ["成都", "绵阳", "德阳"]
    },
    "贵阳": {
        "province": "贵州",
        "default_lat": 26.5982,
        "default_lon": 106.7072,
        "default_district": "观山湖区",
        "default_address": "金融城/大数据产业园",
        "adjacent_cities": ["遵义", "安顺", "黔南", "铜仁"],
        "province_cities": ["毕节", "六盘水", "黔东南", "怀化"]
    },
    "合肥": {
        "province": "安徽",
        "default_lat": 31.8206,
        "default_lon": 117.2272,
        "default_district": "蜀山区",
        "default_address": "高新区创新产业园",
        "adjacent_cities": ["六安", "淮南", "巢湖", "芜湖", "滁州"],
        "province_cities": ["蚌埠", "马鞍山", "安庆", "阜阳"]
    },
    "郑州": {
        "province": "河南",
        "default_lat": 34.7466,
        "default_lon": 113.6253,
        "default_district": "金水区",
        "default_address": "郑东新区龙子湖",
        "adjacent_cities": ["开封", "新乡", "焦作", "许昌"],
        "province_cities": ["洛阳", "南阳", "平顶山", "商丘"]
    },
    "西安": {
        "province": "陕西",
        "default_lat": 34.2258,
        "default_lon": 108.8877,
        "default_district": "雁塔区",
        "default_address": "高新区软件新城",
        "adjacent_cities": ["咸阳", "渭南", "铜川"],
        "province_cities": ["宝鸡", "汉中", "延安", "榆林"]
    }
}

# 全国一线与新一线重点城市群
NATIONWIDE_HUBS = ["上海", "深圳", "北京", "广州", "杭州", "成都", "武汉", "南京"]


def calculate_haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """计算地球表面两点间的大圆距离 (单位: km)"""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 2)


def derive_spatial_tiers(
    city_name: str,
    district: Optional[str] = None,
    address: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None
) -> Dict[str, Any]:
    """
    用户只需输入居住城市/区域，系统全自动智能推导生成全国 4 层空间地理辐射策略模型
    """
    clean_city = city_name.replace("市", "").strip()
    topo = METRO_CLUSTER_TOPOLOGY.get(clean_city, {})

    province = topo.get("province", "全国")
    lat = latitude or topo.get("default_lat", 30.2796)
    lon = longitude or topo.get("default_lon", 120.0253)
    dist = district or topo.get("default_district", "")
    addr = address or topo.get("default_address", f"{clean_city}{dist}")
    adj_cities = topo.get("adjacent_cities", ["周边城市1", "周边城市2"])

    # 构造全国 4 级智能空间结构
    tiers_config = {
        "user_residence": {
            "city": clean_city,
            "district": dist,
            "address": addr,
            "latitude": lat,
            "longitude": lon,
            "province": province
        },
        "enabled_tiers": [
            "tier1_local",
            "tier2_adjacent",
            "tier4_remote_or_national"
        ],
        "tiers_config": {
            "tier1_local": {
                "name": f"Tier 1: 10km 本地神仙通勤圈 ({clean_city}{dist})",
                "enabled": True,
                "max_distance_km": 10.0,
                "min_score": 75,
                "salary_ratio": 0.90,
                "priority_bonus": 15,
                "greeting_tone": "突出居住在附近、通勤极度稳定、可随时到面/到岗"
            },
            "tier2_adjacent": {
                "name": f"Tier 2: 邻近 1 小时核心地级市圈",
                "enabled": True,
                "adjacent_cities": adj_cities,
                "min_score": 80,
                "salary_ratio": 1.00,
                "priority_bonus": 5,
                "greeting_tone": "确认通勤与班车/高铁交通补贴政策"
            },
            "tier3_province": {
                "name": f"Tier 3: {province}省内其他中心城市",
                "enabled": False,
                "min_score": 85,
                "salary_ratio": 1.15,
                "require_company_scale_min": 100,
                "greeting_tone": "确认异地租房生活成本覆盖与自研平台发展空间"
            },
            "tier4_remote_or_national": {
                "name": "Tier 4: 全国优质机会 & 远程办公 (Remote)",
                "enabled": True,
                "min_score": 88,
                "salary_ratio": 1.30,
                "remote_job_bonus": 20,
                "target_hub_cities": [h for h in NATIONWIDE_HUBS if h != clean_city],
                "greeting_tone": "突出技术硬核与远程自主推进能力，异地求职意向明确"
            }
        }
    }
    return tiers_config
