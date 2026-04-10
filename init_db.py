#!/usr/bin/env python3
"""
Data processing script: clean, enrich, and import Japanese learning data into SQLite.
"""

import json
import sqlite3
import os
import re

DB_PATH = os.environ.get('HONJP_DB_PATH', os.path.join(os.path.dirname(__file__), 'honjp.db'))
DATA_DIR = os.path.dirname(os.path.abspath(__file__))

# ============================================================
# Enrichment data – curated examples & details for core items
# ============================================================

KANJI_ENRICHMENT = {
    # N5 kanji – radicals, onyomi, kunyomi, example words, meanings
    "日": {"onyomi": "ニチ、ジツ", "kunyomi": "ひ、-び、-か", "strokes": 4, "radical": "日 (nhật)", "meaning_vi": "Ngày, mặt trời", "examples": [
        {"word": "日本", "reading": "にほん", "meaning": "Nhật Bản"},
        {"word": "毎日", "reading": "まいにち", "meaning": "Mỗi ngày"},
        {"word": "日曜日", "reading": "にちようび", "meaning": "Chủ nhật"},
    ]},
    "一": {"onyomi": "イチ、イツ", "kunyomi": "ひと-、ひと.つ", "strokes": 1, "radical": "一 (nhất)", "meaning_vi": "Một, số một", "examples": [
        {"word": "一人", "reading": "ひとり", "meaning": "Một người"},
        {"word": "一つ", "reading": "ひとつ", "meaning": "Một cái"},
        {"word": "一月", "reading": "いちがつ", "meaning": "Tháng 1"},
    ]},
    "国": {"onyomi": "コク", "kunyomi": "くに", "strokes": 8, "radical": "囗 (vi)", "meaning_vi": "Nước, quốc gia", "examples": [
        {"word": "外国", "reading": "がいこく", "meaning": "Nước ngoài"},
        {"word": "中国", "reading": "ちゅうごく", "meaning": "Trung Quốc"},
        {"word": "国語", "reading": "こくご", "meaning": "Quốc ngữ"},
    ]},
    "人": {"onyomi": "ジン、ニン", "kunyomi": "ひと、-り、-と", "strokes": 2, "radical": "人 (nhân)", "meaning_vi": "Người, con người", "examples": [
        {"word": "日本人", "reading": "にほんじん", "meaning": "Người Nhật"},
        {"word": "三人", "reading": "さんにん", "meaning": "Ba người"},
        {"word": "大人", "reading": "おとな", "meaning": "Người lớn"},
    ]},
    "年": {"onyomi": "ネン", "kunyomi": "とし", "strokes": 6, "radical": "干 (can)", "meaning_vi": "Năm", "examples": [
        {"word": "今年", "reading": "ことし", "meaning": "Năm nay"},
        {"word": "去年", "reading": "きょねん", "meaning": "Năm ngoái"},
        {"word": "来年", "reading": "らいねん", "meaning": "Năm sau"},
    ]},
    "大": {"onyomi": "ダイ、タイ", "kunyomi": "おお-、おお.きい、-おお.いに", "strokes": 3, "radical": "大 (đại)", "meaning_vi": "Lớn, to", "examples": [
        {"word": "大学", "reading": "だいがく", "meaning": "Đại học"},
        {"word": "大きい", "reading": "おおきい", "meaning": "To, lớn"},
        {"word": "大切", "reading": "たいせつ", "meaning": "Quan trọng"},
    ]},
    "十": {"onyomi": "ジュウ、ジッ", "kunyomi": "とお、と", "strokes": 2, "radical": "十 (thập)", "meaning_vi": "Mười, số mười", "examples": [
        {"word": "十分", "reading": "じゅうぶん", "meaning": "Đủ, 10 phút"},
        {"word": "十月", "reading": "じゅうがつ", "meaning": "Tháng 10"},
    ]},
    "二": {"onyomi": "ニ、ジ", "kunyomi": "ふた、ふた.つ、ふたた.び", "strokes": 2, "radical": "二 (nhị)", "meaning_vi": "Hai, số hai", "examples": [
        {"word": "二人", "reading": "ふたり", "meaning": "Hai người"},
        {"word": "二つ", "reading": "ふたつ", "meaning": "Hai cái"},
        {"word": "二月", "reading": "にがつ", "meaning": "Tháng 2"},
    ]},
    "本": {"onyomi": "ホン", "kunyomi": "もと", "strokes": 5, "radical": "木 (mộc)", "meaning_vi": "Gốc, sách, bản", "examples": [
        {"word": "日本", "reading": "にほん", "meaning": "Nhật Bản"},
        {"word": "本当", "reading": "ほんとう", "meaning": "Thật sự"},
        {"word": "本屋", "reading": "ほんや", "meaning": "Hiệu sách"},
    ]},
    "中": {"onyomi": "チュウ", "kunyomi": "なか、うち、あた.る", "strokes": 4, "radical": "丨 (cổn)", "meaning_vi": "Trong, giữa, trung", "examples": [
        {"word": "中学校", "reading": "ちゅうがっこう", "meaning": "Trường trung học"},
        {"word": "中国", "reading": "ちゅうごく", "meaning": "Trung Quốc"},
        {"word": "中心", "reading": "ちゅうしん", "meaning": "Trung tâm"},
    ]},
    "長": {"onyomi": "チョウ", "kunyomi": "なが.い、おさ", "strokes": 8, "radical": "長 (trường)", "meaning_vi": "Dài, trưởng", "examples": [
        {"word": "長い", "reading": "ながい", "meaning": "Dài"},
        {"word": "社長", "reading": "しゃちょう", "meaning": "Giám đốc"},
        {"word": "校長", "reading": "こうちょう", "meaning": "Hiệu trưởng"},
    ]},
    "出": {"onyomi": "シュツ、スイ", "kunyomi": "で.る、-で、だ.す、-だ.す", "strokes": 5, "radical": "凵 (khảm)", "meaning_vi": "Ra, xuất", "examples": [
        {"word": "出口", "reading": "でぐち", "meaning": "Lối ra"},
        {"word": "出す", "reading": "だす", "meaning": "Đưa ra"},
        {"word": "出発", "reading": "しゅっぱつ", "meaning": "Xuất phát"},
    ]},
    "三": {"onyomi": "サン", "kunyomi": "み、み.つ、みっ.つ", "strokes": 3, "radical": "一 (nhất)", "meaning_vi": "Ba, số ba", "examples": [
        {"word": "三人", "reading": "さんにん", "meaning": "Ba người"},
        {"word": "三つ", "reading": "みっつ", "meaning": "Ba cái"},
        {"word": "三月", "reading": "さんがつ", "meaning": "Tháng 3"},
    ]},
    "時": {"onyomi": "ジ", "kunyomi": "とき、-どき", "strokes": 10, "radical": "日 (nhật)", "meaning_vi": "Thời gian, giờ", "examples": [
        {"word": "時間", "reading": "じかん", "meaning": "Thời gian"},
        {"word": "時計", "reading": "とけい", "meaning": "Đồng hồ"},
        {"word": "時々", "reading": "ときどき", "meaning": "Thỉnh thoảng"},
    ]},
    "行": {"onyomi": "コウ、ギョウ、アン", "kunyomi": "い.く、ゆ.く、-ゆ.き、おこな.う", "strokes": 6, "radical": "行 (hành)", "meaning_vi": "Đi, hành", "examples": [
        {"word": "行く", "reading": "いく", "meaning": "Đi"},
        {"word": "銀行", "reading": "ぎんこう", "meaning": "Ngân hàng"},
        {"word": "旅行", "reading": "りょこう", "meaning": "Du lịch"},
    ]},
    "見": {"onyomi": "ケン", "kunyomi": "み.る、み.える、み.せる", "strokes": 7, "radical": "見 (kiến)", "meaning_vi": "Nhìn, thấy", "examples": [
        {"word": "見る", "reading": "みる", "meaning": "Nhìn, xem"},
        {"word": "見える", "reading": "みえる", "meaning": "Có thể thấy"},
        {"word": "意見", "reading": "いけん", "meaning": "Ý kiến"},
    ]},
    "月": {"onyomi": "ゲツ、ガツ", "kunyomi": "つき", "strokes": 4, "radical": "月 (nguyệt)", "meaning_vi": "Trăng, tháng", "examples": [
        {"word": "一月", "reading": "いちがつ", "meaning": "Tháng 1"},
        {"word": "月曜日", "reading": "げつようび", "meaning": "Thứ hai"},
        {"word": "今月", "reading": "こんげつ", "meaning": "Tháng này"},
    ]},
    "後": {"onyomi": "ゴ、コウ", "kunyomi": "のち、うし.ろ、あと", "strokes": 9, "radical": "彳 (xích)", "meaning_vi": "Sau, phía sau", "examples": [
        {"word": "午後", "reading": "ごご", "meaning": "Buổi chiều"},
        {"word": "後ろ", "reading": "うしろ", "meaning": "Phía sau"},
        {"word": "最後", "reading": "さいご", "meaning": "Cuối cùng"},
    ]},
    "前": {"onyomi": "ゼン", "kunyomi": "まえ、-まえ", "strokes": 9, "radical": "刀 (đao)", "meaning_vi": "Trước, phía trước", "examples": [
        {"word": "名前", "reading": "なまえ", "meaning": "Tên"},
        {"word": "午前", "reading": "ごぜん", "meaning": "Buổi sáng"},
        {"word": "前", "reading": "まえ", "meaning": "Phía trước"},
    ]},
    "生": {"onyomi": "セイ、ショウ", "kunyomi": "い.きる、う.まれる、なま", "strokes": 5, "radical": "生 (sinh)", "meaning_vi": "Sinh, sống", "examples": [
        {"word": "先生", "reading": "せんせい", "meaning": "Giáo viên"},
        {"word": "学生", "reading": "がくせい", "meaning": "Học sinh"},
        {"word": "生活", "reading": "せいかつ", "meaning": "Cuộc sống"},
    ]},
    "五": {"onyomi": "ゴ", "kunyomi": "いつ、いつ.つ", "strokes": 4, "radical": "二 (nhị)", "meaning_vi": "Năm, số năm", "examples": [
        {"word": "五人", "reading": "ごにん", "meaning": "Năm người"},
        {"word": "五つ", "reading": "いつつ", "meaning": "Năm cái"},
        {"word": "五月", "reading": "ごがつ", "meaning": "Tháng 5"},
    ]},
    "間": {"onyomi": "カン、ケン", "kunyomi": "あいだ、ま、あい", "strokes": 12, "radical": "門 (môn)", "meaning_vi": "Khoảng, giữa", "examples": [
        {"word": "時間", "reading": "じかん", "meaning": "Thời gian"},
        {"word": "間", "reading": "あいだ", "meaning": "Khoảng giữa"},
        {"word": "人間", "reading": "にんげん", "meaning": "Con người"},
    ]},
    "上": {"onyomi": "ジョウ、ショウ", "kunyomi": "うえ、-うえ、うわ-、かみ、あ.げる、のぼ.る", "strokes": 3, "radical": "一 (nhất)", "meaning_vi": "Trên, lên", "examples": [
        {"word": "上", "reading": "うえ", "meaning": "Phía trên"},
        {"word": "上手", "reading": "じょうず", "meaning": "Giỏi, khéo"},
        {"word": "以上", "reading": "いじょう", "meaning": "Trên, hơn"},
    ]},
    "東": {"onyomi": "トウ", "kunyomi": "ひがし", "strokes": 8, "radical": "木 (mộc)", "meaning_vi": "Đông, phía đông", "examples": [
        {"word": "東京", "reading": "とうきょう", "meaning": "Tokyo"},
        {"word": "東", "reading": "ひがし", "meaning": "Phía đông"},
    ]},
    "四": {"onyomi": "シ", "kunyomi": "よ、よ.つ、よっ.つ、よん", "strokes": 5, "radical": "囗 (vi)", "meaning_vi": "Bốn, số bốn", "examples": [
        {"word": "四人", "reading": "よにん", "meaning": "Bốn người"},
        {"word": "四つ", "reading": "よっつ", "meaning": "Bốn cái"},
        {"word": "四月", "reading": "しがつ", "meaning": "Tháng 4"},
    ]},
    "今": {"onyomi": "コン、キン", "kunyomi": "いま", "strokes": 4, "radical": "人 (nhân)", "meaning_vi": "Bây giờ, hiện tại", "examples": [
        {"word": "今日", "reading": "きょう", "meaning": "Hôm nay"},
        {"word": "今", "reading": "いま", "meaning": "Bây giờ"},
        {"word": "今年", "reading": "ことし", "meaning": "Năm nay"},
    ]},
    "金": {"onyomi": "キン、コン、ゴン", "kunyomi": "かね、かな-、-がね", "strokes": 8, "radical": "金 (kim)", "meaning_vi": "Vàng, tiền", "examples": [
        {"word": "お金", "reading": "おかね", "meaning": "Tiền"},
        {"word": "金曜日", "reading": "きんようび", "meaning": "Thứ sáu"},
        {"word": "金", "reading": "きん", "meaning": "Vàng"},
    ]},
    "九": {"onyomi": "キュウ、ク", "kunyomi": "ここの、ここの.つ", "strokes": 2, "radical": "乙 (ất)", "meaning_vi": "Chín, số chín", "examples": [
        {"word": "九つ", "reading": "ここのつ", "meaning": "Chín cái"},
        {"word": "九月", "reading": "くがつ", "meaning": "Tháng 9"},
    ]},
    "入": {"onyomi": "ニュウ、ジュ", "kunyomi": "い.る、-い.る、-い.り、い.れる、はい.る", "strokes": 2, "radical": "入 (nhập)", "meaning_vi": "Vào, nhập", "examples": [
        {"word": "入口", "reading": "いりぐち", "meaning": "Lối vào"},
        {"word": "入る", "reading": "はいる", "meaning": "Vào"},
        {"word": "入れる", "reading": "いれる", "meaning": "Đưa vào"},
    ]},
    "学": {"onyomi": "ガク", "kunyomi": "まな.ぶ", "strokes": 8, "radical": "子 (tử)", "meaning_vi": "Học", "examples": [
        {"word": "学校", "reading": "がっこう", "meaning": "Trường học"},
        {"word": "大学", "reading": "だいがく", "meaning": "Đại học"},
        {"word": "学生", "reading": "がくせい", "meaning": "Học sinh"},
    ]},
    "高": {"onyomi": "コウ", "kunyomi": "たか.い、たか、-だか、たか.まる、たか.める", "strokes": 10, "radical": "高 (cao)", "meaning_vi": "Cao", "examples": [
        {"word": "高い", "reading": "たかい", "meaning": "Cao, đắt"},
        {"word": "高校", "reading": "こうこう", "meaning": "Trường cấp 3"},
        {"word": "最高", "reading": "さいこう", "meaning": "Tốt nhất"},
    ]},
    "円": {"onyomi": "エン、マル", "kunyomi": "まる.い、まる、まど、まど.か、まろ.やか", "strokes": 4, "radical": "冂 (quynh)", "meaning_vi": "Yên (tiền), tròn", "examples": [
        {"word": "百円", "reading": "ひゃくえん", "meaning": "100 yên"},
        {"word": "千円", "reading": "せんえん", "meaning": "1000 yên"},
    ]},
    "子": {"onyomi": "シ、ス、ツ", "kunyomi": "こ、-こ、ね", "strokes": 3, "radical": "子 (tử)", "meaning_vi": "Con, trẻ con", "examples": [
        {"word": "子供", "reading": "こども", "meaning": "Trẻ con"},
        {"word": "女の子", "reading": "おんなのこ", "meaning": "Con gái"},
        {"word": "男の子", "reading": "おとこのこ", "meaning": "Con trai"},
    ]},
    "外": {"onyomi": "ガイ、ゲ", "kunyomi": "そと、ほか、はず.す、はず.れる、と-", "strokes": 5, "radical": "夕 (tịch)", "meaning_vi": "Ngoài, bên ngoài", "examples": [
        {"word": "外国", "reading": "がいこく", "meaning": "Nước ngoài"},
        {"word": "外", "reading": "そと", "meaning": "Bên ngoài"},
        {"word": "外出", "reading": "がいしゅつ", "meaning": "Đi ra ngoài"},
    ]},
    "八": {"onyomi": "ハチ", "kunyomi": "や、や.つ、やっ.つ、よう", "strokes": 2, "radical": "八 (bát)", "meaning_vi": "Tám, số tám", "examples": [
        {"word": "八つ", "reading": "やっつ", "meaning": "Tám cái"},
        {"word": "八月", "reading": "はちがつ", "meaning": "Tháng 8"},
    ]},
    "六": {"onyomi": "ロク、リク", "kunyomi": "む、む.つ、むっ.つ、むい", "strokes": 4, "radical": "八 (bát)", "meaning_vi": "Sáu, số sáu", "examples": [
        {"word": "六つ", "reading": "むっつ", "meaning": "Sáu cái"},
        {"word": "六月", "reading": "ろくがつ", "meaning": "Tháng 6"},
    ]},
    "下": {"onyomi": "カ、ゲ", "kunyomi": "した、しも、もと、さ.げる、くだ.る、お.ろす", "strokes": 3, "radical": "一 (nhất)", "meaning_vi": "Dưới, xuống", "examples": [
        {"word": "下", "reading": "した", "meaning": "Phía dưới"},
        {"word": "下手", "reading": "へた", "meaning": "Dở, kém"},
        {"word": "地下鉄", "reading": "ちかてつ", "meaning": "Tàu điện ngầm"},
    ]},
    "来": {"onyomi": "ライ、タイ", "kunyomi": "く.る、きた.る、きた.す、き.たす、き.たる", "strokes": 7, "radical": "木 (mộc)", "meaning_vi": "Đến, tới", "examples": [
        {"word": "来る", "reading": "くる", "meaning": "Đến"},
        {"word": "来年", "reading": "らいねん", "meaning": "Năm sau"},
        {"word": "来月", "reading": "らいげつ", "meaning": "Tháng sau"},
    ]},
    "気": {"onyomi": "キ、ケ", "kunyomi": "いき", "strokes": 6, "radical": "气 (khí)", "meaning_vi": "Khí, tinh thần", "examples": [
        {"word": "天気", "reading": "てんき", "meaning": "Thời tiết"},
        {"word": "元気", "reading": "げんき", "meaning": "Khỏe mạnh"},
        {"word": "気持ち", "reading": "きもち", "meaning": "Cảm giác"},
    ]},
    "小": {"onyomi": "ショウ", "kunyomi": "ちい.さい、こ-、お-、さ-", "strokes": 3, "radical": "小 (tiểu)", "meaning_vi": "Nhỏ, bé", "examples": [
        {"word": "小さい", "reading": "ちいさい", "meaning": "Nhỏ"},
        {"word": "小学校", "reading": "しょうがっこう", "meaning": "Trường tiểu học"},
    ]},
    "七": {"onyomi": "シチ", "kunyomi": "なな、なな.つ、なの", "strokes": 2, "radical": "一 (nhất)", "meaning_vi": "Bảy, số bảy", "examples": [
        {"word": "七つ", "reading": "ななつ", "meaning": "Bảy cái"},
        {"word": "七月", "reading": "しちがつ", "meaning": "Tháng 7"},
    ]},
    "山": {"onyomi": "サン、セン", "kunyomi": "やま", "strokes": 3, "radical": "山 (sơn)", "meaning_vi": "Núi", "examples": [
        {"word": "山", "reading": "やま", "meaning": "Núi"},
        {"word": "富士山", "reading": "ふじさん", "meaning": "Núi Phú Sĩ"},
    ]},
    "話": {"onyomi": "ワ", "kunyomi": "はな.す、はなし", "strokes": 13, "radical": "言 (ngôn)", "meaning_vi": "Nói, câu chuyện", "examples": [
        {"word": "電話", "reading": "でんわ", "meaning": "Điện thoại"},
        {"word": "話す", "reading": "はなす", "meaning": "Nói"},
        {"word": "会話", "reading": "かいわ", "meaning": "Hội thoại"},
    ]},
    "女": {"onyomi": "ジョ、ニョ、ニョウ", "kunyomi": "おんな、め", "strokes": 3, "radical": "女 (nữ)", "meaning_vi": "Nữ, phụ nữ", "examples": [
        {"word": "女の人", "reading": "おんなのひと", "meaning": "Phụ nữ"},
        {"word": "女の子", "reading": "おんなのこ", "meaning": "Con gái"},
        {"word": "彼女", "reading": "かのじょ", "meaning": "Cô ấy / bạn gái"},
    ]},
    "北": {"onyomi": "ホク", "kunyomi": "きた", "strokes": 5, "radical": "匕 (chủy)", "meaning_vi": "Bắc, phía bắc", "examples": [
        {"word": "北", "reading": "きた", "meaning": "Phía bắc"},
        {"word": "北海道", "reading": "ほっかいどう", "meaning": "Hokkaido"},
    ]},
    "午": {"onyomi": "ゴ", "kunyomi": "うま", "strokes": 4, "radical": "十 (thập)", "meaning_vi": "Trưa, ngọ", "examples": [
        {"word": "午前", "reading": "ごぜん", "meaning": "Buổi sáng"},
        {"word": "午後", "reading": "ごご", "meaning": "Buổi chiều"},
        {"word": "正午", "reading": "しょうご", "meaning": "Giữa trưa"},
    ]},
    "百": {"onyomi": "ヒャク、ビャク", "kunyomi": "もも", "strokes": 6, "radical": "白 (bạch)", "meaning_vi": "Trăm, một trăm", "examples": [
        {"word": "百円", "reading": "ひゃくえん", "meaning": "100 yên"},
        {"word": "三百", "reading": "さんびゃく", "meaning": "300"},
    ]},
    "書": {"onyomi": "ショ", "kunyomi": "か.く、-がき、-がき", "strokes": 10, "radical": "曰 (viết)", "meaning_vi": "Viết, sách", "examples": [
        {"word": "書く", "reading": "かく", "meaning": "Viết"},
        {"word": "図書館", "reading": "としょかん", "meaning": "Thư viện"},
        {"word": "辞書", "reading": "じしょ", "meaning": "Từ điển"},
    ]},
    "先": {"onyomi": "セン", "kunyomi": "さき、ま.ず", "strokes": 6, "radical": "儿 (nhân)", "meaning_vi": "Trước, tiên", "examples": [
        {"word": "先生", "reading": "せんせい", "meaning": "Giáo viên"},
        {"word": "先週", "reading": "せんしゅう", "meaning": "Tuần trước"},
    ]},
    "名": {"onyomi": "メイ、ミョウ", "kunyomi": "な、-な", "strokes": 6, "radical": "口 (khẩu)", "meaning_vi": "Tên, danh", "examples": [
        {"word": "名前", "reading": "なまえ", "meaning": "Tên"},
        {"word": "有名", "reading": "ゆうめい", "meaning": "Nổi tiếng"},
    ]},
    "川": {"onyomi": "セン", "kunyomi": "かわ", "strokes": 3, "radical": "川 (xuyên)", "meaning_vi": "Sông", "examples": [
        {"word": "川", "reading": "かわ", "meaning": "Sông"},
    ]},
    "千": {"onyomi": "セン", "kunyomi": "ち", "strokes": 3, "radical": "十 (thập)", "meaning_vi": "Nghìn", "examples": [
        {"word": "千円", "reading": "せんえん", "meaning": "1000 yên"},
        {"word": "三千", "reading": "さんぜん", "meaning": "3000"},
    ]},
    "水": {"onyomi": "スイ", "kunyomi": "みず、みず-", "strokes": 4, "radical": "水 (thủy)", "meaning_vi": "Nước", "examples": [
        {"word": "水", "reading": "みず", "meaning": "Nước"},
        {"word": "水曜日", "reading": "すいようび", "meaning": "Thứ tư"},
        {"word": "水泳", "reading": "すいえい", "meaning": "Bơi lội"},
    ]},
    "半": {"onyomi": "ハン", "kunyomi": "なか.ば", "strokes": 5, "radical": "十 (thập)", "meaning_vi": "Nửa, phân nửa", "examples": [
        {"word": "半分", "reading": "はんぶん", "meaning": "Một nửa"},
        {"word": "半年", "reading": "はんとし", "meaning": "Nửa năm"},
    ]},
    "男": {"onyomi": "ダン、ナン", "kunyomi": "おとこ、お", "strokes": 7, "radical": "田 (điền)", "meaning_vi": "Nam, đàn ông", "examples": [
        {"word": "男の人", "reading": "おとこのひと", "meaning": "Đàn ông"},
        {"word": "男の子", "reading": "おとこのこ", "meaning": "Con trai"},
        {"word": "長男", "reading": "ちょうなん", "meaning": "Con trai trưởng"},
    ]},
    "西": {"onyomi": "セイ、サイ", "kunyomi": "にし", "strokes": 6, "radical": "西 (tây)", "meaning_vi": "Tây, phía tây", "examples": [
        {"word": "西", "reading": "にし", "meaning": "Phía tây"},
    ]},
    "電": {"onyomi": "デン", "kunyomi": "", "strokes": 13, "radical": "雨 (vũ)", "meaning_vi": "Điện", "examples": [
        {"word": "電話", "reading": "でんわ", "meaning": "Điện thoại"},
        {"word": "電車", "reading": "でんしゃ", "meaning": "Tàu điện"},
        {"word": "電気", "reading": "でんき", "meaning": "Điện"},
    ]},
    "車": {"onyomi": "シャ", "kunyomi": "くるま", "strokes": 7, "radical": "車 (xa)", "meaning_vi": "Xe", "examples": [
        {"word": "電車", "reading": "でんしゃ", "meaning": "Tàu điện"},
        {"word": "自動車", "reading": "じどうしゃ", "meaning": "Ô tô"},
        {"word": "車", "reading": "くるま", "meaning": "Xe"},
    ]},
    "食": {"onyomi": "ショク、ジキ", "kunyomi": "く.う、く.らう、た.べる、は.む", "strokes": 9, "radical": "食 (thực)", "meaning_vi": "Ăn, thực phẩm", "examples": [
        {"word": "食べる", "reading": "たべる", "meaning": "Ăn"},
        {"word": "食事", "reading": "しょくじ", "meaning": "Bữa ăn"},
        {"word": "食堂", "reading": "しょくどう", "meaning": "Nhà ăn"},
    ]},
    "何": {"onyomi": "カ", "kunyomi": "なに、なん", "strokes": 7, "radical": "人 (nhân)", "meaning_vi": "Gì, cái gì", "examples": [
        {"word": "何", "reading": "なに", "meaning": "Cái gì"},
        {"word": "何人", "reading": "なんにん", "meaning": "Mấy người"},
        {"word": "何時", "reading": "なんじ", "meaning": "Mấy giờ"},
    ]},
    "南": {"onyomi": "ナン、ナ", "kunyomi": "みなみ", "strokes": 9, "radical": "十 (thập)", "meaning_vi": "Nam, phía nam", "examples": [
        {"word": "南", "reading": "みなみ", "meaning": "Phía nam"},
    ]},
    "万": {"onyomi": "マン、バン", "kunyomi": "よろず", "strokes": 3, "radical": "一 (nhất)", "meaning_vi": "Vạn, mười nghìn", "examples": [
        {"word": "一万円", "reading": "いちまんえん", "meaning": "10,000 yên"},
    ]},
    "毎": {"onyomi": "マイ", "kunyomi": "ごと、-ごと.に", "strokes": 6, "radical": "母 (mẫu)", "meaning_vi": "Mỗi", "examples": [
        {"word": "毎日", "reading": "まいにち", "meaning": "Mỗi ngày"},
        {"word": "毎週", "reading": "まいしゅう", "meaning": "Mỗi tuần"},
        {"word": "毎年", "reading": "まいとし", "meaning": "Mỗi năm"},
    ]},
    "白": {"onyomi": "ハク、ビャク", "kunyomi": "しろ、しら-、しろ.い", "strokes": 5, "radical": "白 (bạch)", "meaning_vi": "Trắng", "examples": [
        {"word": "白い", "reading": "しろい", "meaning": "Trắng"},
    ]},
    "天": {"onyomi": "テン", "kunyomi": "あまつ、あめ、あま-", "strokes": 4, "radical": "大 (đại)", "meaning_vi": "Trời, thiên", "examples": [
        {"word": "天気", "reading": "てんき", "meaning": "Thời tiết"},
        {"word": "天国", "reading": "てんごく", "meaning": "Thiên đường"},
    ]},
    "母": {"onyomi": "ボ", "kunyomi": "はは、も", "strokes": 5, "radical": "母 (mẫu)", "meaning_vi": "Mẹ", "examples": [
        {"word": "お母さん", "reading": "おかあさん", "meaning": "Mẹ"},
    ]},
    "火": {"onyomi": "カ", "kunyomi": "ひ、-び、ほ-", "strokes": 4, "radical": "火 (hỏa)", "meaning_vi": "Lửa", "examples": [
        {"word": "火曜日", "reading": "かようび", "meaning": "Thứ ba"},
        {"word": "火事", "reading": "かじ", "meaning": "Hỏa hoạn"},
    ]},
    "右": {"onyomi": "ウ、ユウ", "kunyomi": "みぎ", "strokes": 5, "radical": "口 (khẩu)", "meaning_vi": "Phải, bên phải", "examples": [
        {"word": "右", "reading": "みぎ", "meaning": "Bên phải"},
    ]},
    "読": {"onyomi": "ドク、トク、トウ", "kunyomi": "よ.む、-よ.み", "strokes": 14, "radical": "言 (ngôn)", "meaning_vi": "Đọc", "examples": [
        {"word": "読む", "reading": "よむ", "meaning": "Đọc"},
        {"word": "読書", "reading": "どくしょ", "meaning": "Đọc sách"},
    ]},
    "友": {"onyomi": "ユウ", "kunyomi": "とも", "strokes": 4, "radical": "又 (hựu)", "meaning_vi": "Bạn", "examples": [
        {"word": "友達", "reading": "ともだち", "meaning": "Bạn bè"},
        {"word": "親友", "reading": "しんゆう", "meaning": "Bạn thân"},
    ]},
    "左": {"onyomi": "サ", "kunyomi": "ひだり", "strokes": 5, "radical": "工 (công)", "meaning_vi": "Trái, bên trái", "examples": [
        {"word": "左", "reading": "ひだり", "meaning": "Bên trái"},
    ]},
    "休": {"onyomi": "キュウ", "kunyomi": "やす.む、やす.まる、やす.める", "strokes": 6, "radical": "人 (nhân)", "meaning_vi": "Nghỉ ngơi", "examples": [
        {"word": "休む", "reading": "やすむ", "meaning": "Nghỉ"},
        {"word": "休み", "reading": "やすみ", "meaning": "Ngày nghỉ"},
        {"word": "休日", "reading": "きゅうじつ", "meaning": "Ngày lễ"},
    ]},
    "父": {"onyomi": "フ", "kunyomi": "ちち", "strokes": 4, "radical": "父 (phụ)", "meaning_vi": "Cha, bố", "examples": [
        {"word": "お父さん", "reading": "おとうさん", "meaning": "Bố"},
    ]},
    "雨": {"onyomi": "ウ", "kunyomi": "あめ、あま-、-さめ", "strokes": 8, "radical": "雨 (vũ)", "meaning_vi": "Mưa", "examples": [
        {"word": "雨", "reading": "あめ", "meaning": "Mưa"},
        {"word": "大雨", "reading": "おおあめ", "meaning": "Mưa to"},
    ]},
    "土": {"onyomi": "ド、ト", "kunyomi": "つち", "strokes": 3, "radical": "土 (thổ)", "meaning_vi": "Đất", "examples": [
        {"word": "土曜日", "reading": "どようび", "meaning": "Thứ bảy"},
    ]},
    "木": {"onyomi": "ボク、モク", "kunyomi": "き、こ-", "strokes": 4, "radical": "木 (mộc)", "meaning_vi": "Cây, gỗ", "examples": [
        {"word": "木曜日", "reading": "もくようび", "meaning": "Thứ năm"},
        {"word": "木", "reading": "き", "meaning": "Cây"},
    ]},
    "花": {"onyomi": "カ、ケ", "kunyomi": "はな", "strokes": 7, "radical": "艸 (thảo)", "meaning_vi": "Hoa", "examples": [
        {"word": "花", "reading": "はな", "meaning": "Hoa"},
        {"word": "花見", "reading": "はなみ", "meaning": "Ngắm hoa"},
    ]},
    "目": {"onyomi": "モク、ボク", "kunyomi": "め、-め、ま-", "strokes": 5, "radical": "目 (mục)", "meaning_vi": "Mắt", "examples": [
        {"word": "目", "reading": "め", "meaning": "Mắt"},
    ]},
    "耳": {"onyomi": "ジ", "kunyomi": "みみ", "strokes": 6, "radical": "耳 (nhĩ)", "meaning_vi": "Tai", "examples": [
        {"word": "耳", "reading": "みみ", "meaning": "Tai"},
    ]},
    "口": {"onyomi": "コウ、ク", "kunyomi": "くち", "strokes": 3, "radical": "口 (khẩu)", "meaning_vi": "Miệng", "examples": [
        {"word": "口", "reading": "くち", "meaning": "Miệng"},
        {"word": "入口", "reading": "いりぐち", "meaning": "Lối vào"},
        {"word": "出口", "reading": "でぐち", "meaning": "Lối ra"},
    ]},
    "足": {"onyomi": "ソク", "kunyomi": "あし、た.りる、た.る、た.す", "strokes": 7, "radical": "足 (túc)", "meaning_vi": "Chân, đủ", "examples": [
        {"word": "足", "reading": "あし", "meaning": "Chân"},
        {"word": "足りる", "reading": "たりる", "meaning": "Đủ"},
    ]},
    "手": {"onyomi": "シュ、ズ", "kunyomi": "て、て-、-て、た-", "strokes": 4, "radical": "手 (thủ)", "meaning_vi": "Tay", "examples": [
        {"word": "手", "reading": "て", "meaning": "Tay"},
        {"word": "上手", "reading": "じょうず", "meaning": "Giỏi"},
        {"word": "下手", "reading": "へた", "meaning": "Dở"},
    ]},
}

# Vocabulary enrichment – type classification and examples
VOCAB_TYPE_MAP = {
    # Verbs
    "会う": "動詞 (Động từ)", "青い": "形容詞 (Tính từ -i)", "赤い": "形容詞 (Tính từ -i)",
    "明るい": "形容詞 (Tính từ -i)", "開く": "動詞 (Động từ)", "開ける": "動詞 (Động từ)",
    "上げる": "動詞 (Động từ)", "遊ぶ": "動詞 (Động từ)", "洗う": "動詞 (Động từ)",
    "ある": "動詞 (Động từ)", "歩く": "動詞 (Động từ)", "言う": "動詞 (Động từ)",
    "行く": "動詞 (Động từ)", "いる": "動詞 (Động từ)", "入れる": "動詞 (Động từ)",
    "歌う": "動詞 (Động từ)", "生まれる": "動詞 (Động từ)", "売る": "動詞 (Động từ)",
    "起きる": "動詞 (Động từ)", "置く": "動詞 (Động từ)", "送る": "動詞 (Động từ)",
    "押す": "動詞 (Động từ)", "覚える": "動詞 (Động từ)", "泳ぐ": "動詞 (Động từ)",
    "終わる": "動詞 (Động từ)", "買い物": "名詞 (Danh từ)", "返す": "動詞 (Động từ)",
    "帰る": "動詞 (Động từ)", "かかる": "動詞 (Động từ)", "書く": "動詞 (Động từ)",
    "貸す": "動詞 (Động từ)", "借りる": "動詞 (Động từ)", "消える": "動詞 (Động từ)",
    "聞く": "動詞 (Động từ)", "切る": "動詞 (Động từ)", "来る": "動詞 (Động từ)",
    "消す": "動詞 (Động từ)", "答える": "動詞 (Động từ)", "困る": "動詞 (Động từ)",
    "咲く": "動詞 (Động từ)", "知る": "動詞 (Động từ)", "住む": "動詞 (Động từ)",
    "座る": "動詞 (Động từ)", "する": "動詞 (Động từ)", "出す": "動詞 (Động từ)",
    "立つ": "動詞 (Động từ)", "食べる": "動詞 (Động từ)", "違う": "動詞 (Động từ)",
    "使う": "動詞 (Động từ)", "疲れる": "動詞 (Động từ)", "着く": "動詞 (Động từ)",
    "作る": "動詞 (Động từ)", "出かける": "動詞 (Động từ)", "できる": "動詞 (Động từ)",
    "出る": "動詞 (Động từ)", "飛ぶ": "動詞 (Động từ)", "止まる": "動詞 (Động từ)",
    "取る": "動詞 (Động từ)", "撮る": "動詞 (Động từ)", "鳴く": "動詞 (Động từ)",
    "なくす": "動詞 (Động từ)", "並ぶ": "動詞 (Động từ)", "並べる": "動詞 (Động từ)",
    "なる": "動詞 (Động từ)", "脱ぐ": "動詞 (Động từ)", "登る": "動詞 (Động từ)",
    "飲む": "動詞 (Động từ)", "乗る": "動詞 (Động từ)", "入る": "動詞 (Động từ)",
    "始まる": "動詞 (Động từ)", "走る": "動詞 (Động từ)", "働く": "動詞 (Động từ)",
    "話す": "動詞 (Động từ)", "貼る": "動詞 (Động từ)", "引く": "動詞 (Động từ)",
    "弾く": "動詞 (Động từ)", "吹く": "動詞 (Động từ)", "降る": "動詞 (Động từ)",
    "曲がる": "動詞 (Động từ)", "待つ": "動詞 (Động từ)", "磨く": "動詞 (Động từ)",
    "見せる": "動詞 (Động từ)", "見る": "動詞 (Động từ)", "持つ": "動詞 (Động từ)",
    "もらう": "動詞 (Động từ)", "やる": "動詞 (Động từ)", "呼ぶ": "動詞 (Động từ)",
    "読む": "動詞 (Động từ)", "分かる": "動詞 (Động từ)", "忘れる": "動詞 (Động từ)",
    "渡す": "動詞 (Động từ)", "渡る": "動詞 (Động từ)",
    # i-adjectives
    "暑い": "形容詞 (Tính từ -i)", "熱い": "形容詞 (Tính từ -i)", "新しい": "形容詞 (Tính từ -i)",
    "暖かい": "形容詞 (Tính từ -i)", "厚い": "形容詞 (Tính từ -i)", "危ない": "形容詞 (Tính từ -i)",
    "いい": "形容詞 (Tính từ -i)", "忙しい": "形容詞 (Tính từ -i)", "痛い": "形容詞 (Tính từ -i)",
    "薄い": "形容詞 (Tính từ -i)", "美味しい": "形容詞 (Tính từ -i)", "遅い": "形容詞 (Tính từ -i)",
    "大きい": "形容詞 (Tính từ -i)", "重い": "形容詞 (Tính từ -i)", "面白い": "形容詞 (Tính từ -i)",
    "辛い": "形容詞 (Tính từ -i)", "軽い": "形容詞 (Tính từ -i)", "黄色い": "形容詞 (Tính từ -i)",
    "汚い": "形容詞 (Tính từ -i)", "暗い": "形容詞 (Tính từ -i)", "黒い": "形容詞 (Tính từ -i)",
    "寒い": "形容詞 (Tính từ -i)", "白い": "形容詞 (Tính từ -i)", "涼しい": "形容詞 (Tính từ -i)",
    "狭い": "形容詞 (Tính từ -i)", "少ない": "形容詞 (Tính từ -i)", "高い": "形容詞 (Tính từ -i)",
    "楽しい": "形容詞 (Tính từ -i)", "小さい": "形容詞 (Tính từ -i)", "近い": "形容詞 (Tính từ -i)",
    "強い": "形容詞 (Tính từ -i)", "冷たい": "形容詞 (Tính từ -i)", "長い": "形容詞 (Tính từ -i)",
    "早い": "形容詞 (Tính từ -i)", "速い": "形容詞 (Tính từ -i)", "低い": "形容詞 (Tính từ -i)",
    "広い": "形容詞 (Tính từ -i)", "太い": "形容詞 (Tính từ -i)", "古い": "形容詞 (Tính từ -i)",
    "欲しい": "形容詞 (Tính từ -i)", "細い": "形容詞 (Tính từ -i)", "不味い": "形容詞 (Tính từ -i)",
    "丸い": "形容詞 (Tính từ -i)", "短い": "形容詞 (Tính từ -i)", "難しい": "形容詞 (Tính từ -i)",
    "易しい": "形容詞 (Tính từ -i)", "安い": "形容詞 (Tính từ -i)", "優しい": "形容詞 (Tính từ -i)",
    "若い": "形容詞 (Tính từ -i)", "悪い": "形容詞 (Tính từ -i)", "多い": "形容詞 (Tính từ -i)",
    "遠い": "形容詞 (Tính từ -i)", "弱い": "形容詞 (Tính từ -i)", "甘い": "形容詞 (Tính từ -i)",
    # na-adjectives
    "元気": "形容動詞 (Tính từ -na)", "静か": "形容動詞 (Tính từ -na)",
    "好き": "形容動詞 (Tính từ -na)", "嫌い": "形容動詞 (Tính từ -na)",
    "上手": "形容動詞 (Tính từ -na)", "下手": "形容動詞 (Tính từ -na)",
    "有名": "形容動詞 (Tính từ -na)", "大切": "形容動詞 (Tính từ -na)",
    "大丈夫": "形容動詞 (Tính từ -na)", "暇": "形容動詞 (Tính từ -na)",
    "便利": "形容動詞 (Tính từ -na)", "不便": "形容動詞 (Tính từ -na)",
    "きれい": "形容動詞 (Tính từ -na)", "賑やか": "形容動詞 (Tính từ -na)",
}

VOCAB_EXAMPLES = {
    "会う": {"example": "友達に会う。", "example_reading": "ともだちにあう。", "example_meaning": "Gặp bạn bè."},
    "青い": {"example": "空は青い。", "example_reading": "そらはあおい。", "example_meaning": "Bầu trời màu xanh."},
    "赤い": {"example": "赤いりんごが好きです。", "example_reading": "あかいりんごがすきです。", "example_meaning": "Tôi thích táo đỏ."},
    "明るい": {"example": "部屋が明るい。", "example_reading": "へやがあかるい。", "example_meaning": "Phòng sáng."},
    "行く": {"example": "学校に行く。", "example_reading": "がっこうにいく。", "example_meaning": "Đi đến trường."},
    "食べる": {"example": "朝ごはんを食べる。", "example_reading": "あさごはんをたべる。", "example_meaning": "Ăn bữa sáng."},
    "飲む": {"example": "お茶を飲む。", "example_reading": "おちゃをのむ。", "example_meaning": "Uống trà."},
    "見る": {"example": "テレビを見る。", "example_reading": "テレビをみる。", "example_meaning": "Xem tivi."},
    "読む": {"example": "本を読む。", "example_reading": "ほんをよむ。", "example_meaning": "Đọc sách."},
    "書く": {"example": "手紙を書く。", "example_reading": "てがみをかく。", "example_meaning": "Viết thư."},
    "聞く": {"example": "音楽を聞く。", "example_reading": "おんがくをきく。", "example_meaning": "Nghe nhạc."},
    "話す": {"example": "日本語を話す。", "example_reading": "にほんごをはなす。", "example_meaning": "Nói tiếng Nhật."},
    "買う": {"example": "本を買う。", "example_reading": "ほんをかう。", "example_meaning": "Mua sách."},
    "来る": {"example": "友達が来る。", "example_reading": "ともだちがくる。", "example_meaning": "Bạn đến."},
    "帰る": {"example": "家に帰る。", "example_reading": "いえにかえる。", "example_meaning": "Về nhà."},
    "大きい": {"example": "大きい犬がいます。", "example_reading": "おおきいいぬがいます。", "example_meaning": "Có con chó lớn."},
    "小さい": {"example": "小さい猫がいます。", "example_reading": "ちいさいねこがいます。", "example_meaning": "Có con mèo nhỏ."},
    "高い": {"example": "この山は高い。", "example_reading": "このやまはたかい。", "example_meaning": "Ngọn núi này cao."},
    "安い": {"example": "この本は安い。", "example_reading": "このほんはやすい。", "example_meaning": "Quyển sách này rẻ."},
    "新しい": {"example": "新しい車を買った。", "example_reading": "あたらしいくるまをかった。", "example_meaning": "Đã mua xe mới."},
    "古い": {"example": "古い家に住んでいる。", "example_reading": "ふるいいえにすんでいる。", "example_meaning": "Sống trong nhà cũ."},
    "長い": {"example": "髪が長い。", "example_reading": "かみがながい。", "example_meaning": "Tóc dài."},
    "短い": {"example": "短い鉛筆。", "example_reading": "みじかいえんぴつ。", "example_meaning": "Bút chì ngắn."},
    "忙しい": {"example": "今日は忙しい。", "example_reading": "きょうはいそがしい。", "example_meaning": "Hôm nay bận."},
    "難しい": {"example": "日本語は難しい。", "example_reading": "にほんごはむずかしい。", "example_meaning": "Tiếng Nhật khó."},
    "面白い": {"example": "この映画は面白い。", "example_reading": "このえいがはおもしろい。", "example_meaning": "Bộ phim này hay."},
    "元気": {"example": "元気ですか。", "example_reading": "げんきですか。", "example_meaning": "Bạn khỏe không?"},
    "好き": {"example": "猫が好きです。", "example_reading": "ねこがすきです。", "example_meaning": "Tôi thích mèo."},
    "きれい": {"example": "この花はきれいです。", "example_reading": "このはなはきれいです。", "example_meaning": "Bông hoa này đẹp."},
    "する": {"example": "勉強をする。", "example_reading": "べんきょうをする。", "example_meaning": "Học bài."},
    "分かる": {"example": "日本語が分かる。", "example_reading": "にほんごがわかる。", "example_meaning": "Hiểu tiếng Nhật."},
    "働く": {"example": "会社で働く。", "example_reading": "かいしゃではたらく。", "example_meaning": "Làm việc ở công ty."},
    "休む": {"example": "日曜日に休む。", "example_reading": "にちようびにやすむ。", "example_meaning": "Nghỉ vào chủ nhật."},
    "住む": {"example": "東京に住む。", "example_reading": "とうきょうにすむ。", "example_meaning": "Sống ở Tokyo."},
    "待つ": {"example": "バスを待つ。", "example_reading": "バスをまつ。", "example_meaning": "Đợi xe buýt."},
    "持つ": {"example": "かばんを持つ。", "example_reading": "かばんをもつ。", "example_meaning": "Cầm cặp."},
    "乗る": {"example": "電車に乗る。", "example_reading": "でんしゃにのる。", "example_meaning": "Lên tàu điện."},
    "走る": {"example": "公園で走る。", "example_reading": "こうえんではしる。", "example_meaning": "Chạy ở công viên."},
    "泳ぐ": {"example": "プールで泳ぐ。", "example_reading": "プールでおよぐ。", "example_meaning": "Bơi ở hồ bơi."},
    "遊ぶ": {"example": "友達と遊ぶ。", "example_reading": "ともだちとあそぶ。", "example_meaning": "Chơi với bạn."},
    "歩く": {"example": "学校まで歩く。", "example_reading": "がっこうまであるく。", "example_meaning": "Đi bộ đến trường."},
    "飛ぶ": {"example": "鳥が飛ぶ。", "example_reading": "とりがとぶ。", "example_meaning": "Chim bay."},
    "座る": {"example": "椅子に座る。", "example_reading": "いすにすわる。", "example_meaning": "Ngồi trên ghế."},
    "立つ": {"example": "ここに立つ。", "example_reading": "ここにたつ。", "example_meaning": "Đứng ở đây."},
    "寝る": {"example": "早く寝る。", "example_reading": "はやくねる。", "example_meaning": "Ngủ sớm."},
    "起きる": {"example": "朝早く起きる。", "example_reading": "あさはやくおきる。", "example_meaning": "Thức dậy sớm."},
    "作る": {"example": "料理を作る。", "example_reading": "りょうりをつくる。", "example_meaning": "Nấu ăn."},
    "入る": {"example": "部屋に入る。", "example_reading": "へやにはいる。", "example_meaning": "Vào phòng."},
    "出る": {"example": "家を出る。", "example_reading": "いえをでる。", "example_meaning": "Ra khỏi nhà."},
}

# Grammar enrichment – corrected explanations and examples for N5
GRAMMAR_ENRICHMENT = {
    "～から～まで": {
        "meaning": "Từ ~ đến ~",
        "structure": "Danh từ (thời gian/địa điểm) + から + Danh từ (thời gian/địa điểm) + まで",
        "explanation": "Dùng để diễn tả phạm vi từ điểm bắt đầu đến điểm kết thúc, có thể là thời gian hoặc địa điểm.",
        "example": "月曜日から金曜日まで働きます。",
        "example_reading": "げつようびからきんようびまではたらきます。",
        "example_meaning": "Tôi làm việc từ thứ hai đến thứ sáu."
    },
    "～から": {
        "meaning": "Vì ~, bởi vì ~",
        "structure": "Câu thường thể/Câu lịch sự + から",
        "explanation": "Dùng để nêu lý do, nguyên nhân. Đặt phần lý do trước から, kết quả sau.",
        "example": "暑いから、窓を開けてください。",
        "example_reading": "あついから、まどをあけてください。",
        "example_meaning": "Vì nóng nên hãy mở cửa sổ."
    },
    "～と": {
        "meaning": "Với ~, cùng với ~",
        "structure": "Danh từ (người) + と + Động từ",
        "explanation": "Dùng để biểu thị người cùng thực hiện hành động.",
        "example": "友達と映画を見ます。",
        "example_reading": "ともだちとえいがをみます。",
        "example_meaning": "Tôi xem phim với bạn."
    },
    "います": {
        "meaning": "Có ~ (dùng cho sinh vật)",
        "structure": "Nơi chốn + に + Sinh vật + が + います",
        "explanation": "Dùng để diễn tả sự tồn tại của sinh vật (người, động vật) tại một nơi nào đó.",
        "example": "公園に猫がいます。",
        "example_reading": "こうえんにねこがいます。",
        "example_meaning": "Ở công viên có một con mèo."
    },
    "～に～回": {
        "meaning": "~ lần trong ~ (tần suất)",
        "structure": "Thời gian + に + Số lần + 回",
        "explanation": "Dùng để diễn tả tần suất thực hiện hành động trong một khoảng thời gian.",
        "example": "一週間に三回日本語を勉強します。",
        "example_reading": "いっしゅうかんにさんかいにほんごをべんきょうします。",
        "example_meaning": "Tôi học tiếng Nhật 3 lần một tuần."
    },
    "～で": {
        "meaning": "Tại ~, bằng ~",
        "structure": "Danh từ (nơi chốn/phương tiện) + で + Động từ",
        "explanation": "Dùng để chỉ nơi chốn xảy ra hành động, hoặc phương tiện/cách thức thực hiện.",
        "example": "図書館で勉強します。",
        "example_reading": "としょかんでべんきょうします。",
        "example_meaning": "Tôi học tại thư viện."
    },
    "～を": {
        "meaning": "~ (trợ từ tân ngữ)",
        "structure": "Danh từ + を + Động từ",
        "explanation": "Trợ từ đánh dấu tân ngữ trực tiếp (đối tượng chịu tác động của hành động).",
        "example": "本を読みます。",
        "example_reading": "ほんをよみます。",
        "example_meaning": "Tôi đọc sách."
    },
    "～が": {
        "meaning": "~ (trợ từ chủ ngữ)",
        "structure": "Danh từ + が + Tính từ/Động từ",
        "explanation": "Trợ từ đánh dấu chủ ngữ, thường dùng với tính từ thể thích/giỏi, hoặc khi giới thiệu thông tin mới.",
        "example": "猫が好きです。",
        "example_reading": "ねこがすきです。",
        "example_meaning": "Tôi thích mèo."
    },
    "～は": {
        "meaning": "~ (trợ từ chủ đề)",
        "structure": "Danh từ + は + Vị ngữ",
        "explanation": "Trợ từ đánh dấu chủ đề của câu. Dùng khi nói về điều gì đó đã được biết hoặc muốn nhấn mạnh.",
        "example": "私は学生です。",
        "example_reading": "わたしはがくせいです。",
        "example_meaning": "Tôi là học sinh."
    },
    "～に": {
        "meaning": "Đến ~, vào ~ (thời gian), ở ~ (tồn tại)",
        "structure": "Danh từ + に + Động từ",
        "explanation": "Trợ từ đa chức năng: chỉ đích đến, thời điểm, hoặc nơi tồn tại.",
        "example": "七時に起きます。",
        "example_reading": "しちじにおきます。",
        "example_meaning": "Tôi thức dậy lúc 7 giờ."
    },
    "～も": {
        "meaning": "~ cũng",
        "structure": "Danh từ + も + Vị ngữ",
        "explanation": "Trợ từ thể hiện sự tương đồng, nghĩa là 'cũng'. Thay thế は, が, を.",
        "example": "私も学生です。",
        "example_reading": "わたしもがくせいです。",
        "example_meaning": "Tôi cũng là học sinh."
    },
    "～ましょう": {
        "meaning": "Hãy cùng ~",
        "structure": "Động từ thể ます (bỏ ます) + ましょう",
        "explanation": "Dùng để rủ rê, đề nghị cùng làm gì đó.",
        "example": "一緒に食べましょう。",
        "example_reading": "いっしょにたべましょう。",
        "example_meaning": "Hãy cùng ăn nhé."
    },
    "～たい": {
        "meaning": "Muốn ~",
        "structure": "Động từ thể ます (bỏ ます) + たい",
        "explanation": "Dùng để diễn tả mong muốn của người nói. Chỉ dùng cho ngôi thứ 1 (hoặc câu hỏi ngôi thứ 2).",
        "example": "日本に行きたいです。",
        "example_reading": "にほんにいきたいです。",
        "example_meaning": "Tôi muốn đi Nhật Bản."
    },
    "～てください": {
        "meaning": "Xin hãy ~",
        "structure": "Động từ thể て + ください",
        "explanation": "Dùng để yêu cầu hoặc nhờ ai đó làm gì một cách lịch sự.",
        "example": "ここに名前を書いてください。",
        "example_reading": "ここにまなえをかいてください。",
        "example_meaning": "Xin hãy viết tên ở đây."
    },
    "～ている": {
        "meaning": "Đang ~ (trạng thái tiếp diễn)",
        "structure": "Động từ thể て + いる/います",
        "explanation": "Dùng để diễn tả hành động đang xảy ra, hoặc trạng thái kết quả của hành động.",
        "example": "今、本を読んでいます。",
        "example_reading": "いま、ほんをよんでいます。",
        "example_meaning": "Bây giờ tôi đang đọc sách."
    },
    "～ないでください": {
        "meaning": "Xin đừng ~",
        "structure": "Động từ thể ない + でください",
        "explanation": "Dùng để yêu cầu ai đó không làm gì một cách lịch sự.",
        "example": "ここで写真を撮らないでください。",
        "example_reading": "ここでしゃしんをとらないでください。",
        "example_meaning": "Xin đừng chụp ảnh ở đây."
    },
    "～てもいい": {
        "meaning": "Được phép ~",
        "structure": "Động từ thể て + もいい",
        "explanation": "Dùng để xin phép hoặc cho phép làm gì đó.",
        "example": "ここに座ってもいいですか。",
        "example_reading": "ここにすわってもいいですか。",
        "example_meaning": "Tôi có thể ngồi đây không?"
    },
    "～てはいけない": {
        "meaning": "Không được phép ~",
        "structure": "Động từ thể て + はいけない/はいけません",
        "explanation": "Dùng để cấm hoặc từ chối cho phép làm gì đó.",
        "example": "ここでタバコを吸ってはいけません。",
        "example_reading": "ここでタバコをすってはいけません。",
        "example_meaning": "Không được hút thuốc ở đây."
    },
    "～ことがある": {
        "meaning": "Đã từng ~",
        "structure": "Động từ thể た + ことがある/あります",
        "explanation": "Dùng để diễn tả kinh nghiệm – đã từng hoặc chưa từng làm gì đó.",
        "example": "日本に行ったことがあります。",
        "example_reading": "にほんにいったことがあります。",
        "example_meaning": "Tôi đã từng đi Nhật Bản."
    },
    "～と思う": {
        "meaning": "Tôi nghĩ là ~",
        "structure": "Câu thường thể + と思う/と思います",
        "explanation": "Dùng để diễn tả suy nghĩ, ý kiến cá nhân.",
        "example": "明日は雨だと思います。",
        "example_reading": "あしたはあめだとおもいます。",
        "example_meaning": "Tôi nghĩ ngày mai trời mưa."
    },
    "～前に": {
        "meaning": "Trước khi ~",
        "structure": "Động từ thể từ điển + 前に / Danh từ + の前に",
        "explanation": "Dùng để diễn tả hành động xảy ra trước một hành động khác.",
        "example": "寝る前に歯を磨きます。",
        "example_reading": "ねるまえにはをみがきます。",
        "example_meaning": "Trước khi ngủ tôi đánh răng."
    },
    "～後で": {
        "meaning": "Sau khi ~",
        "structure": "Động từ thể た + 後で / Danh từ + の後で",
        "explanation": "Dùng để diễn tả hành động xảy ra sau một hành động khác.",
        "example": "食べた後で散歩します。",
        "example_reading": "たべたあとでさんぽします。",
        "example_meaning": "Sau khi ăn tôi đi dạo."
    },
    "～つもり": {
        "meaning": "Dự định ~",
        "structure": "Động từ thể từ điển + つもり / Động từ thể ない + つもり",
        "explanation": "Dùng để diễn tả dự định, kế hoạch cá nhân.",
        "example": "来年日本に行くつもりです。",
        "example_reading": "らいねんにほんにいくつもりです。",
        "example_meaning": "Tôi dự định đi Nhật năm sau."
    },
    "～なければならない": {
        "meaning": "Phải ~",
        "structure": "Động từ thể ない (bỏ ない) + なければならない",
        "explanation": "Dùng để diễn tả nghĩa vụ, bắt buộc phải làm gì đó.",
        "example": "毎日勉強しなければなりません。",
        "example_reading": "まいにちべんきょうしなければなりません。",
        "example_meaning": "Phải học mỗi ngày."
    },
    "あります": {
        "meaning": "Có ~ (dùng cho vật vô sinh)",
        "structure": "Nơi chốn + に + Danh từ (vật) + が + あります",
        "explanation": "Dùng để diễn tả sự tồn tại của đồ vật, sự việc tại một nơi nào đó.",
        "example": "テーブルの上に本があります。",
        "example_reading": "テーブルのうえにほんがあります。",
        "example_meaning": "Trên bàn có quyển sách."
    },
    "～ました": {
        "meaning": "Đã ~ (quá khứ lịch sự)",
        "structure": "Động từ thể ます (bỏ ます) + ました",
        "explanation": "Thể quá khứ lịch sự của động từ, dùng để nói về hành động đã hoàn thành.",
        "example": "昨日映画を見ました。",
        "example_reading": "きのうえいがをみました。",
        "example_meaning": "Hôm qua tôi đã xem phim."
    },
    "～ません": {
        "meaning": "Không ~ (phủ định lịch sự)",
        "structure": "Động từ thể ます (bỏ ます) + ません",
        "explanation": "Thể phủ định lịch sự của động từ.",
        "example": "お酒を飲みません。",
        "example_reading": "おさけをのみません。",
        "example_meaning": "Tôi không uống rượu."
    },
    "です": {
        "meaning": "Là ~ (khẳng định lịch sự)",
        "structure": "Danh từ/Tính từ -na + です",
        "explanation": "Dùng ở cuối câu để khẳng định một cách lịch sự. Tương đương 'là' trong tiếng Việt.",
        "example": "私は学生です。",
        "example_reading": "わたしはがくせいです。",
        "example_meaning": "Tôi là học sinh."
    },
    "じゃない": {
        "meaning": "Không phải là ~ (phủ định)",
        "structure": "Danh từ/Tính từ -na + じゃない/ではありません",
        "explanation": "Dùng để phủ định danh từ và tính từ -na.",
        "example": "これは本じゃないです。",
        "example_reading": "これはほんじゃないです。",
        "example_meaning": "Đây không phải là sách."
    },
    "～ましょうか": {
        "meaning": "Tôi ~ cho bạn nhé? / Chúng ta ~ nhé?",
        "structure": "Động từ thể ます (bỏ ます) + ましょうか",
        "explanation": "Dùng để đề nghị giúp đỡ hoặc rủ rê.",
        "example": "窓を開けましょうか。",
        "example_reading": "まどをあけましょうか。",
        "example_meaning": "Tôi mở cửa sổ cho bạn nhé?"
    },
    # Additional N5 grammar patterns
    "～ので": {
        "meaning": "Vì ~ nên ~",
        "structure": "Câu thường thể + ので / Tính từ -na + なので / Danh từ + なので",
        "explanation": "Dùng để nêu lý do một cách khách quan, lịch sự hơn から. Thường dùng trong văn viết và giao tiếp trang trọng.",
        "example": "病気なので、学校を休みます。",
        "example_reading": "びょうきなので、がっこうをやすみます。",
        "example_meaning": "Vì bị bệnh nên tôi nghỉ học."
    },
    "て形": {
        "meaning": "Thể て (nối câu, yêu cầu)",
        "structure": "Động từ nhóm 1: thay đuôi → って/んで/いて... | Nhóm 2: bỏ る → て | Nhóm 3: して/きて",
        "explanation": "Thể て là dạng chia quan trọng nhất trong tiếng Nhật. Dùng để nối câu, yêu cầu, diễn tả hành động liên tiếp.",
        "example": "朝起きて、顔を洗って、朝ごはんを食べます。",
        "example_reading": "あさおきて、かおをあらって、あさごはんをたべます。",
        "example_meaning": "Sáng thức dậy, rửa mặt, ăn sáng."
    },
    "て～て": {
        "meaning": "Nối câu (liên tiếp hành động)",
        "structure": "Động từ thể て + Động từ thể て + Động từ (cuối câu)",
        "explanation": "Dùng thể て để nối nhiều hành động liên tiếp theo thứ tự thời gian.",
        "example": "スーパーに行って、野菜を買って、料理を作りました。",
        "example_reading": "スーパーにいって、やさいをかって、りょうりをつくりました。",
        "example_meaning": "Đi siêu thị, mua rau, rồi nấu ăn."
    },
    "否定形": {
        "meaning": "Thể phủ định",
        "structure": "Động từ nhóm 1: thay đuôi う段 → あ段+ない | Nhóm 2: bỏ る → ない | Nhóm 3: しない/こない",
        "explanation": "Thể phủ định (ない形) dùng để phủ định hành động trong câu thường.",
        "example": "明日は学校に行かない。",
        "example_reading": "あしたはがっこうにいかない。",
        "example_meaning": "Ngày mai tôi không đi học."
    },
    "丁寧形": {
        "meaning": "Thể lịch sự (ます形)",
        "structure": "Động từ nhóm 1: thay đuôi う段 → い段+ます | Nhóm 2: bỏ る → ます | Nhóm 3: します/きます",
        "explanation": "Thể lịch sự dùng trong giao tiếp hàng ngày, công sở, với người lớn tuổi hơn.",
        "example": "毎朝コーヒーを飲みます。",
        "example_reading": "まいあさコーヒーをのみます。",
        "example_meaning": "Mỗi sáng tôi uống cà phê."
    },
    "過去形": {
        "meaning": "Thể quá khứ (~た/~ました)",
        "structure": "Động từ thể て → thay て thành た | ます形 → ました",
        "explanation": "Dùng để nói về hành động đã xảy ra trong quá khứ.",
        "example": "昨日友達と映画を見た。",
        "example_reading": "きのうともだちとえいがをみた。",
        "example_meaning": "Hôm qua tôi đã xem phim với bạn."
    },
    "辞書形": {
        "meaning": "Thể từ điển (thể nguyên dạng)",
        "structure": "Dạng gốc của động từ kết thúc bằng âm う段 (う、く、す、つ、ぬ、ぶ、む、る)",
        "explanation": "Dạng cơ bản nhất của động từ, dùng trong văn nói thường, và kết hợp với nhiều mẫu ngữ pháp.",
        "example": "日本語を話すことができる。",
        "example_reading": "にほんごをはなすことができる。",
        "example_meaning": "Tôi có thể nói tiếng Nhật."
    },
    "の中": {
        "meaning": "Trong ~",
        "structure": "Danh từ + の中 + に/で",
        "explanation": "Dùng để chỉ bên trong một nơi chốn hoặc vật thể.",
        "example": "かばんの中に本があります。",
        "example_reading": "かばんのなかにほんがあります。",
        "example_meaning": "Trong cặp có quyển sách."
    },
    "何をしますか": {
        "meaning": "Làm gì? (Hỏi hành động)",
        "structure": "何を + Động từ + ますか",
        "explanation": "Mẫu câu hỏi cơ bản để hỏi ai đó làm gì.",
        "example": "週末は何をしますか。",
        "example_reading": "しゅうまつはなにをしますか。",
        "example_meaning": "Cuối tuần bạn làm gì?"
    },
    "何か": {
        "meaning": "Cái gì đó, điều gì đó",
        "structure": "何か + Động từ",
        "explanation": "Dùng khi không xác định cụ thể đối tượng. 何か = something.",
        "example": "何か飲みたいですか。",
        "example_reading": "なにかのみたいですか。",
        "example_meaning": "Bạn muốn uống gì không?"
    },
    "お国": {
        "meaning": "Nước nào (hỏi quốc tịch lịch sự)",
        "structure": "お国はどちらですか",
        "explanation": "Cách hỏi quốc tịch lịch sự. お là tiền tố kính ngữ thêm vào trước danh từ.",
        "example": "お国はどちらですか。",
        "example_reading": "おくにはどちらですか。",
        "example_meaning": "Bạn đến từ nước nào?"
    },
    "と言う": {
        "meaning": "Nói là ~, gọi là ~",
        "structure": "Câu/Tên + と言う/と言います",
        "explanation": "Dùng để trích dẫn lời nói hoặc giới thiệu tên gọi.",
        "example": "私はホアンと言います。",
        "example_reading": "わたしはホアンといいます。",
        "example_meaning": "Tôi tên là Hoàng."
    },
    "へ ～ に行きます": {
        "meaning": "Đi đâu để làm gì",
        "structure": "Nơi chốn + へ + Danh từ/Động từ thể ます(bỏ ます) + に + 行きます",
        "explanation": "Dùng để diễn tả mục đích đi đến một nơi nào đó.",
        "example": "デパートへ買い物に行きます。",
        "example_reading": "デパートへかいものにいきます。",
        "example_meaning": "Tôi đi trung tâm thương mại để mua sắm."
    },
    "へ ～ に帰ります": {
        "meaning": "Trở về đâu để làm gì",
        "structure": "Nơi chốn + へ + Động từ thể ます(bỏ ます) + に + 帰ります",
        "explanation": "Dùng để diễn tả mục đích trở về một nơi nào đó.",
        "example": "家へ休みに帰ります。",
        "example_reading": "いえへやすみにかえります。",
        "example_meaning": "Tôi về nhà để nghỉ ngơi."
    },
    "～ だけで": {
        "meaning": "Chỉ cần ~ (đã đủ)",
        "structure": "Danh từ/Động từ thể た + だけで",
        "explanation": "Diễn tả rằng chỉ cần một điều kiện đó là đủ.",
        "example": "見ただけで分かります。",
        "example_reading": "みただけでわかります。",
        "example_meaning": "Chỉ cần nhìn là hiểu."
    },
    "～ね": {
        "meaning": "~ nhỉ, ~ nhé (xác nhận, đồng tình)",
        "structure": "Câu + ね",
        "explanation": "Trợ từ cuối câu dùng để xác nhận, tìm kiếm sự đồng tình từ người nghe.",
        "example": "今日はいい天気ですね。",
        "example_reading": "きょうはいいてんきですね。",
        "example_meaning": "Hôm nay thời tiết đẹp nhỉ."
    },
    "～よ": {
        "meaning": "~ đấy, ~ đó (nhấn mạnh thông tin)",
        "structure": "Câu + よ",
        "explanation": "Trợ từ cuối câu dùng để nhấn mạnh thông tin mới mà người nghe chưa biết.",
        "example": "この本は面白いですよ。",
        "example_reading": "このほんはおもしろいですよ。",
        "example_meaning": "Quyển sách này hay đấy."
    },
    "～か": {
        "meaning": "~ không? (câu hỏi)",
        "structure": "Câu + か",
        "explanation": "Trợ từ cuối câu biến câu khẳng định thành câu hỏi.",
        "example": "日本語を勉強していますか。",
        "example_reading": "にほんごをべんきょうしていますか。",
        "example_meaning": "Bạn đang học tiếng Nhật à?"
    },
    "～けど": {
        "meaning": "Nhưng ~, tuy nhiên ~",
        "structure": "Câu 1 + けど/けれども + Câu 2",
        "explanation": "Dùng để nối hai câu có ý nghĩa tương phản. けど là dạng thoải mái, けれども là trang trọng.",
        "example": "高いけど、おいしいです。",
        "example_reading": "たかいけど、おいしいです。",
        "example_meaning": "Đắt nhưng ngon."
    },
    "どう": {
        "meaning": "Như thế nào?",
        "structure": "どう + ですか / でしたか",
        "explanation": "Từ nghi vấn dùng để hỏi ý kiến, cảm nhận hoặc tình trạng.",
        "example": "日本の食べ物はどうですか。",
        "example_reading": "にほんのたべものはどうですか。",
        "example_meaning": "Đồ ăn Nhật Bản thế nào?"
    },
    "～ながら": {
        "meaning": "Vừa ~ vừa ~",
        "structure": "Động từ thể ます(bỏ ます) + ながら + Động từ",
        "explanation": "Diễn tả hai hành động diễn ra đồng thời. Hành động chính ở sau ながら.",
        "example": "音楽を聞きながら、勉強します。",
        "example_reading": "おんがくをききながら、べんきょうします。",
        "example_meaning": "Tôi vừa nghe nhạc vừa học."
    },
    "～たり～たり": {
        "meaning": "Vừa ~ vừa ~ (liệt kê hành động)",
        "structure": "Động từ た形 + り + Động từ た形 + り + します",
        "explanation": "Dùng để liệt kê một số hành động tiêu biểu (không phải tất cả).",
        "example": "休みの日は本を読んだり映画を見たりします。",
        "example_reading": "やすみのひはほんをよんだりえいがをみたりします。",
        "example_meaning": "Ngày nghỉ tôi đọc sách, xem phim..."
    },
    "～方": {
        "meaning": "Cách ~, phương pháp ~",
        "structure": "Động từ thể ます(bỏ ます) + 方(かた)",
        "explanation": "Dùng để hỏi hoặc nói về cách thức thực hiện một hành động.",
        "example": "この漢字の読み方を教えてください。",
        "example_reading": "このかんじのよみかたをおしえてください。",
        "example_meaning": "Hãy dạy tôi cách đọc kanji này."
    },
    "～すぎる": {
        "meaning": "Quá ~",
        "structure": "Động từ thể ます(bỏ ます) + すぎる / Tính từ -i(bỏ い) + すぎる / Tính từ -na + すぎる",
        "explanation": "Diễn tả mức độ vượt quá giới hạn bình thường.",
        "example": "昨日食べすぎました。",
        "example_reading": "きのうたべすぎました。",
        "example_meaning": "Hôm qua tôi ăn quá nhiều."
    },
    "～やすい": {
        "meaning": "Dễ ~",
        "structure": "Động từ thể ます(bỏ ます) + やすい",
        "explanation": "Diễn tả hành động dễ thực hiện.",
        "example": "この本は読みやすいです。",
        "example_reading": "このほんはよみやすいです。",
        "example_meaning": "Quyển sách này dễ đọc."
    },
    "～にくい": {
        "meaning": "Khó ~",
        "structure": "Động từ thể ます(bỏ ます) + にくい",
        "explanation": "Diễn tả hành động khó thực hiện.",
        "example": "この字は読みにくいです。",
        "example_reading": "このじはよみにくいです。",
        "example_meaning": "Chữ này khó đọc."
    },
    "～ことができる": {
        "meaning": "Có thể ~ (khả năng)",
        "structure": "Động từ thể từ điển + ことができる",
        "explanation": "Diễn tả khả năng, năng lực thực hiện một hành động.",
        "example": "日本語を話すことができます。",
        "example_reading": "にほんごをはなすことができます。",
        "example_meaning": "Tôi có thể nói tiếng Nhật."
    },
    "～のが好き": {
        "meaning": "Thích việc ~",
        "structure": "Động từ thể từ điển + のが + 好き/上手/下手",
        "explanation": "Dùng の để biến động từ thành danh từ, kết hợp với tính từ đánh giá.",
        "example": "料理を作るのが好きです。",
        "example_reading": "りょうりをつくるのがすきです。",
        "example_meaning": "Tôi thích nấu ăn."
    },
    "～く/になる": {
        "meaning": "Trở nên ~",
        "structure": "Tính từ -i(bỏ い) + くなる / Tính từ -na + になる / Danh từ + になる",
        "explanation": "Diễn tả sự thay đổi trạng thái tự nhiên.",
        "example": "日本語が上手になりました。",
        "example_reading": "にほんごがじょうずになりました。",
        "example_meaning": "Tiếng Nhật của tôi đã giỏi lên."
    },
    "～く/にする": {
        "meaning": "Làm cho ~",
        "structure": "Tính từ -i(bỏ い) + くする / Tính từ -na + にする / Danh từ + にする",
        "explanation": "Diễn tả hành động chủ động thay đổi trạng thái.",
        "example": "部屋をきれいにしてください。",
        "example_reading": "へやをきれいにしてください。",
        "example_meaning": "Hãy dọn phòng cho sạch."
    },
    "～そうだ(様態)": {
        "meaning": "Trông có vẻ ~ (phỏng đoán từ ngoại hình)",
        "structure": "Tính từ -i(bỏ い) + そうだ / Tính từ -na + そうだ / Động từ ます(bỏ ます) + そうだ",
        "explanation": "Dùng để phỏng đoán dựa trên quan sát bề ngoài.",
        "example": "このケーキはおいしそうですね。",
        "example_reading": "このケーキはおいしそうですね。",
        "example_meaning": "Cái bánh này trông ngon nhỉ."
    },
    "～そうだ(伝聞)": {
        "meaning": "Nghe nói ~ (thông tin gián tiếp)",
        "structure": "Câu thường thể + そうだ/そうです",
        "explanation": "Dùng để truyền đạt thông tin nghe được từ người khác.",
        "example": "明日は雨だそうです。",
        "example_reading": "あしたはあめだそうです。",
        "example_meaning": "Nghe nói ngày mai trời mưa."
    },
    "～ようにする": {
        "meaning": "Cố gắng ~, tập thói quen ~",
        "structure": "Động từ thể từ điển/ない + ようにする",
        "explanation": "Diễn tả nỗ lực duy trì hoặc thay đổi thói quen.",
        "example": "毎日運動するようにしています。",
        "example_reading": "まいにちうんどうするようにしています。",
        "example_meaning": "Tôi cố gắng tập thể dục mỗi ngày."
    },
    "～ようになる": {
        "meaning": "Trở nên có thể ~",
        "structure": "Động từ thể từ điển/ない + ようになる",
        "explanation": "Diễn tả sự thay đổi khả năng hoặc thói quen theo thời gian.",
        "example": "日本語が話せるようになりました。",
        "example_reading": "にほんごがはなせるようになりました。",
        "example_meaning": "Tôi đã có thể nói tiếng Nhật rồi."
    },
    "～てあげる": {
        "meaning": "Làm ~ cho ai (mình làm cho người khác)",
        "structure": "Động từ thể て + あげる",
        "explanation": "Diễn tả hành động làm gì đó giúp người khác. Không dùng với người trên.",
        "example": "友達に日本語を教えてあげました。",
        "example_reading": "ともだちににほんごをおしえてあげました。",
        "example_meaning": "Tôi đã dạy tiếng Nhật cho bạn."
    },
    "～てもらう": {
        "meaning": "Được ai đó làm ~ cho mình",
        "structure": "Người + に + Động từ thể て + もらう",
        "explanation": "Diễn tả việc nhận được sự giúp đỡ, mang ý biết ơn.",
        "example": "友達に日本語を教えてもらいました。",
        "example_reading": "ともだちににほんごをおしえてもらいました。",
        "example_meaning": "Tôi được bạn dạy tiếng Nhật."
    },
    "～てくれる": {
        "meaning": "Ai đó làm ~ cho mình (biết ơn)",
        "structure": "Người + が + Động từ thể て + くれる",
        "explanation": "Diễn tả việc ai đó làm gì đó cho mình, mang ý biết ơn.",
        "example": "母が弁当を作ってくれました。",
        "example_reading": "ははがべんとうをつくってくれました。",
        "example_meaning": "Mẹ đã làm cơm hộp cho tôi."
    },
    "～ば": {
        "meaning": "Nếu ~ thì ~",
        "structure": "Động từ: bỏ う段 + え段+ば | Tính từ -i: bỏ い + ければ | Tính từ -na/Danh từ: + であれば",
        "explanation": "Dạng điều kiện dùng để diễn tả điều kiện giả định. Thường dùng cho điều kiện tổng quát.",
        "example": "安ければ買います。",
        "example_reading": "やすければかいます。",
        "example_meaning": "Nếu rẻ thì tôi mua."
    },
    "～たら": {
        "meaning": "Nếu ~ thì ~, Khi ~ thì ~",
        "structure": "Động từ た形 + ら / Tính từ -i(bỏ い) + かったら / Tính từ -na/Danh từ + だったら",
        "explanation": "Dạng điều kiện linh hoạt nhất, dùng cho cả giả định và thực tế.",
        "example": "雨が降ったら、出かけません。",
        "example_reading": "あめがふったら、でかけません。",
        "example_meaning": "Nếu trời mưa thì tôi không ra ngoài."
    },
    "～と(条件)": {
        "meaning": "Khi ~ thì ~ (tự nhiên, tất yếu)",
        "structure": "Câu thường thể + と + Kết quả",
        "explanation": "Dùng cho điều kiện mang tính tự nhiên, quy luật, tất yếu xảy ra.",
        "example": "春になると、桜が咲きます。",
        "example_reading": "はるになると、さくらがさきます。",
        "example_meaning": "Khi mùa xuân đến, hoa anh đào nở."
    },
    "～なら": {
        "meaning": "Nếu nói về ~ thì ~",
        "structure": "Danh từ/Câu thường thể + なら",
        "explanation": "Dùng để đưa ra lời khuyên hoặc ý kiến dựa trên thông tin từ người khác.",
        "example": "日本に行くなら、京都がいいですよ。",
        "example_reading": "にほんにいくなら、きょうとがいいですよ。",
        "example_meaning": "Nếu đi Nhật thì Kyoto tốt đấy."
    },
    "～し": {
        "meaning": "~ và ~ (liệt kê lý do)",
        "structure": "Câu thường thể + し + Câu thường thể + し",
        "explanation": "Dùng để liệt kê nhiều lý do cùng lúc.",
        "example": "この店は安いし、おいしいし、よく行きます。",
        "example_reading": "このみせはやすいし、おいしいし、よくいきます。",
        "example_meaning": "Quán này vừa rẻ vừa ngon nên tôi hay đến."
    },
    "～のに": {
        "meaning": "Mặc dù ~ nhưng ~ (bất ngờ/bất mãn)",
        "structure": "Câu thường thể + のに",
        "explanation": "Diễn tả sự trái ngược với kỳ vọng, thường mang ý bất mãn, tiếc nuối.",
        "example": "たくさん勉強したのに、テストは難しかった。",
        "example_reading": "たくさんべんきょうしたのに、テストはむずかしかった。",
        "example_meaning": "Mặc dù đã học nhiều nhưng bài thi vẫn khó."
    },
    "～てしまう": {
        "meaning": "Đã ~ mất rồi (hoàn thành/tiếc nuối)",
        "structure": "Động từ thể て + しまう/しまいます",
        "explanation": "Diễn tả hành động hoàn thành hoàn toàn, hoặc kết quả không mong muốn, tiếc nuối.",
        "example": "財布をなくしてしまいました。",
        "example_reading": "さいふをなくしてしまいました。",
        "example_meaning": "Tôi đã làm mất ví rồi."
    },
    "～ておく": {
        "meaning": "Làm ~ sẵn, chuẩn bị ~",
        "structure": "Động từ thể て + おく/おきます",
        "explanation": "Diễn tả hành động làm trước để chuẩn bị cho việc gì đó.",
        "example": "旅行の前にホテルを予約しておきます。",
        "example_reading": "りょこうのまえにホテルをよやくしておきます。",
        "example_meaning": "Trước chuyến đi, tôi đặt khách sạn trước."
    },
    "～てみる": {
        "meaning": "Thử ~ xem",
        "structure": "Động từ thể て + みる/みます",
        "explanation": "Diễn tả việc thử làm gì đó để xem kết quả.",
        "example": "新しいレストランに行ってみましょう。",
        "example_reading": "あたらしいレストランにいってみましょう。",
        "example_meaning": "Hãy thử đi nhà hàng mới xem."
    },
    "～てくる": {
        "meaning": "~ rồi quay lại / bắt đầu ~",
        "structure": "Động từ thể て + くる/きます",
        "explanation": "Diễn tả: 1) Đi làm gì rồi quay lại. 2) Sự thay đổi bắt đầu diễn ra.",
        "example": "コンビニでお弁当を買ってきます。",
        "example_reading": "コンビニでおべんとうをかってきます。",
        "example_meaning": "Tôi đi mua cơm hộp ở cửa hàng tiện lợi rồi về."
    },
    "～ていく": {
        "meaning": "~ rồi đi / tiếp tục ~",
        "structure": "Động từ thể て + いく/いきます",
        "explanation": "Diễn tả: 1) Làm gì trước khi đi. 2) Sự thay đổi tiếp diễn trong tương lai.",
        "example": "これからも日本語を勉強していきます。",
        "example_reading": "これからもにほんごをべんきょうしていきます。",
        "example_meaning": "Từ nay tôi sẽ tiếp tục học tiếng Nhật."
    },
    "受身形": {
        "meaning": "Thể bị động",
        "structure": "Nhóm 1: あ段 + れる | Nhóm 2: bỏ る + られる | する→される / くる→こられる",
        "explanation": "Diễn tả hành động bị tác động. Thường mang ý bị ảnh hưởng tiêu cực (bị ~).",
        "example": "電車の中で足を踏まれました。",
        "example_reading": "でんしゃのなかであしをふまれました。",
        "example_meaning": "Tôi bị giẫm lên chân trên tàu điện."
    },
    "使役形": {
        "meaning": "Thể sai khiến (bắt/cho ~)",
        "structure": "Nhóm 1: あ段 + せる | Nhóm 2: bỏ る + させる | する→させる / くる→こさせる",
        "explanation": "Diễn tả việc bắt hoặc cho phép ai làm gì. Ngữ cảnh quyết định 'bắt' hay 'cho'.",
        "example": "先生は学生にレポートを書かせました。",
        "example_reading": "せんせいはがくせいにレポートをかかせました。",
        "example_meaning": "Giáo viên bắt học sinh viết báo cáo."
    },
    "敬語": {
        "meaning": "Kính ngữ (lịch sự cao)",
        "structure": "お + Động từ ます(bỏ ます) + になる (tôn kính) | お + Động từ ます(bỏ ます) + する (khiêm nhường)",
        "explanation": "Hệ thống ngôn ngữ lịch sự cao gồm: 尊敬語 (tôn kính), 謙譲語 (khiêm nhường), 丁寧語 (lịch sự).",
        "example": "先生はもうお帰りになりました。",
        "example_reading": "せんせいはもうおかえりになりました。",
        "example_meaning": "Thầy đã về rồi ạ."
    },
}


def create_db():
    """Create SQLite database with proper schema."""
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Vocabulary table
    c.execute('''CREATE TABLE vocabulary (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        word TEXT NOT NULL,
        level TEXT NOT NULL,
        reading TEXT DEFAULT '',
        meaning TEXT DEFAULT '',
        type TEXT DEFAULT '',
        kanji_form TEXT DEFAULT '',
        example TEXT DEFAULT '',
        example_reading TEXT DEFAULT '',
        example_meaning TEXT DEFAULT '',
        UNIQUE(word, level)
    )''')
    
    # Kanji table
    c.execute('''CREATE TABLE kanji (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        kanji TEXT NOT NULL,
        level TEXT NOT NULL,
        meaning TEXT DEFAULT '',
        meaning_vi TEXT DEFAULT '',
        onyomi TEXT DEFAULT '',
        kunyomi TEXT DEFAULT '',
        strokes INTEGER DEFAULT 0,
        radical TEXT DEFAULT '',
        UNIQUE(kanji, level)
    )''')
    
    # Kanji examples table
    c.execute('''CREATE TABLE kanji_examples (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        kanji_id INTEGER NOT NULL,
        word TEXT NOT NULL,
        reading TEXT DEFAULT '',
        meaning TEXT DEFAULT '',
        FOREIGN KEY (kanji_id) REFERENCES kanji(id)
    )''')
    
    # Grammar table
    c.execute('''CREATE TABLE grammar (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pattern TEXT NOT NULL,
        level TEXT NOT NULL,
        meaning TEXT DEFAULT '',
        structure TEXT DEFAULT '',
        explanation TEXT DEFAULT '',
        example TEXT DEFAULT '',
        example_reading TEXT DEFAULT '',
        example_meaning TEXT DEFAULT '',
        UNIQUE(pattern, level)
    )''')
    
    # Study progress table
    c.execute('''CREATE TABLE progress (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_type TEXT NOT NULL,
        item_id INTEGER NOT NULL,
        status TEXT DEFAULT 'new',
        correct_count INTEGER DEFAULT 0,
        wrong_count INTEGER DEFAULT 0,
        last_studied TEXT,
        UNIQUE(item_type, item_id)
    )''')
    
    # Bookmarks table for study status tracking
    c.execute('''CREATE TABLE bookmarks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_type TEXT NOT NULL,
        item_id INTEGER NOT NULL,
        status TEXT NOT NULL DEFAULT 'review',
        created_at TEXT DEFAULT (datetime('now')),
        UNIQUE(item_type, item_id)
    )''')
    
    c.execute('CREATE INDEX idx_vocab_level ON vocabulary(level)')
    c.execute('CREATE INDEX idx_kanji_level ON kanji(level)')
    c.execute('CREATE INDEX idx_grammar_level ON grammar(level)')
    c.execute('CREATE INDEX idx_progress_type ON progress(item_type)')
    c.execute('CREATE INDEX idx_bookmarks_type ON bookmarks(item_type, status)')
    
    conn.commit()
    return conn


def is_noise(text):
    """Check if entry is a noise/header entry."""
    noise_patterns = [
        'Bảng chữ cái', 'Hán tự', 'Từ vựng', 'Ngữ pháp', 'Thực hành',
        '語Từ', '文Ngữ', '漢Hán', 'あBảng',
    ]
    for p in noise_patterns:
        if p in text:
            return True
    return False


def has_kanji(text):
    """Check if text contains kanji characters."""
    for ch in text:
        if '\u4e00' <= ch <= '\u9fff':
            return True
    return False


# Curated examples for common N5 words (practical, IT-related where possible)
CURATED_EXAMPLES = {
    # N5 Verbs
    '会う': ('友達とオンラインで会う。', 'ともだちとオンラインであう。', 'Gặp bạn online.'),
    '開ける': ('新しいファイルを開ける。', 'あたらしいファイルをあける。', 'Mở file mới.'),
    '上げる': ('サーバーにデータを上げる。', 'サーバーにデータをあげる。', 'Upload dữ liệu lên server.'),
    '遊ぶ': ('休みの日にゲームで遊ぶ。', 'やすみのひにゲームであそぶ。', 'Ngày nghỉ chơi game.'),
    '浴びる': ('シャワーを浴びてから出勤する。', 'シャワーをあびてからしゅっきんする。', 'Tắm xong rồi đi làm.'),
    '洗う': ('手を洗ってからキーボードを触る。', 'てをあらってからキーボードをさわる。', 'Rửa tay rồi mới chạm bàn phím.'),
    '歩く': ('駅から会社まで歩く。', 'えきからかいしゃまであるく。', 'Đi bộ từ ga đến công ty.'),
    '言う': ('ミーティングで意見を言う。', 'ミーティングでいけんをいう。', 'Nêu ý kiến trong meeting.'),
    '行く': ('毎朝会社に行く。', 'まいあさかいしゃにいく。', 'Mỗi sáng đi công ty.'),
    '要る': ('新しいパソコンが要る。', 'あたらしいパソコンがいる。', 'Cần máy tính mới.'),
    '入れる': ('パスワードを入れてください。', 'パスワードをいれてください。', 'Vui lòng nhập mật khẩu.'),
    '歌う': ('カラオケで日本語の歌を歌う。', 'カラオケでにほんごのうたをうたう。', 'Hát nhạc Nhật ở karaoke.'),
    '生まれる': ('私は1990年に生まれた。', 'わたしは1990ねんにうまれた。', 'Tôi sinh năm 1990.'),
    '売る': ('アプリをストアで売る。', 'アプリをストアでうる。', 'Bán app trên store.'),
    '起きる': ('毎朝7時に起きる。', 'まいあさ7じにおきる。', 'Mỗi sáng thức dậy lúc 7 giờ.'),
    '教える': ('後輩にプログラミングを教える。', 'こうはいにプログラミングをおしえる。', 'Dạy lập trình cho đàn em.'),
    '押す': ('Enterキーを押す。', 'Enterキーをおす。', 'Nhấn phím Enter.'),
    '覚える': ('新しいプログラミング言語を覚える。', 'あたらしいプログラミングげんごをおぼえる。', 'Học ngôn ngữ lập trình mới.'),
    '泳ぐ': ('週末にプールで泳ぐ。', 'しゅうまつにプールでおよぐ。', 'Cuối tuần đi bơi ở hồ.'),
    '終わる': ('会議が5時に終わる。', 'かいぎが5じにおわる。', 'Cuộc họp kết thúc lúc 5 giờ.'),
    '買う': ('新しいモニターを買う。', 'あたらしいモニターをかう。', 'Mua màn hình mới.'),
    '返す': ('図書館に本を返す。', 'としょかんにほんをかえす。', 'Trả sách cho thư viện.'),
    '帰る': ('残業しないで早く帰る。', 'ざんぎょうしないではやくかえる。', 'Không tăng ca, về sớm.'),
    '書く': ('レポートを書く。', 'レポートをかく。', 'Viết báo cáo.'),
    '掛ける': ('眼鏡を掛けてコードを見る。', 'めがねをかけてコードをみる。', 'Đeo kính nhìn code.'),
    '貸す': ('友達にUSBを貸す。', 'ともだちにUSBをかす。', 'Cho bạn mượn USB.'),
    '借りる': ('会社からノートPCを借りる。', 'かいしゃからノートPCをかりる。', 'Mượn laptop từ công ty.'),
    '消す': ('ファイルを消す前にバックアップする。', 'ファイルをけすまえにバックアップする。', 'Backup trước khi xóa file.'),
    '聞く': ('先輩にわからないことを聞く。', 'せんぱいにわからないことをきく。', 'Hỏi tiền bối điều không hiểu.'),
    '切る': ('電源を切ってから帰る。', 'でんげんをきってからかえる。', 'Tắt nguồn rồi về.'),
    '来る': ('明日クライアントが来る。', 'あしたクライアントがくる。', 'Ngày mai khách hàng đến.'),
    '答える': ('面接の質問に答える。', 'めんせつのしつもんにこたえる。', 'Trả lời câu hỏi phỏng vấn.'),
    '困る': ('バグが多くて困る。', 'バグがおおくてこまる。', 'Nhiều bug quá nên phiền.'),
    '知る': ('新しい技術を知る。', 'あたらしいぎじゅつをしる。', 'Biết công nghệ mới.'),
    '吸う': ('タバコは吸わない。', 'タバコはすわない。', 'Tôi không hút thuốc.'),
    '住む': ('東京に住んでいる。', 'とうきょうにすんでいる。', 'Tôi đang sống ở Tokyo.'),
    '座る': ('椅子に座ってコードを書く。', 'いすにすわってコードをかく。', 'Ngồi ghế viết code.'),
    '出す': ('レポートを出す。', 'レポートをだす。', 'Nộp báo cáo.'),
    '立つ': ('スタンディングデスクの前に立つ。', 'スタンディングデスクのまえにたつ。', 'Đứng trước bàn đứng.'),
    '食べる': ('昼休みにラーメンを食べる。', 'ひるやすみにラーメンをたべる。', 'Giờ nghỉ trưa ăn ramen.'),
    '使う': ('毎日パソコンを使う。', 'まいにちパソコンをつかう。', 'Mỗi ngày dùng máy tính.'),
    '着く': ('朝9時に会社に着く。', 'あさ9じにかいしゃにつく。', 'Sáng 9 giờ đến công ty.'),
    '作る': ('新しいウェブサイトを作る。', 'あたらしいウェブサイトをつくる。', 'Làm website mới.'),
    '出かける': ('週末に買い物に出かける。', 'しゅうまつにかいものにでかける。', 'Cuối tuần đi mua sắm.'),
    '出る': ('ミーティングに出る。', 'ミーティングにでる。', 'Tham gia meeting.'),
    '飛ぶ': ('日本へ飛行機で飛ぶ。', 'にほんへひこうきでとぶ。', 'Bay sang Nhật bằng máy bay.'),
    '止まる': ('エレベーターが止まった。', 'エレベーターがとまった。', 'Thang máy đã dừng.'),
    '取る': ('スクリーンショットを取る。', 'スクリーンショットをとる。', 'Chụp screenshot.'),
    '撮る': ('写真を撮る。', 'しゃしんをとる。', 'Chụp ảnh.'),
    '鳴く': ('猫が鳴く。', 'ねこがなく。', 'Con mèo kêu.'),
    '無くす': ('データを無くさないように注意する。', 'データをなくさないようにちゅういする。', 'Cẩn thận để không mất dữ liệu.'),
    '並ぶ': ('ランチの店に並ぶ。', 'ランチのみせにならぶ。', 'Xếp hàng ở quán ăn trưa.'),
    '習う': ('日本語を習っている。', 'にほんごをならっている。', 'Đang học tiếng Nhật.'),
    '脱ぐ': ('靴を脱いで部屋に入る。', 'くつをぬいでへやにはいる。', 'Cởi giày rồi vào phòng.'),
    '寝る': ('夜12時に寝る。', 'よる12じにねる。', 'Đêm 12 giờ đi ngủ.'),
    '登る': ('休日に山に登る。', 'きゅうじつにやまにのぼる。', 'Ngày nghỉ leo núi.'),
    '飲む': ('コーヒーを飲みながら仕事する。', 'コーヒーをのみながらしごとする。', 'Vừa uống cà phê vừa làm việc.'),
    '乗る': ('毎朝電車に乗る。', 'まいあさでんしゃにのる。', 'Mỗi sáng đi tàu điện.'),
    '入る': ('会議室に入る。', 'かいぎしつにはいる。', 'Vào phòng họp.'),
    '履く': ('スーツにズボンを履く。', 'スーツにズボンをはく。', 'Mặc quần với vest.'),
    '始まる': ('会議が9時に始まる。', 'かいぎが9じにはじまる。', 'Cuộc họp bắt đầu lúc 9 giờ.'),
    '走る': ('毎朝公園を走る。', 'まいあさこうえんをはしる。', 'Mỗi sáng chạy ở công viên.'),
    '働く': ('IT会社で働く。', 'ITかいしゃではたらく。', 'Làm việc ở công ty IT.'),
    '話す': ('英語で話す。', 'えいごではなす。', 'Nói bằng tiếng Anh.'),
    '貼る': ('ポストイットを貼る。', 'ポストイットをはる。', 'Dán giấy nhớ.'),
    '引く': ('ドキュメントから引用を引く。', 'ドキュメントからいんようをひく。', 'Trích dẫn từ tài liệu.'),
    '弾く': ('趣味でギターを弾く。', 'しゅみでギターをひく。', 'Sở thích chơi guitar.'),
    '吹く': ('風が吹く。', 'かぜがふく。', 'Gió thổi.'),
    '降る': ('雨が降っているから傘を持つ。', 'あめがふっているからかさをもつ。', 'Trời đang mưa nên mang ô.'),
    '曲がる': ('次の角を右に曲がる。', 'つぎのかどをみぎにまがる。', 'Rẽ phải ở ngã rẽ tiếp theo.'),
    '待つ': ('デプロイの結果を待つ。', 'デプロイのけっかをまつ。', 'Đợi kết quả deploy.'),
    '磨く': ('歯を磨いてから寝る。', 'はをみがいてからねる。', 'Đánh răng rồi đi ngủ.'),
    '見せる': ('画面を見せてください。', 'がめんをみせてください。', 'Cho tôi xem màn hình.'),
    '見る': ('ログを見てバグを探す。', 'ログをみてバグをさがす。', 'Xem log để tìm bug.'),
    '持つ': ('ノートパソコンを持つ。', 'ノートパソコンをもつ。', 'Mang laptop.'),
    '休む': ('疲れたから少し休む。', 'つかれたからすこしやすむ。', 'Mệt nên nghỉ một chút.'),
    '呼ぶ': ('タクシーを呼ぶ。', 'タクシーをよぶ。', 'Gọi taxi.'),
    '読む': ('技術ブログを読む。', 'ぎじゅつブログをよむ。', 'Đọc blog công nghệ.'),
    '分かる': ('コードの意味が分かる。', 'コードのいみがわかる。', 'Hiểu ý nghĩa của code.'),
    '渡す': ('資料を渡す。', 'しりょうをわたす。', 'Đưa tài liệu.'),
    '渡る': ('信号で道を渡る。', 'しんごうでみちをわたる。', 'Qua đường ở đèn giao thông.'),
    # N5 i-adjectives
    '青い': ('空は青い。', 'そらはあおい。', 'Bầu trời màu xanh.'),
    '赤い': ('赤いエラーメッセージが出た。', 'あかいエラーメッセージがでた。', 'Xuất hiện thông báo lỗi màu đỏ.'),
    '明るい': ('この部屋は明るくて仕事しやすい。', 'このへやはあかるくてしごとしやすい。', 'Phòng này sáng nên dễ làm việc.'),
    '暖かい': ('今日は暖かいから散歩する。', 'きょうはあたたかいからさんぽする。', 'Hôm nay ấm nên đi dạo.'),
    '新しい': ('新しいフレームワークを試す。', 'あたらしいフレームワークをためす。', 'Thử framework mới.'),
    '暑い': ('夏のオフィスは暑い。', 'なつのオフィスはあつい。', 'Mùa hè văn phòng nóng.'),
    '危ない': ('パスワードを共有するのは危ない。', 'パスワードをきょうゆうするのはあぶない。', 'Chia sẻ mật khẩu thì nguy hiểm.'),
    '痛い': ('ずっとタイピングして手が痛い。', 'ずっとタイピングしててがいたい。', 'Gõ phím suốt nên đau tay.'),
    '薄い': ('このノートパソコンは薄い。', 'このノートパソコンはうすい。', 'Laptop này mỏng.'),
    '美味しい': ('日本のラーメンは美味しい。', 'にほんのラーメンはおいしい。', 'Ramen Nhật Bản ngon.'),
    '大きい': ('大きいモニターで作業する。', 'おおきいモニターでさぎょうする。', 'Làm việc với màn hình lớn.'),
    '遅い': ('ネットが遅い。', 'ネットがおそい。', 'Mạng chậm.'),
    '面白い': ('この技術記事は面白い。', 'このぎじゅつきじはおもしろい。', 'Bài viết công nghệ này thú vị.'),
    '重い': ('このファイルは重い。', 'このファイルはおもい。', 'File này nặng.'),
    '軽い': ('このアプリは軽くて速い。', 'このアプリはかるくてはやい。', 'App này nhẹ và nhanh.'),
    '辛い': ('残業が続くと辛い。', 'ざんぎょうがつづくとつらい。', 'Tăng ca liên tục thì vất vả.'),
    '黒い': ('黒い画面が好きだ。', 'くろいがめんがすきだ。', 'Tôi thích màn hình tối.'),
    '寒い': ('冬のオフィスは寒い。', 'ふゆのオフィスはさむい。', 'Mùa đông văn phòng lạnh.'),
    '白い': ('白い画面にエラーはない。', 'しろいがめんにエラーはない。', 'Màn hình trắng không có lỗi.'),
    '涼しい': ('エアコンがあるから涼しい。', 'エアコンがあるからすずしい。', 'Có điều hòa nên mát.'),
    '狭い': ('このオフィスは狭い。', 'このオフィスはせまい。', 'Văn phòng này chật.'),
    '高い': ('日本の家賃は高い。', 'にほんのやちんはたかい。', 'Tiền thuê nhà ở Nhật đắt.'),
    '短い': ('締め切りが短い。', 'しめきりがみじかい。', 'Deadline ngắn.'),
    '近い': ('会社は駅に近い。', 'かいしゃはえきにちかい。', 'Công ty gần ga.'),
    '小さい': ('小さい画面でコードは見にくい。', 'ちいさいがめんでコードはみにくい。', 'Màn hình nhỏ thì khó nhìn code.'),
    '強い': ('強いパスワードを使ってください。', 'つよいパスワードをつかってください。', 'Hãy dùng mật khẩu mạnh.'),
    '冷たい': ('冷たいお茶を飲む。', 'つめたいおちゃをのむ。', 'Uống trà lạnh.'),
    '長い': ('このコードは長すぎる。', 'このコードはながすぎる。', 'Code này dài quá.'),
    '速い': ('この新しいPCは速い。', 'このあたらしいPCははやい。', 'PC mới này nhanh.'),
    '早い': ('朝早いミーティングがある。', 'あさはやいミーティングがある。', 'Có meeting sáng sớm.'),
    '広い': ('新しいオフィスは広い。', 'あたらしいオフィスはひろい。', 'Văn phòng mới rộng.'),
    '太い': ('太い線でグラフを描く。', 'ふといせんでグラフをかく。', 'Vẽ biểu đồ bằng nét đậm.'),
    '古い': ('古いブラウザはサポートしない。', 'ふるいブラウザはサポートしない。', 'Không hỗ trợ trình duyệt cũ.'),
    '欲しい': ('新しいキーボードが欲しい。', 'あたらしいキーボードがほしい。', 'Tôi muốn bàn phím mới.'),
    '細い': ('細い字は読みにくい。', 'ほそいじはよみにくい。', 'Chữ nhỏ thì khó đọc.'),
    '丸い': ('丸いアイコンをデザインする。', 'まるいアイコンをデザインする。', 'Thiết kế icon hình tròn.'),
    '短い': ('短いコードの方がいい。', 'みじかいコードのほうがいい。', 'Code ngắn thì tốt hơn.'),
    '難しい': ('このアルゴリズムは難しい。', 'このアルゴリズムはむずかしい。', 'Thuật toán này khó.'),
    '優しい': ('先輩は優しくて教えてくれる。', 'せんぱいはやさしくておしえてくれる。', 'Tiền bối tốt bụng nên dạy cho.'),
    '安い': ('この居酒屋は安い。', 'このいざかやはやすい。', 'Quán nhậu này rẻ.'),
    '悪い': ('エラーハンドリングが悪い。', 'エラーハンドリングがわるい。', 'Xử lý lỗi tệ.'),
    '若い': ('若いエンジニアが多い。', 'わかいエンジニアがおおい。', 'Nhiều kỹ sư trẻ.'),
    # N5 Nouns
    '朝': ('朝コードレビューする。', 'あさコードレビューする。', 'Buổi sáng review code.'),
    '午後': ('午後からミーティングがある。', 'ごごからミーティングがある。', 'Chiều có meeting.'),
    '午前': ('午前中にコーディングする。', 'ごぜんちゅうにコーディングする。', 'Buổi sáng viết code.'),
    '今日': ('今日のタスクを確認する。', 'きょうのタスクをかくにんする。', 'Kiểm tra task hôm nay.'),
    '昨日': ('昨日のバグは直った。', 'きのうのバグはなおった。', 'Bug hôm qua đã sửa xong.'),
    '明日': ('明日リリースする。', 'あしたリリースする。', 'Ngày mai release.'),
    '会社': ('IT会社で働いている。', 'ITかいしゃではたらいている。', 'Đang làm ở công ty IT.'),
    '学校': ('プログラミング学校に通う。', 'プログラミングがっこうにかよう。', 'Đi học trường lập trình.'),
    '先生': ('先生に日本語を教わった。', 'せんせいににほんごをおそわった。', 'Được thầy dạy tiếng Nhật.'),
    '学生': ('大学生の時にプログラミングを始めた。', 'だいがくせいのときにプログラミングをはじめた。', 'Bắt đầu lập trình từ thời sinh viên.'),
    '友達': ('友達と一緒にアプリを作った。', 'ともだちといっしょにアプリをつくった。', 'Cùng bạn làm app.'),
    '電話': ('クライアントに電話する。', 'クライアントにでんわする。', 'Gọi điện cho khách hàng.'),
    '部屋': ('会議室の部屋を予約する。', 'かいぎしつのへやをよやくする。', 'Đặt phòng họp.'),
    '仕事': ('今日は仕事が多い。', 'きょうはしごとがおおい。', 'Hôm nay nhiều việc.'),
    '勉強': ('毎日日本語を勉強する。', 'まいにちにほんごをべんきょうする。', 'Mỗi ngày học tiếng Nhật.'),
    '練習': ('毎日タイピングの練習をする。', 'まいにちタイピングのれんしゅうをする。', 'Mỗi ngày luyện gõ phím.'),
    '時間': ('時間がないからすぐ始める。', 'じかんがないからすぐはじめる。', 'Không có thời gian nên bắt đầu ngay.'),
    '天気': ('天気がいいから外で仕事する。', 'てんきがいいからそとでしごとする。', 'Thời tiết tốt nên ra ngoài làm việc.'),
    '映画': ('日本語の映画を見て勉強する。', 'にほんごのえいがをみてべんきょうする。', 'Xem phim Nhật để học.'),
    '音楽': ('音楽を聞きながらコーディングする。', 'おんがくをききながらコーディングする。', 'Vừa nghe nhạc vừa code.'),
    '写真': ('製品の写真を撮る。', 'せいひんのしゃしんをとる。', 'Chụp ảnh sản phẩm.'),
    '問題': ('この問題を解決する方法を考える。', 'このもんだいをかいけつするほうほうをかんがえる。', 'Nghĩ cách giải quyết vấn đề này.'),
    '質問': ('質問があればSlackで聞いてください。', 'しつもんがあればSlackできいてください。', 'Nếu có câu hỏi hãy hỏi trên Slack.'),
    '意味': ('このエラーメッセージの意味が分からない。', 'このエラーメッセージのいみがわからない。', 'Không hiểu nghĩa thông báo lỗi này.'),
    '食べ物': ('コンビニで食べ物を買う。', 'コンビニでたべものをかう。', 'Mua đồ ăn ở cửa hàng tiện lợi.'),
    '飲み物': ('自販機で飲み物を買う。', 'じはんきでのみものをかう。', 'Mua đồ uống ở máy bán tự động.'),
    '料理': ('週末に日本料理を作る。', 'しゅうまつににほんりょうりをつくる。', 'Cuối tuần nấu món Nhật.'),
    '病気': ('病気の時は休んでください。', 'びょうきのときはやすんでください。', 'Khi bệnh hãy nghỉ ngơi.'),
    '旅行': ('日本に旅行に行きたい。', 'にほんにりょこうにいきたい。', 'Muốn đi du lịch Nhật Bản.'),
    '散歩': ('昼休みに散歩する。', 'ひるやすみにさんぽする。', 'Giờ nghỉ trưa đi dạo.'),
    '名前': ('変数の名前は分かりやすくする。', 'へんすうのなまえはわかりやすくする。', 'Đặt tên biến dễ hiểu.'),
    '空': ('今日の空はきれいだ。', 'きょうのそらはきれいだ。', 'Bầu trời hôm nay đẹp.'),
    '海': ('夏に海に行きたい。', 'なつにうみにいきたい。', 'Mùa hè muốn đi biển.'),
    '色': ('UIの色を変更する。', 'UIのいろをへんこうする。', 'Thay đổi màu UI.'),
}


def auto_generate_example(word, reading, meaning, word_type):
    """Auto-generate a practical example sentence based on word type."""
    # Check curated examples first
    if word in CURATED_EXAMPLES:
        return CURATED_EXAMPLES[word]
    
    first_meaning = meaning.split(",")[0].split("(")[0].split("/")[0].strip()
    
    # Verb patterns
    if word_type and ('動詞' in word_type or 'Động từ' in word_type):
        if word.endswith('る'):
            return (
                f'仕事で{word}ことがある。',
                f'しごとで{reading or word}ことがある。',
                f'Có lúc {first_meaning.lower()} trong công việc.'
            )
        elif word.endswith(('す', 'く', 'ぐ', 'む', 'ぶ', 'つ', 'う', 'ぬ')):
            return (
                f'毎日{word}ようにしている。',
                f'まいにち{reading or word}ようにしている。',
                f'Tôi cố gắng {first_meaning.lower()} mỗi ngày.'
            )
    
    # i-adjective patterns
    if word_type and ('形容詞' in word_type or 'Tính từ' in word_type):
        if word.endswith('い'):
            return (
                f'このプロジェクトはなかなか{word}。',
                f'このプロジェクトはなかなか{reading or word}。',
                f'Dự án này khá là {first_meaning.lower()}.'
            )
    
    # Na-adjective patterns
    if word_type and ('形容動詞' in word_type or '-na' in word_type):
        return (
            f'日本の生活はとても{word}だと思う。',
            f'にほんのせいかつはとても{reading or word}だとおもう。',
            f'Tôi nghĩ cuộc sống Nhật rất {first_meaning.lower()}.'
        )
    
    # Noun patterns with varied contexts
    if has_kanji(word) or (not word_type):
        return (
            f'{word}について調べる。',
            f'{reading or word}についてしらべる。',
            f'Tìm hiểu về {first_meaning.lower()}.'
        )
    
    return None


# Mapping of common hiragana-only words to their kanji forms
HIRAGANA_TO_KANJI = {
    'あう': '会う', 'あおい': '青い', 'あかい': '赤い', 'あかるい': '明るい',
    'あき': '秋', 'あげる': '上げる', 'あさ': '朝', 'あさごはん': '朝ご飯',
    'あし': '足', 'あした': '明日', 'あそぶ': '遊ぶ', 'あたま': '頭',
    'あたらしい': '新しい', 'あつい': '暑い', 'あと': '後', 'あなた': '貴方',
    'あに': '兄', 'あね': '姉', 'あびる': '浴びる', 'あまい': '甘い',
    'あめ': '雨', 'あるく': '歩く', 'いう': '言う', 'いえ': '家',
    'いす': '椅子', 'いそがしい': '忙しい', 'いたい': '痛い',
    'いちばん': '一番', 'いつ': '何時', 'いつも': '何時も',
    'いぬ': '犬', 'いもうと': '妹', 'いる': '居る', 'いれる': '入れる',
    'うえ': '上', 'うしろ': '後ろ', 'うすい': '薄い', 'うた': '歌',
    'うたう': '歌う', 'うまれる': '生まれる', 'うみ': '海',
    'うる': '売る', 'うるさい': '煩い', 'えいが': '映画',
    'えいご': '英語', 'えき': '駅', 'おおきい': '大きい', 'おおい': '多い',
    'おかし': 'お菓子', 'おかね': 'お金', 'おきる': '起きる',
    'おく': '置く', 'おくる': '送る', 'おしえる': '教える',
    'おす': '押す', 'おそい': '遅い', 'おちゃ': 'お茶',
    'おとうさん': 'お父さん', 'おとうと': '弟', 'おとこ': '男',
    'おとな': '大人', 'おなじ': '同じ', 'おにいさん': 'お兄さん',
    'おねえさん': 'お姉さん', 'おぼえる': '覚える', 'おもい': '重い',
    'おもう': '思う', 'おもしろい': '面白い', 'おわる': '終わる',
    'おんがく': '音楽', 'おんな': '女', 'かいしゃ': '会社',
    'かいもの': '買い物', 'かう': '買う', 'かえす': '返す',
    'かえる': '帰る', 'かかる': '掛かる', 'かく': '書く',
    'かぜ': '風', 'かた': '方', 'かたち': '形', 'がっこう': '学校',
    'かど': '角', 'かなしい': '悲しい', 'かのじょ': '彼女',
    'かみ': '紙', 'からだ': '体', 'かりる': '借りる',
    'かるい': '軽い', 'かれ': '彼', 'かわ': '川',
    'きいろい': '黄色い', 'きく': '聞く', 'きた': '北',
    'きたない': '汚い', 'きって': '切手', 'きる': '切る',
    'きれい': '綺麗', 'ぎんこう': '銀行', 'くすり': '薬',
    'くち': '口', 'くつ': '靴', 'くに': '国', 'くもる': '曇る',
    'くらい': '暗い', 'くる': '来る', 'くるま': '車',
    'けす': '消す', 'こたえる': '答える', 'ことし': '今年',
    'ことば': '言葉', 'こども': '子供', 'こまる': '困る',
    'こめ': '米', 'ころぶ': '転ぶ',
    'さかな': '魚', 'さがす': '探す', 'さき': '先',
    'さむい': '寒い', 'しごと': '仕事', 'した': '下',
    'しぬ': '死ぬ', 'しまる': '閉まる', 'しめる': '閉める',
    'しる': '知る', 'しろい': '白い', 'すき': '好き',
    'すくない': '少ない', 'すずしい': '涼しい', 'すむ': '住む',
    'すわる': '座る', 'せまい': '狭い',
    'たかい': '高い', 'たつ': '立つ', 'たのしい': '楽しい',
    'たべる': '食べる', 'ちいさい': '小さい', 'ちかい': '近い',
    'ちかく': '近く', 'ちから': '力', 'ちず': '地図',
    'つかう': '使う', 'つかれる': '疲れる', 'つくる': '作る',
    'つける': '付ける', 'つよい': '強い',
    'てがみ': '手紙', 'でる': '出る',
    'でんき': '電気', 'でんしゃ': '電車', 'でんわ': '電話',
    'とおい': '遠い', 'ところ': '所', 'とし': '年',
    'としょかん': '図書館', 'とぶ': '飛ぶ', 'とまる': '止まる',
    'ともだち': '友達', 'とる': '取る', 'とり': '鳥',
    'ながい': '長い', 'なく': '泣く', 'なつ': '夏',
    'ならう': '習う', 'ならぶ': '並ぶ',
    'にく': '肉', 'にし': '西', 'にわ': '庭',
    'ぬぐ': '脱ぐ', 'ぬる': '塗る',
    'ねこ': '猫', 'ねる': '寝る',
    'のぼる': '登る', 'のむ': '飲む', 'のる': '乗る',
    'はいる': '入る', 'はじまる': '始まる', 'はじめ': '始め',
    'はしる': '走る', 'はたらく': '働く', 'はな': '花',
    'はなし': '話', 'はなす': '話す', 'はやい': '早い',
    'はる': '春', 'ひがし': '東', 'ひくい': '低い',
    'ひく': '引く', 'ひと': '人', 'ひとつ': '一つ',
    'ひとり': '一人', 'ひま': '暇', 'ひろい': '広い',
    'ふとい': '太い', 'ふゆ': '冬', 'ふるい': '古い',
    'へた': '下手', 'へや': '部屋',
    'ほしい': '欲しい', 'ほそい': '細い', 'ほん': '本',
    'まいにち': '毎日', 'まえ': '前', 'まがる': '曲がる',
    'まち': '町', 'まつ': '待つ', 'まど': '窓',
    'まるい': '丸い', 'みえる': '見える', 'みがく': '磨く',
    'みぎ': '右', 'みじかい': '短い', 'みず': '水',
    'みせ': '店', 'みち': '道', 'みなみ': '南',
    'みみ': '耳', 'みる': '見る',
    'むずかしい': '難しい', 'むすこ': '息子', 'むすめ': '娘',
    'め': '目', 'もつ': '持つ', 'もの': '物',
    'やすい': '安い', 'やすみ': '休み', 'やすむ': '休む',
    'やま': '山', 'ゆうめい': '有名',
    'よぶ': '呼ぶ', 'よむ': '読む', 'よる': '夜',
    'よわい': '弱い',
    'わかい': '若い', 'わかる': '分かる', 'わすれる': '忘れる',
    'わたす': '渡す', 'わたる': '渡る',
    # N4 common
    'あつめる': '集める', 'あらわれる': '現れる', 'いきる': '生きる',
    'うごく': '動く', 'うつくしい': '美しい', 'うつす': '写す',
    'うつる': '移る', 'うまい': '旨い', 'うれしい': '嬉しい',
    'おこる': '怒る', 'おこなう': '行う', 'おちる': '落ちる',
    'おどる': '踊る', 'おもいだす': '思い出す', 'およぐ': '泳ぐ',
    'かえる': '変える', 'かたい': '硬い', 'かなう': '叶う',
    'かよう': '通う', 'きこえる': '聞こえる', 'きまる': '決まる',
    'きめる': '決める', 'くわしい': '詳しい',
    'こわい': '怖い', 'こわす': '壊す',
    'さがる': '下がる', 'さげる': '下げる', 'さそう': '誘う',
    'しらべる': '調べる', 'すぎる': '過ぎる',
    'たおれる': '倒れる', 'たしか': '確か', 'たすける': '助ける',
    'ちがう': '違う', 'つたえる': '伝える', 'つづく': '続く',
    'つづける': '続ける', 'つとめる': '勤める',
    'とどける': '届ける', 'なおす': '直す', 'なおる': '治る',
    'なくなる': '無くなる', 'なげる': '投げる', 'ぬすむ': '盗む',
    'ねがう': '願う', 'のこる': '残る', 'のぼる': '上る',
    'はこぶ': '運ぶ', 'はずかしい': '恥ずかしい',
    'ひっこす': '引っ越す', 'ひろげる': '広げる',
    'ふえる': '増える', 'まける': '負ける', 'まもる': '守る',
    'みつかる': '見つかる', 'みつける': '見つける',
    'むかえる': '迎える', 'もうしこむ': '申し込む',
    'もどる': '戻る', 'やくにたつ': '役に立つ', 'やめる': '辞める',
    'ゆるす': '許す', 'よろこぶ': '喜ぶ',
    'わかれる': '別れる', 'わらう': '笑う',
    # N3 common
    'あたえる': '与える', 'あやまる': '謝る', 'あらそう': '争う',
    'いのる': '祈る', 'うたがう': '疑う', 'うばう': '奪う',
    'おさえる': '抑える', 'おどろく': '驚く',
    'かかえる': '抱える', 'かせぐ': '稼ぐ', 'かたづける': '片付ける',
    'くらべる': '比べる', 'くるしい': '苦しい',
    'さからう': '逆らう', 'さまたげる': '妨げる',
    'したがう': '従う', 'すくう': '救う', 'すすめる': '勧める',
    'たずねる': '訪ねる', 'たたかう': '戦う', 'たよる': '頼る',
    'ちかづく': '近づく', 'つかまえる': '捕まえる', 'つながる': '繋がる',
    'とける': '溶ける', 'とめる': '止める',
    'なやむ': '悩む', 'にげる': '逃げる', 'ぬける': '抜ける',
    'のぞむ': '望む', 'はげます': '励ます', 'はたす': '果たす',
    'ふせぐ': '防ぐ', 'まよう': '迷う', 'みとめる': '認める',
    'めざす': '目指す', 'もうける': '設ける', 'もとめる': '求める',
    'やぶる': '破る', 'ゆずる': '譲る', 'よごれる': '汚れる',
}


def clean_vocabulary(data):
    """Clean and deduplicate vocabulary data. Remove hiragana-only duplicates.
    For hiragana-only words without a kanji counterpart, add kanji_form if known."""
    
    # First pass: collect all kanji-containing entries indexed by (reading, meaning)
    kanji_entries = {}
    for item in data:
        word = item.get('word', '').strip()
        reading = item.get('reading', '').strip()
        meaning = item.get('meaning', '').strip()
        if has_kanji(word) and reading and meaning:
            kanji_entries[(reading, meaning)] = word
    
    seen = set()
    cleaned = []
    
    for item in data:
        word = item.get('word', '').strip()
        if not word or is_noise(word):
            continue
        
        level = item.get('level', '').strip()
        reading = item.get('reading', '').strip()
        meaning = item.get('meaning', '').strip()
        word_type = item.get('type', '').strip()
        
        # Skip hiragana-only duplicates where a kanji version exists
        if not has_kanji(word) and not reading:
            # Check if a kanji entry has this word as its reading and same meaning
            if (word, meaning) in kanji_entries:
                continue
            # Also check via HIRAGANA_TO_KANJI mapping
            if word in HIRAGANA_TO_KANJI:
                continue
        
        key = (word, level)
        if key in seen:
            continue
        seen.add(key)
        
        # Skip entries with no meaning
        if not meaning:
            continue
        
        # For hiragana-only words, try to add kanji_form
        kanji_form = ''
        if not has_kanji(word):
            if word in HIRAGANA_TO_KANJI:
                kanji_form = HIRAGANA_TO_KANJI[word]
            elif (word, meaning) in kanji_entries:
                kanji_form = kanji_entries[(word, meaning)]
        
        # Enrich with type
        if not word_type and word in VOCAB_TYPE_MAP:
            word_type = VOCAB_TYPE_MAP[word]
        elif not word_type:
            # Auto-detect type from word endings
            effective_word = kanji_form or word
            if effective_word.endswith('い') and has_kanji(effective_word):
                word_type = "形容詞 (Tính từ -i)"
            elif effective_word.endswith(('る', 'す', 'く', 'ぐ', 'む', 'ぬ', 'ぶ', 'つ', 'う')):
                word_type = "動詞 (Động từ)"
        
        # Enrich with examples: prefer kanji_form for lookup
        example = ''
        example_reading = ''
        example_meaning = ''
        lookup_word = kanji_form or word
        if lookup_word in VOCAB_EXAMPLES:
            ex = VOCAB_EXAMPLES[lookup_word]
            example = ex.get('example', '')
            example_reading = ex.get('example_reading', '')
            example_meaning = ex.get('example_meaning', '')
        elif word in VOCAB_EXAMPLES:
            ex = VOCAB_EXAMPLES[word]
            example = ex.get('example', '')
            example_reading = ex.get('example_reading', '')
            example_meaning = ex.get('example_meaning', '')
        elif has_japanese(lookup_word):
            auto_ex = auto_generate_example(lookup_word, reading or word, meaning, word_type)
            if auto_ex:
                example, example_reading, example_meaning = auto_ex
        elif has_japanese(word):
            auto_ex = auto_generate_example(word, reading, meaning, word_type)
            if auto_ex:
                example, example_reading, example_meaning = auto_ex
        
        cleaned.append({
            'word': word,
            'level': level,
            'reading': reading,
            'meaning': meaning,
            'type': word_type,
            'kanji_form': kanji_form,
            'example': example,
            'example_reading': example_reading,
            'example_meaning': example_meaning,
        })
    
    return cleaned


def clean_kanji(data):
    """Clean and enrich kanji data."""
    seen = set()
    cleaned = []
    
    for item in data:
        kanji = item.get('kanji', '').strip()
        if not kanji or len(kanji) != 1:
            continue
        
        level = item.get('level', '').strip()
        meaning = item.get('meaning', '').strip()
        
        key = (kanji, level)
        if key in seen:
            continue
        seen.add(key)
        
        enrichment = KANJI_ENRICHMENT.get(kanji, {})
        
        onyomi = enrichment.get('onyomi', item.get('onyomi', ''))
        kunyomi = enrichment.get('kunyomi', item.get('kunyomi', ''))
        strokes = enrichment.get('strokes', item.get('strokes', 0))
        radical = enrichment.get('radical', '')
        meaning_vi = enrichment.get('meaning_vi', '')
        examples = enrichment.get('examples', [])
        
        cleaned.append({
            'kanji': kanji,
            'level': level,
            'meaning': meaning,
            'meaning_vi': meaning_vi,
            'onyomi': onyomi,
            'kunyomi': kunyomi,
            'strokes': strokes,
            'radical': radical,
            'examples': examples,
        })
    
    return cleaned


def has_japanese(text):
    """Check if text contains any Japanese characters (hiragana, katakana, kanji)."""
    for ch in text:
        cp = ord(ch)
        # Hiragana: U+3040-U+309F, Katakana: U+30A0-U+30FF, Kanji: U+4E00-U+9FFF
        if (0x3040 <= cp <= 0x309F) or (0x30A0 <= cp <= 0x30FF) or (0x4E00 <= cp <= 0x9FFF):
            return True
    return False


def clean_grammar(data):
    """Clean and enrich grammar data."""
    seen = set()
    cleaned = []
    
    for item in data:
        pattern = item.get('pattern', '').strip()
        if not pattern or is_noise(pattern):
            continue
        
        level = item.get('level', '').strip()
        meaning = item.get('meaning', '').strip()
        
        # Skip Vietnamese-only entries (duplicates of Japanese patterns)
        if not has_japanese(pattern):
            continue
        
        key = (pattern, level)
        if key in seen:
            continue
        seen.add(key)
        
        enrichment = GRAMMAR_ENRICHMENT.get(pattern, {})
        
        structure = enrichment.get('structure', item.get('structure', ''))
        explanation = enrichment.get('explanation', '')
        example = enrichment.get('example', item.get('example', ''))
        example_reading = enrichment.get('example_reading', '')
        example_meaning = enrichment.get('example_meaning', item.get('example_meaning', ''))
        
        if enrichment.get('meaning'):
            meaning = enrichment['meaning']
        
        cleaned.append({
            'pattern': pattern,
            'level': level,
            'meaning': meaning,
            'structure': structure,
            'explanation': explanation,
            'example': example,
            'example_reading': example_reading,
            'example_meaning': example_meaning,
        })
    
    return cleaned


def import_data(conn):
    """Import all cleaned data into the database."""
    c = conn.cursor()
    
    # Import vocabulary
    with open(os.path.join(DATA_DIR, 'vocabulary.json'), 'r', encoding='utf-8') as f:
        vocab_data = json.load(f)
    
    vocab_cleaned = clean_vocabulary(vocab_data)
    for v in vocab_cleaned:
        try:
            c.execute('''INSERT INTO vocabulary (word, level, reading, meaning, type, kanji_form, example, example_reading, example_meaning)
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                      (v['word'], v['level'], v['reading'], v['meaning'], v['type'],
                       v.get('kanji_form', ''),
                       v['example'], v['example_reading'], v['example_meaning']))
        except sqlite3.IntegrityError:
            pass
    
    print(f"Imported {len(vocab_cleaned)} vocabulary entries")
    
    # Import kanji
    with open(os.path.join(DATA_DIR, 'kanji.json'), 'r', encoding='utf-8') as f:
        kanji_data = json.load(f)
    
    kanji_cleaned = clean_kanji(kanji_data)
    for k in kanji_cleaned:
        try:
            c.execute('''INSERT INTO kanji (kanji, level, meaning, meaning_vi, onyomi, kunyomi, strokes, radical)
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                      (k['kanji'], k['level'], k['meaning'], k['meaning_vi'],
                       k['onyomi'], k['kunyomi'], k['strokes'], k['radical']))
            kanji_id = c.lastrowid
            
            for ex in k.get('examples', []):
                c.execute('''INSERT INTO kanji_examples (kanji_id, word, reading, meaning)
                             VALUES (?, ?, ?, ?)''',
                          (kanji_id, ex['word'], ex['reading'], ex['meaning']))
        except sqlite3.IntegrityError:
            pass
    
    print(f"Imported {len(kanji_cleaned)} kanji entries")
    
    # Import grammar
    with open(os.path.join(DATA_DIR, 'grammar.json'), 'r', encoding='utf-8') as f:
        grammar_data = json.load(f)
    
    grammar_cleaned = clean_grammar(grammar_data)
    for g in grammar_cleaned:
        try:
            c.execute('''INSERT INTO grammar (pattern, level, meaning, structure, explanation, example, example_reading, example_meaning)
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                      (g['pattern'], g['level'], g['meaning'], g['structure'],
                       g['explanation'], g['example'], g['example_reading'], g['example_meaning']))
        except sqlite3.IntegrityError:
            pass
    
    print(f"Imported {len(grammar_cleaned)} grammar entries")
    
    conn.commit()


def main():
    print("Creating database...")
    conn = create_db()
    print("Importing and cleaning data...")
    import_data(conn)
    
    # Print summary
    c = conn.cursor()
    for table in ['vocabulary', 'kanji', 'grammar']:
        c.execute(f'SELECT level, COUNT(*) FROM {table} GROUP BY level ORDER BY level')
        rows = c.fetchall()
        print(f"\n{table.upper()}:")
        for level, count in rows:
            print(f"  {level}: {count}")
    
    conn.close()
    print(f"\nDatabase created: {DB_PATH}")


if __name__ == '__main__':
    main()
