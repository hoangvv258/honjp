#!/usr/bin/env python3
"""
HonJP - Japanese Learning Web Application
Flask backend with SQLite database
"""

import os
import sqlite3
import random
from datetime import datetime
from flask import Flask, render_template, request, jsonify, g

app = Flask(__name__)

# For serverless/read-only environments, use /tmp
_base_dir = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(_base_dir, 'honjp.db')
if not os.access(_base_dir, os.W_OK):
    DB_PATH = os.path.join('/tmp', 'honjp.db')

LEVELS = ['N5', 'N4', 'N3', 'N2', 'N1']

# Kanji component decomposition for common kanji
KANJI_COMPONENTS = {
    '日': [{'char': '日', 'meaning': 'Mặt trời'}],
    '月': [{'char': '月', 'meaning': 'Mặt trăng'}],
    '木': [{'char': '木', 'meaning': 'Cây'}],
    '山': [{'char': '山', 'meaning': 'Núi'}],
    '川': [{'char': '川', 'meaning': 'Sông'}],
    '田': [{'char': '田', 'meaning': 'Ruộng'}],
    '人': [{'char': '人', 'meaning': 'Người'}],
    '口': [{'char': '口', 'meaning': 'Miệng'}],
    '火': [{'char': '火', 'meaning': 'Lửa'}],
    '水': [{'char': '水', 'meaning': 'Nước'}],
    '金': [{'char': '金', 'meaning': 'Vàng/Kim loại'}],
    '土': [{'char': '土', 'meaning': 'Đất'}],
    '大': [{'char': '一', 'meaning': 'Một'}, {'char': '人', 'meaning': 'Người'}],
    '小': [{'char': '亅', 'meaning': 'Móc'}, {'char': '八', 'meaning': 'Tám'}],
    '休': [{'char': '亻', 'meaning': 'Người (bộ nhân)'}, {'char': '木', 'meaning': 'Cây → Người tựa vào cây = nghỉ'}],
    '体': [{'char': '亻', 'meaning': 'Người (bộ nhân)'}, {'char': '本', 'meaning': 'Gốc → Gốc của người = thân thể'}],
    '何': [{'char': '亻', 'meaning': 'Người (bộ nhân)'}, {'char': '可', 'meaning': 'Có thể → Người hỏi "có thể gì?" = cái gì'}],
    '会': [{'char': '人', 'meaning': 'Người'}, {'char': '云', 'meaning': 'Nói → Người gặp nói chuyện = gặp mặt'}],
    '明': [{'char': '日', 'meaning': 'Mặt trời'}, {'char': '月', 'meaning': 'Mặt trăng → Trời + Trăng = sáng'}],
    '好': [{'char': '女', 'meaning': 'Nữ'}, {'char': '子', 'meaning': 'Con → Mẹ yêu con = thích'}],
    '安': [{'char': '宀', 'meaning': 'Mái nhà'}, {'char': '女', 'meaning': 'Nữ → Phụ nữ trong nhà = yên'}],
    '男': [{'char': '田', 'meaning': 'Ruộng'}, {'char': '力', 'meaning': 'Sức → Cày ruộng bằng sức = đàn ông'}],
    '花': [{'char': '艹', 'meaning': 'Cỏ (bộ thảo)'}, {'char': '化', 'meaning': 'Biến hóa → Cỏ biến hóa = hoa'}],
    '話': [{'char': '言', 'meaning': 'Lời nói'}, {'char': '舌', 'meaning': 'Lưỡi → Dùng lưỡi nói = nói chuyện'}],
    '語': [{'char': '言', 'meaning': 'Lời'}, {'char': '吾', 'meaning': 'Ta → Lời của ta = ngôn ngữ'}],
    '読': [{'char': '言', 'meaning': 'Lời'}, {'char': '売', 'meaning': 'Bán → Bán lời = đọc'}],
    '書': [{'char': '聿', 'meaning': 'Bút'}, {'char': '日', 'meaning': 'Ngày → Dùng bút hàng ngày = viết'}],
    '食': [{'char': '人', 'meaning': 'Người'}, {'char': '良', 'meaning': 'Tốt → Người cần điều tốt = ăn'}],
    '飲': [{'char': '食', 'meaning': 'Ăn'}, {'char': '欠', 'meaning': 'Khuyết → Ăn mà thiếu = uống'}],
    '見': [{'char': '目', 'meaning': 'Mắt'}, {'char': '儿', 'meaning': 'Chân → Mắt trên chân = nhìn'}],
    '聞': [{'char': '門', 'meaning': 'Cổng'}, {'char': '耳', 'meaning': 'Tai → Tai ở cổng = nghe'}],
    '学': [{'char': '⺍', 'meaning': 'Ký tự'}, {'char': '子', 'meaning': 'Con → Con học chữ = học'}],
    '生': [{'char': '生', 'meaning': 'Cây mọc từ đất = sống, sinh'}],
    '先': [{'char': '⺧', 'meaning': 'Chân'}, {'char': '儿', 'meaning': 'Người → Người đi trước = trước'}],
    '時': [{'char': '日', 'meaning': 'Ngày'}, {'char': '寺', 'meaning': 'Chùa → Ngày ở chùa = thời gian'}],
    '間': [{'char': '門', 'meaning': 'Cổng'}, {'char': '日', 'meaning': 'Mặt trời → Trời lọt qua cổng = khoảng'}],
    '新': [{'char': '立', 'meaning': 'Đứng'}, {'char': '木', 'meaning': 'Cây'}, {'char': '斤', 'meaning': 'Rìu → Rìu chặt cây đứng = mới'}],
    '古': [{'char': '十', 'meaning': 'Mười'}, {'char': '口', 'meaning': 'Miệng → Mười đời truyền miệng = cũ'}],
    '長': [{'char': '長', 'meaning': 'Tóc dài của người già = dài, trưởng'}],
    '白': [{'char': '白', 'meaning': 'Ánh sáng mặt trời = trắng'}],
    '百': [{'char': '一', 'meaning': 'Một'}, {'char': '白', 'meaning': 'Trắng → Một trăm'}],
    '千': [{'char': '千', 'meaning': 'Người đi xa = nghìn'}],
    '万': [{'char': '万', 'meaning': 'Rất nhiều = vạn'}],
    '円': [{'char': '冂', 'meaning': 'Bao quanh → Hình tròn = yên (tiền)'}],
    '入': [{'char': '入', 'meaning': 'Người đi vào = vào'}],
    '出': [{'char': '山', 'meaning': 'Núi chồng = ra ngoài'}],
    '立': [{'char': '立', 'meaning': 'Người đứng trên mặt đất = đứng'}],
    '上': [{'char': '上', 'meaning': 'Nét trên đường = trên'}],
    '下': [{'char': '下', 'meaning': 'Nét dưới đường = dưới'}],
    '中': [{'char': '口', 'meaning': 'Hộp'}, {'char': '丨', 'meaning': 'Nét dọc → Giữa hộp = trong, giữa'}],
    '右': [{'char': '口', 'meaning': 'Miệng'}, {'char': '手', 'meaning': 'Tay → Tay cầm đồ ăn = phải'}],
    '左': [{'char': '工', 'meaning': 'Công cụ'}, {'char': '手', 'meaning': 'Tay → Tay cầm dụng cụ = trái'}],
    '北': [{'char': '北', 'meaning': 'Hai người quay lưng = bắc'}],
    '南': [{'char': '南', 'meaning': 'Cây trong nhà ấm = nam'}],
    '東': [{'char': '木', 'meaning': 'Cây'}, {'char': '日', 'meaning': 'Trời → Mặt trời sau cây = đông'}],
    '西': [{'char': '西', 'meaning': 'Chim về tổ khi trời tối = tây'}],
    '天': [{'char': '一', 'meaning': 'Một'}, {'char': '大', 'meaning': 'Lớn → Trên người lớn = trời'}],
    '気': [{'char': '气', 'meaning': 'Hơi'}, {'char': '〆', 'meaning': 'Gạo → Khí từ gạo nấu = khí, tinh thần'}],
    '電': [{'char': '雨', 'meaning': 'Mưa'}, {'char': '田', 'meaning': 'Ruộng → Sấm sét trên ruộng = điện'}],
    '車': [{'char': '車', 'meaning': 'Hình xe nhìn từ trên = xe'}],
    '門': [{'char': '門', 'meaning': 'Hai cánh cửa = cổng'}],
    '雨': [{'char': '雨', 'meaning': 'Giọt nước rơi từ trời = mưa'}],
    '国': [{'char': '囗', 'meaning': 'Biên giới'}, {'char': '玉', 'meaning': 'Ngọc → Báu vật trong biên giới = nước'}],
    '手': [{'char': '手', 'meaning': 'Hình bàn tay = tay'}],
    '足': [{'char': '口', 'meaning': 'Đầu gối'}, {'char': '止', 'meaning': 'Bàn chân = chân'}],
    '目': [{'char': '目', 'meaning': 'Hình con mắt = mắt'}],
    '耳': [{'char': '耳', 'meaning': 'Hình lỗ tai = tai'}],
    '力': [{'char': '力', 'meaning': 'Cánh tay cong = sức lực'}],
    '心': [{'char': '心', 'meaning': 'Hình trái tim = tâm, lòng'}],
    '思': [{'char': '田', 'meaning': 'Ruộng (não)'}, {'char': '心', 'meaning': 'Tim → Não + tim = suy nghĩ'}],
    '友': [{'char': '又', 'meaning': 'Tay → Hai tay nắm nhau = bạn'}],
    '父': [{'char': '父', 'meaning': 'Tay cầm rìu = cha'}],
    '母': [{'char': '母', 'meaning': 'Phụ nữ cho con bú = mẹ'}],
    '子': [{'char': '子', 'meaning': 'Trẻ em quấn tã = con'}],
    '女': [{'char': '女', 'meaning': 'Hình người quỳ = nữ'}],
    '来': [{'char': '木', 'meaning': 'Cây'}, {'char': '人', 'meaning': 'Người → Người đến dưới cây = đến'}],
    '行': [{'char': '彳', 'meaning': 'Bước chân → Bước chân ở ngã tư = đi'}],
    '帰': [{'char': '刂', 'meaning': 'Dao'}, {'char': '帚', 'meaning': 'Chổi → Phụ nữ cầm chổi = về nhà'}],
    '買': [{'char': '网', 'meaning': 'Lưới'}, {'char': '貝', 'meaning': 'Vỏ sò (tiền) → Dùng tiền = mua'}],
    '売': [{'char': '士', 'meaning': 'Người'}, {'char': '買', 'meaning': 'Mua → Người đưa hàng = bán'}],
    '待': [{'char': '彳', 'meaning': 'Bước'}, {'char': '寺', 'meaning': 'Chùa → Đứng chờ ở chùa = đợi'}],
    '持': [{'char': '扌', 'meaning': 'Tay'}, {'char': '寺', 'meaning': 'Chùa → Tay giữ đồ ở chùa = giữ, cầm'}],
    '教': [{'char': '孝', 'meaning': 'Hiếu thảo'}, {'char': '攵', 'meaning': 'Tay cầm roi → Dạy bảo = dạy'}],
    '勉': [{'char': '免', 'meaning': 'Miễn'}, {'char': '力', 'meaning': 'Sức → Cố gắng bằng sức = siêng năng'}],
    '強': [{'char': '弓', 'meaning': 'Cung'}, {'char': '虫', 'meaning': 'Sâu → Sâu kéo cung = mạnh'}],
    '使': [{'char': '亻', 'meaning': 'Người'}, {'char': '吏', 'meaning': 'Quan → Người sai quan = sử dụng'}],
    '作': [{'char': '亻', 'meaning': 'Người'}, {'char': '乍', 'meaning': 'Đột ngột → Người làm = tạo, làm'}],
    '知': [{'char': '矢', 'meaning': 'Mũi tên'}, {'char': '口', 'meaning': 'Miệng → Nói nhanh như tên = biết'}],
    '多': [{'char': '夕', 'meaning': 'Tối'}, {'char': '夕', 'meaning': 'Tối → Nhiều đêm = nhiều'}],
    '少': [{'char': '小', 'meaning': 'Nhỏ'}, {'char': '丿', 'meaning': 'Nét phẩy → Nhỏ bớt = ít'}],
    '高': [{'char': '高', 'meaning': 'Hình tòa nhà cao = cao'}],
    '低': [{'char': '亻', 'meaning': 'Người'}, {'char': '氐', 'meaning': 'Đáy → Người ở thấp = thấp'}],
    '近': [{'char': '斤', 'meaning': 'Rìu'}, {'char': '辶', 'meaning': 'Đi → Đi đến gần = gần'}],
    '遠': [{'char': '袁', 'meaning': 'Áo dài'}, {'char': '辶', 'meaning': 'Đi → Đi xa = xa'}],
    '早': [{'char': '日', 'meaning': 'Mặt trời'}, {'char': '十', 'meaning': 'Mười → Mặt trời lên = sớm'}],
    '朝': [{'char': '月', 'meaning': 'Trăng'}, {'char': '日', 'meaning': 'Trời → Trăng lặn trời lên = buổi sáng'}],
    '昼': [{'char': '尺', 'meaning': 'Thước'}, {'char': '日', 'meaning': 'Mặt trời → Mặt trời cao = buổi trưa'}],
    '夜': [{'char': '亠', 'meaning': 'Đầu'}, {'char': '夕', 'meaning': 'Tối → Người nằm lúc tối = đêm'}],
    '春': [{'char': '日', 'meaning': 'Mặt trời'}, {'char': '屯', 'meaning': 'Mầm cây → Mầm mọc dưới nắng = xuân'}],
    '夏': [{'char': '夊', 'meaning': 'Bước'}, {'char': '頁', 'meaning': 'Đầu → Người đi dưới nắng = hè'}],
    '秋': [{'char': '禾', 'meaning': 'Lúa'}, {'char': '火', 'meaning': 'Lửa → Lúa chín vàng = thu'}],
    '冬': [{'char': '夂', 'meaning': 'Cuối'}, {'char': '冫', 'meaning': 'Băng → Cuối năm lạnh = đông'}],
}


def ensure_db():
    """Create database if it doesn't exist (for deployment)."""
    if not os.path.exists(DB_PATH):
        import init_db
        init_db.DB_PATH = DB_PATH
        conn = init_db.create_db()
        init_db.import_data(conn)
        conn.close()


def get_db():
    if 'db' not in g:
        ensure_db()
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exception):
    db = g.pop('db', None)
    if db is not None:
        db.close()


# ==================== Pages ====================

@app.route('/')
def index():
    db = get_db()
    stats = {}
    for table in ['vocabulary', 'kanji', 'grammar']:
        row = db.execute(f'SELECT COUNT(*) as total FROM {table}').fetchone()
        stats[table] = row['total']
        
        level_stats = db.execute(
            f'SELECT level, COUNT(*) as cnt FROM {table} GROUP BY level ORDER BY level'
        ).fetchall()
        stats[f'{table}_levels'] = {r['level']: r['cnt'] for r in level_stats}
    
    # Progress stats
    progress = db.execute(
        'SELECT item_type, status, COUNT(*) as cnt FROM progress GROUP BY item_type, status'
    ).fetchall()
    stats['progress'] = {}
    for p in progress:
        if p['item_type'] not in stats['progress']:
            stats['progress'][p['item_type']] = {}
        stats['progress'][p['item_type']][p['status']] = p['cnt']
    
    return render_template('index.html', stats=stats, levels=LEVELS)


@app.route('/vocabulary')
def vocabulary_page():
    return render_template('vocabulary.html', levels=LEVELS)


@app.route('/kanji')
def kanji_page():
    return render_template('kanji.html', levels=LEVELS)


@app.route('/grammar')
def grammar_page():
    return render_template('grammar.html', levels=LEVELS)


@app.route('/flashcard')
def flashcard_page():
    return render_template('flashcard.html', levels=LEVELS)


@app.route('/quiz')
def quiz_page():
    return render_template('quiz.html', levels=LEVELS)


# ==================== API Endpoints ====================

@app.route('/api/vocabulary')
def api_vocabulary():
    db = get_db()
    level = request.args.get('level', '')
    search = request.args.get('search', '')
    bookmark = request.args.get('bookmark', '')  # 'review', 'learned', or ''
    page = max(1, int(request.args.get('page', 1)))
    per_page = min(100, int(request.args.get('per_page', 50)))
    offset = (page - 1) * per_page
    
    query = 'SELECT v.* FROM vocabulary v'
    params = []
    
    if bookmark:
        query += ' INNER JOIN bookmarks b ON b.item_type = "vocabulary" AND b.item_id = v.id AND b.status = ?'
        params.append(bookmark)
    
    query += ' WHERE 1=1'
    
    if level:
        query += ' AND v.level = ?'
        params.append(level)
    if search:
        query += ' AND (v.word LIKE ? OR v.reading LIKE ? OR v.meaning LIKE ?)'
        search_param = f'%{search}%'
        params.extend([search_param, search_param, search_param])
    
    # Count total
    count_query = query.replace('SELECT v.*', 'SELECT COUNT(*)')
    total = db.execute(count_query, params).fetchone()[0]
    
    query += ' ORDER BY v.level, v.word LIMIT ? OFFSET ?'
    params.extend([per_page, offset])
    
    rows = db.execute(query, params).fetchall()
    items = [dict(r) for r in rows]
    
    return jsonify({
        'items': items,
        'total': total,
        'page': page,
        'per_page': per_page,
        'pages': (total + per_page - 1) // per_page
    })


@app.route('/api/kanji')
def api_kanji():
    db = get_db()
    level = request.args.get('level', '')
    search = request.args.get('search', '')
    bookmark = request.args.get('bookmark', '')
    page = max(1, int(request.args.get('page', 1)))
    per_page = min(100, int(request.args.get('per_page', 50)))
    offset = (page - 1) * per_page
    
    query = 'SELECT k.* FROM kanji k'
    params = []
    
    if bookmark:
        query += ' INNER JOIN bookmarks b ON b.item_type = "kanji" AND b.item_id = k.id AND b.status = ?'
        params.append(bookmark)
    
    query += ' WHERE 1=1'
    
    if level:
        query += ' AND k.level = ?'
        params.append(level)
    if search:
        query += ' AND (k.kanji LIKE ? OR k.meaning LIKE ? OR k.meaning_vi LIKE ? OR k.onyomi LIKE ? OR k.kunyomi LIKE ?)'
        search_param = f'%{search}%'
        params.extend([search_param] * 5)
    
    count_query = query.replace('SELECT k.*', 'SELECT COUNT(*)')
    total = db.execute(count_query, params).fetchone()[0]
    
    query += ' ORDER BY k.level, k.kanji LIMIT ? OFFSET ?'
    params.extend([per_page, offset])
    
    rows = db.execute(query, params).fetchall()
    items = []
    for r in rows:
        item = dict(r)
        examples = db.execute(
            'SELECT word, reading, meaning FROM kanji_examples WHERE kanji_id = ?',
            (r['id'],)
        ).fetchall()
        item['examples'] = [dict(e) for e in examples]
        items.append(item)
    
    return jsonify({
        'items': items,
        'total': total,
        'page': page,
        'per_page': per_page,
        'pages': (total + per_page - 1) // per_page
    })


@app.route('/api/grammar')
def api_grammar():
    db = get_db()
    level = request.args.get('level', '')
    search = request.args.get('search', '')
    bookmark = request.args.get('bookmark', '')
    page = max(1, int(request.args.get('page', 1)))
    per_page = min(100, int(request.args.get('per_page', 50)))
    offset = (page - 1) * per_page
    
    query = 'SELECT g.* FROM grammar g'
    params = []
    
    if bookmark:
        query += ' INNER JOIN bookmarks b ON b.item_type = "grammar" AND b.item_id = g.id AND b.status = ?'
        params.append(bookmark)
    
    query += ' WHERE 1=1'
    
    if level:
        query += ' AND g.level = ?'
        params.append(level)
    if search:
        query += ' AND (g.pattern LIKE ? OR g.meaning LIKE ? OR g.explanation LIKE ?)'
        search_param = f'%{search}%'
        params.extend([search_param] * 3)
    
    count_query = query.replace('SELECT g.*', 'SELECT COUNT(*)')
    total = db.execute(count_query, params).fetchone()[0]
    
    query += ' ORDER BY g.level, g.pattern LIMIT ? OFFSET ?'
    params.extend([per_page, offset])
    
    rows = db.execute(query, params).fetchall()
    items = [dict(r) for r in rows]
    
    return jsonify({
        'items': items,
        'total': total,
        'page': page,
        'per_page': per_page,
        'pages': (total + per_page - 1) // per_page
    })


@app.route('/api/kanji/<kanji_char>')
def api_kanji_detail(kanji_char):
    """Get detailed info for a specific kanji including related vocabulary."""
    db = get_db()
    
    # Get kanji info
    kanji_row = db.execute('SELECT * FROM kanji WHERE kanji = ?', (kanji_char,)).fetchone()
    if not kanji_row:
        return jsonify({'error': 'Kanji not found'}), 404
    
    kanji_data = dict(kanji_row)
    
    # Get kanji examples
    examples = db.execute(
        'SELECT word, reading, meaning FROM kanji_examples WHERE kanji_id = ?',
        (kanji_row['id'],)
    ).fetchall()
    kanji_data['examples'] = [dict(e) for e in examples]
    
    # Add component decomposition
    kanji_data['components'] = KANJI_COMPONENTS.get(kanji_char, [])
    
    # Find vocabulary containing this kanji
    vocab_rows = db.execute(
        'SELECT word, reading, meaning, level, type FROM vocabulary WHERE word LIKE ? ORDER BY level LIMIT 20',
        (f'%{kanji_char}%',)
    ).fetchall()
    kanji_data['related_vocab'] = [dict(v) for v in vocab_rows]
    
    return jsonify(kanji_data)


@app.route('/api/vocabulary/<int:vocab_id>')
def api_vocab_detail(vocab_id):
    """Get detailed info for a specific vocabulary item including related kanji."""
    db = get_db()
    
    row = db.execute('SELECT * FROM vocabulary WHERE id = ?', (vocab_id,)).fetchone()
    if not row:
        return jsonify({'error': 'Vocabulary not found'}), 404
    
    item = dict(row)
    
    # Find kanji contained in this word (or kanji_form for hiragana words)
    related_kanji = []
    kanji_source = item.get('kanji_form') or item['word']
    for ch in kanji_source:
        cp = ord(ch)
        if 0x4E00 <= cp <= 0x9FFF:
            k = db.execute('SELECT kanji, meaning, meaning_vi, onyomi, kunyomi, level FROM kanji WHERE kanji = ?', (ch,)).fetchone()
            if k:
                related_kanji.append(dict(k))
    item['related_kanji'] = related_kanji
    
    # Find similar words (same reading or similar meaning)
    similar = db.execute(
        'SELECT id, word, reading, meaning, level FROM vocabulary WHERE level = ? AND id != ? AND (reading = ? OR word LIKE ?) LIMIT 10',
        (item['level'], vocab_id, item.get('reading', ''), f'%{item["word"][:1]}%')
    ).fetchall()
    item['similar_words'] = [dict(s) for s in similar]
    
    return jsonify(item)


@app.route('/api/grammar/<int:grammar_id>')
def api_grammar_detail(grammar_id):
    """Get detailed info for a specific grammar pattern."""
    db = get_db()
    
    row = db.execute('SELECT * FROM grammar WHERE id = ?', (grammar_id,)).fetchone()
    if not row:
        return jsonify({'error': 'Grammar not found'}), 404
    
    item = dict(row)
    
    # Find related grammar patterns (same level)
    related = db.execute(
        'SELECT id, pattern, meaning, level FROM grammar WHERE level = ? AND id != ? ORDER BY pattern LIMIT 10',
        (item['level'], grammar_id)
    ).fetchall()
    item['related_patterns'] = [dict(r) for r in related]
    
    return jsonify(item)


@app.route('/api/flashcard')
def api_flashcard():
    """Get random items for flashcard study."""
    db = get_db()
    card_type = request.args.get('type', 'vocabulary')
    level = request.args.get('level', 'N5')
    count = min(20, int(request.args.get('count', 10)))
    
    if card_type == 'vocabulary':
        rows = db.execute(
            'SELECT * FROM vocabulary WHERE level = ? ORDER BY RANDOM() LIMIT ?',
            (level, count)
        ).fetchall()
    elif card_type == 'kanji':
        rows = db.execute(
            'SELECT * FROM kanji WHERE level = ? ORDER BY RANDOM() LIMIT ?',
            (level, count)
        ).fetchall()
        items = []
        for r in rows:
            item = dict(r)
            examples = db.execute(
                'SELECT word, reading, meaning FROM kanji_examples WHERE kanji_id = ?',
                (r['id'],)
            ).fetchall()
            item['examples'] = [dict(e) for e in examples]
            items.append(item)
        return jsonify({'items': items})
    elif card_type == 'grammar':
        rows = db.execute(
            'SELECT * FROM grammar WHERE level = ? ORDER BY RANDOM() LIMIT ?',
            (level, count)
        ).fetchall()
    else:
        return jsonify({'error': 'Invalid type'}), 400
    
    return jsonify({'items': [dict(r) for r in rows]})


@app.route('/api/quiz')
def api_quiz():
    """Generate quiz questions."""
    db = get_db()
    quiz_type = request.args.get('type', 'vocabulary')
    level = request.args.get('level', 'N5')
    count = min(20, int(request.args.get('count', 10)))
    
    questions = []
    
    if quiz_type == 'vocabulary':
        # Get items with meaning
        rows = db.execute(
            "SELECT * FROM vocabulary WHERE level = ? AND meaning != '' ORDER BY RANDOM() LIMIT ?",
            (level, count)
        ).fetchall()
        
        all_meanings = db.execute(
            "SELECT DISTINCT meaning FROM vocabulary WHERE level = ? AND meaning != ''",
            (level,)
        ).fetchall()
        all_meanings = [r['meaning'] for r in all_meanings]
        
        for r in rows:
            correct = r['meaning']
            wrong = random.sample([m for m in all_meanings if m != correct], min(3, len(all_meanings) - 1))
            options = wrong + [correct]
            random.shuffle(options)
            
            questions.append({
                'id': r['id'],
                'question': r['word'],
                'reading': r['reading'],
                'correct': correct,
                'options': options,
            })
    
    elif quiz_type == 'kanji':
        rows = db.execute(
            "SELECT * FROM kanji WHERE level = ? AND meaning != '' ORDER BY RANDOM() LIMIT ?",
            (level, count)
        ).fetchall()
        
        all_meanings = db.execute(
            "SELECT DISTINCT meaning FROM kanji WHERE level = ? AND meaning != ''",
            (level,)
        ).fetchall()
        all_meanings = [r['meaning'] for r in all_meanings]
        
        for r in rows:
            correct = r['meaning']
            wrong = random.sample([m for m in all_meanings if m != correct], min(3, len(all_meanings) - 1))
            options = wrong + [correct]
            random.shuffle(options)
            
            questions.append({
                'id': r['id'],
                'question': r['kanji'],
                'correct': correct,
                'options': options,
            })
    
    elif quiz_type == 'grammar':
        rows = db.execute(
            "SELECT * FROM grammar WHERE level = ? AND meaning != '' ORDER BY RANDOM() LIMIT ?",
            (level, count)
        ).fetchall()
        
        all_meanings = db.execute(
            "SELECT DISTINCT meaning FROM grammar WHERE level = ? AND meaning != ''",
            (level,)
        ).fetchall()
        all_meanings = [r['meaning'] for r in all_meanings]
        
        for r in rows:
            correct = r['meaning']
            wrong = random.sample([m for m in all_meanings if m != correct], min(3, len(all_meanings) - 1))
            options = wrong + [correct]
            random.shuffle(options)
            
            questions.append({
                'id': r['id'],
                'question': r['pattern'],
                'correct': correct,
                'options': options,
            })
    
    return jsonify({'questions': questions})


@app.route('/api/progress', methods=['POST'])
def api_update_progress():
    """Update study progress."""
    db = get_db()
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data'}), 400
    
    item_type = data.get('item_type', '')
    item_id = data.get('item_id', 0)
    correct = data.get('correct', False)
    
    if not item_type or not item_id:
        return jsonify({'error': 'Missing fields'}), 400
    
    existing = db.execute(
        'SELECT * FROM progress WHERE item_type = ? AND item_id = ?',
        (item_type, item_id)
    ).fetchone()
    
    now = datetime.now().isoformat()
    
    if existing:
        if correct:
            new_correct = existing['correct_count'] + 1
            new_status = 'mastered' if new_correct >= 3 else 'learning'
            db.execute(
                'UPDATE progress SET correct_count = ?, status = ?, last_studied = ? WHERE id = ?',
                (new_correct, new_status, now, existing['id'])
            )
        else:
            db.execute(
                'UPDATE progress SET wrong_count = wrong_count + 1, status = ?, last_studied = ? WHERE id = ?',
                ('learning', now, existing['id'])
            )
    else:
        status = 'learning'
        db.execute(
            'INSERT INTO progress (item_type, item_id, status, correct_count, wrong_count, last_studied) VALUES (?, ?, ?, ?, ?, ?)',
            (item_type, item_id, status, 1 if correct else 0, 0 if correct else 1, now)
        )
    
    db.commit()
    return jsonify({'success': True})


@app.route('/api/stats')
def api_stats():
    """Get overall statistics."""
    db = get_db()
    stats = {}
    
    for table in ['vocabulary', 'kanji', 'grammar']:
        level_counts = db.execute(
            f'SELECT level, COUNT(*) as cnt FROM {table} GROUP BY level'
        ).fetchall()
        stats[table] = {r['level']: r['cnt'] for r in level_counts}
    
    progress = db.execute(
        'SELECT item_type, status, COUNT(*) as cnt FROM progress GROUP BY item_type, status'
    ).fetchall()
    stats['progress'] = {}
    for p in progress:
        if p['item_type'] not in stats['progress']:
            stats['progress'][p['item_type']] = {}
        stats['progress'][p['item_type']][p['status']] = p['cnt']
    
    return jsonify(stats)


# ---- Bookmark API ----

@app.route('/api/bookmark', methods=['POST'])
def api_set_bookmark():
    """Set or update bookmark status for an item."""
    db = get_db()
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data'}), 400

    item_type = data.get('item_type', '')
    item_id = data.get('item_id', 0)
    status = data.get('status', '')  # 'review', 'learned', or '' to remove

    if not item_type or not item_id:
        return jsonify({'error': 'Missing fields'}), 400
    if item_type not in ('vocabulary', 'kanji', 'grammar'):
        return jsonify({'error': 'Invalid item_type'}), 400

    if not status:
        # Remove bookmark
        db.execute('DELETE FROM bookmarks WHERE item_type = ? AND item_id = ?',
                    (item_type, item_id))
    else:
        if status not in ('review', 'learned'):
            return jsonify({'error': 'Invalid status'}), 400
        db.execute('''INSERT INTO bookmarks (item_type, item_id, status)
                      VALUES (?, ?, ?)
                      ON CONFLICT(item_type, item_id) DO UPDATE SET status = ?''',
                   (item_type, item_id, status, status))

    db.commit()
    return jsonify({'success': True, 'item_type': item_type, 'item_id': item_id, 'status': status})


@app.route('/api/bookmark')
def api_get_bookmarks():
    """Get bookmark status for items. Pass item_type and optionally item_id or status."""
    db = get_db()
    item_type = request.args.get('item_type', '')
    item_id = request.args.get('item_id', '')
    status = request.args.get('status', '')

    if item_type and item_id:
        row = db.execute('SELECT status FROM bookmarks WHERE item_type = ? AND item_id = ?',
                         (item_type, int(item_id))).fetchone()
        return jsonify({'status': row['status'] if row else ''})

    query = 'SELECT item_id, status FROM bookmarks WHERE 1=1'
    params = []
    if item_type:
        query += ' AND item_type = ?'
        params.append(item_type)
    if status:
        query += ' AND status = ?'
        params.append(status)

    rows = db.execute(query, params).fetchall()
    result = {r['item_id']: r['status'] for r in rows}
    return jsonify(result)


if __name__ == '__main__':
    if not os.path.exists(DB_PATH):
        print("Database not found. Run init_db.py first:")
        print("  python init_db.py")
        exit(1)
    
    app.run(debug=True, host='127.0.0.1', port=5000)
