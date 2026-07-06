#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
管理后台路由
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from io import BytesIO
import os
try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False
    pd = None
from models import db, User, Category, Group, Question, QuizRecord, QuizDetail, UserProgress
from utils import admin_required

admin_bp = Blueprint('admin', __name__)

TEMPLATES_DIR = 'templates'
ADMIN_TEMPLATES_DIR = os.path.join(TEMPLATES_DIR, 'admin')

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp'}

def _allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def _handle_background_image_upload():
    """处理背景图片上传，返回保存的文件路径"""
    file = request.files.get('background_image')
    if file and file.filename and _allowed_file(file.filename):
        filename = secure_filename(file.filename)
        upload_dir = os.path.join('project', 'static', 'uploads', 'backgrounds')
        os.makedirs(upload_dir, exist_ok=True)
        filepath = os.path.join(upload_dir, filename)
        file.save(filepath)
        return os.path.join('static', 'uploads', 'backgrounds', filename).replace('\\', '/')
    return None

@admin_bp.route('/')
@login_required
@admin_required
def admin_dashboard():
    return render_template('admin/dashboard.html')

# ==================== 分类管理 ====================
@admin_bp.route('/categories')
@login_required
@admin_required
def admin_categories():
    cats = Category.query.all()
    return render_template('admin/categories.html', categories=cats)

@admin_bp.route('/category/add', methods=['POST'])
@login_required
@admin_required
def admin_category_add():
    name = request.form['name']
    parent_id = request.form.get('parent_id', type=int)
    cat = Category(name=name, parent_id=parent_id)
    db.session.add(cat)
    db.session.commit()
    flash('分类添加成功')
    return redirect(url_for('admin.admin_categories'))

@admin_bp.route('/category/delete/<int:id>')
@login_required
@admin_required
def admin_category_delete(id):
    cat = Category.query.get_or_404(id)
    db.session.delete(cat)
    db.session.commit()
    flash('分类已删除')
    return redirect(url_for('admin.admin_categories'))

# ==================== 分组管理 ====================
@admin_bp.route('/groups')
@login_required
@admin_required
def admin_groups():
    groups = Group.query.all()
    return render_template('admin/groups.html', groups=groups)

@admin_bp.route('/group/add', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_group_add():
    if request.method == 'POST':
        name = request.form['name']
        category_id = request.form['category_id']
        order = request.form.get('order', 0, type=int)
        description = request.form.get('description', '')
        study_content = request.form.get('study_content', '')
        unlock_order = request.form.get('unlock_order', 0, type=int)
        background_image = _handle_background_image_upload()
        group = Group(name=name, category_id=category_id, order=order,
                      description=description, study_content=study_content,
                      unlock_order=unlock_order, background_image=background_image)
        db.session.add(group)
        db.session.commit()
        flash('分组添加成功')
        return redirect(url_for('admin.admin_groups'))
    categories = Category.query.all()
    return render_template('admin/group_form.html', categories=categories, group=None)

@admin_bp.route('/group/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_group_edit(id):
    group = Group.query.get_or_404(id)
    if request.method == 'POST':
        group.name = request.form['name']
        group.category_id = request.form['category_id']
        group.order = request.form.get('order', 0, type=int)
        group.description = request.form.get('description', '')
        group.study_content = request.form.get('study_content', '')
        group.unlock_order = request.form.get('unlock_order', 0, type=int)
        bg_image = _handle_background_image_upload()
        if bg_image:
            group.background_image = bg_image
        db.session.commit()
        flash('分组更新成功')
        return redirect(url_for('admin.admin_groups'))
    categories = Category.query.all()
    return render_template('admin/group_form.html', categories=categories, group=group)

@admin_bp.route('/group/delete/<int:id>')
@login_required
@admin_required
def admin_group_delete(id):
    group = Group.query.get_or_404(id)
    Question.query.filter_by(group_id=id).update({Question.group_id: None})
    db.session.delete(group)
    db.session.commit()
    flash('分组已删除')
    return redirect(url_for('admin.admin_groups'))

# ==================== 题目管理 ====================
@admin_bp.route('/questions')
@login_required
@admin_required
def admin_questions():
    questions = Question.query.all()
    return render_template('admin/questions.html', questions=questions)

@admin_bp.route('/question/add', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_question_add():
    if request.method == 'POST':
        category_id = request.form['category_id']
        group_id = request.form.get('group_id', type=int) or None
        qtype = request.form['type']
        content = request.form['content']
        options_text = request.form.get('options', '')
        options = [line.strip() for line in options_text.splitlines() if line.strip()] if qtype not in ['judge', 'fill'] else []
        answer = request.form['answer']
        analysis = request.form.get('analysis', '')
        difficulty = request.form.get('difficulty', 1, type=int)
        q = Question(category_id=category_id, group_id=group_id, type=qtype, content=content,
                     options=options, answer=answer, analysis=analysis, difficulty=difficulty)
        db.session.add(q)
        db.session.commit()
        flash('题目添加成功')
        return redirect(url_for('admin.admin_questions'))
    categories = Category.query.all()
    groups = Group.query.all()
    return render_template('admin/question_form.html',
                                  categories=categories, groups=groups, question=None)

@admin_bp.route('/question/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_question_edit(id):
    q = Question.query.get_or_404(id)
    if request.method == 'POST':
        q.category_id = request.form['category_id']
        q.group_id = request.form.get('group_id', type=int) or None
        q.type = request.form['type']
        q.content = request.form['content']
        options_text = request.form.get('options', '')
        q.options = [line.strip() for line in options_text.splitlines() if line.strip()] if q.type not in ['judge', 'fill'] else []
        q.answer = request.form['answer']
        q.analysis = request.form.get('analysis', '')
        q.difficulty = request.form.get('difficulty', 1, type=int)
        db.session.commit()
        flash('题目更新成功')
        return redirect(url_for('admin.admin_questions'))
    categories = Category.query.all()
    groups = Group.query.all()
    return render_template('admin/question_form.html',
                                  categories=categories, groups=groups, question=q)

@admin_bp.route('/question/delete/<int:id>')
@login_required
@admin_required
def admin_question_delete(id):
    q = Question.query.get_or_404(id)
    db.session.delete(q)
    db.session.commit()
    flash('题目已删除')
    return redirect(url_for('admin.admin_questions'))

@admin_bp.route('/questions/bulk_delete', methods=['POST'])
@login_required
@admin_required
def admin_questions_bulk_delete():
    question_ids = request.form.getlist('question_ids')
    if not question_ids:
        flash('请至少选择一道题目')
        return redirect(url_for('admin.admin_questions'))

    ids = [int(qid) for qid in question_ids]
    QuizDetail.query.filter(QuizDetail.question_id.in_(ids)).delete(synchronize_session=False)
    Question.query.filter(Question.id.in_(ids)).delete(synchronize_session=False)
    db.session.commit()

    flash(f'成功删除 {len(ids)} 道题目')
    return redirect(url_for('admin.admin_questions'))

# ==================== 批量导入 ====================
@admin_bp.route('/import', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_import():
    if request.method == 'POST':
        file = request.files['file']
        if file and file.filename.endswith(('.xlsx', '.xls', '.csv')):
            filename = secure_filename(file.filename)
            filepath = os.path.join('uploads', filename)
            file.save(filepath)
            try:
                df = pd.read_excel(filepath) if filepath.endswith(('xlsx','xls')) else pd.read_csv(filepath)
                add_count = 0
                update_count = 0
                for _, row in df.iterrows():
                    cat_name = row['分类名称']
                    category = Category.query.filter_by(name=cat_name).first()
                    if not category:
                        category = Category(name=cat_name)
                        db.session.add(category)
                        db.session.flush()

                    group_name = row.get('分组名称', '')
                    group_id = None
                    if group_name:
                        group = Group.query.filter_by(name=group_name, category_id=category.id).first()
                        if not group:
                            group = Group(name=group_name, category_id=category.id)
                            db.session.add(group)
                            db.session.flush()
                        group_id = group.id

                    qtype = row['题型']
                    if qtype not in ['single', 'multiple', 'judge', 'fill']:
                        flash(f'跳过未知题型：{qtype}')
                        continue

                    opts = row['选项'].split('|') if pd.notna(row.get('选项')) else []
                    answer = row['正确答案']
                    content = row['题干']
                    analysis = row.get('解析', '')
                    difficulty = row.get('难度', 1)

                    existing = Question.query.filter_by(category_id=category.id, content=content).first()
                    if existing:
                        existing.type = qtype
                        existing.options = opts
                        existing.answer = answer
                        existing.analysis = analysis
                        existing.difficulty = difficulty
                        existing.group_id = group_id
                        update_count += 1
                    else:
                        q = Question(
                            category_id=category.id,
                            group_id=group_id,
                            type=qtype,
                            content=content,
                            options=opts,
                            answer=answer,
                            analysis=analysis,
                            difficulty=difficulty
                        )
                        db.session.add(q)
                        add_count += 1

                db.session.commit()
                flash(f'导入完成：新增 {add_count} 道，更新 {update_count} 道')
            except Exception as e:
                db.session.rollback()
                flash(f'导入失败：{str(e)}')
            finally:
                os.remove(filepath)
        else:
            flash('请上传 Excel 或 CSV 文件')
        return redirect(url_for('admin.admin_import'))
    return render_template('admin/import.html')

# ==================== 导出数据 ====================
@admin_bp.route('/export-page')
@login_required
@admin_required
def admin_export_page():
    categories = Category.query.all()
    return render_template('admin/export.html', categories=categories)

@admin_bp.route('/export')
@login_required
@admin_required
def admin_export():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    category_id = request.args.get('category_id', type=int)
    username = request.args.get('username')

    query = QuizRecord.query.join(User).join(Category)
    if start_date:
        query = query.filter(QuizRecord.start_time >= datetime.strptime(start_date, '%Y-%m-%d'))
    if end_date:
        query = query.filter(QuizRecord.start_time <= datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1))
    if category_id:
        query = query.filter(QuizRecord.category_id == category_id)
    if username:
        query = query.filter(User.username.contains(username))

    records = query.all()

    data = []
    for rec in records:
        data.append({
            '用户名': rec.user.username,
            '开始时间': rec.start_time.strftime('%Y-%m-%d %H:%M:%S') if rec.start_time else '',
            '结束时间': rec.end_time.strftime('%Y-%m-%d %H:%M:%S') if rec.end_time else '',
            '分类': rec.category.name,
            '得分': rec.score,
            '正确题数': rec.correct_count,
            '总题数': rec.total_questions,
            '用时 (秒)': (rec.end_time - rec.start_time).total_seconds() if rec.end_time else None
        })

    df = pd.DataFrame(data)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='汇总')
        details_data = []
        for rec in records:
            for det in rec.details:
                details_data.append({
                    '记录 ID': rec.id,
                    '用户名': rec.user.username,
                    '题目': det.question.content,
                    '用户答案': det.user_answer,
                    '正确答案': det.question.answer,
                    '是否正确': det.is_correct,
                    '得分': det.score_earned
                })
        if details_data:
            df_details = pd.DataFrame(details_data)
            df_details.to_excel(writer, index=False, sheet_name='详情')
    output.seek(0)

    return send_file(output, download_name=f'答题记录_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx', as_attachment=True)

# ==================== 用户管理 ====================
@admin_bp.route('/users')
@login_required
@admin_required
def admin_users():
    users = User.query.all()
    return render_template('admin/users.html', users=users)

@admin_bp.route('/user/toggle/<int:id>')
@login_required
@admin_required
def admin_toggle_user(id):
    user = User.query.get_or_404(id)
    if user.id == current_user.id:
        flash('不能禁用自己')
    else:
        user.status = not user.status
        db.session.commit()
        flash(f'用户 {user.username} 状态已切换')
    return redirect(url_for('admin.admin_users'))


@admin_bp.route('/user/clear_history/<int:id>')
@login_required
@admin_required
def admin_clear_user_history(id):
    """清除指定用户的所有答题历史数据"""
    user = User.query.get_or_404(id)
    if user.id == current_user.id:
        flash('不能清除自己的历史数据')
        return redirect(url_for('admin.admin_users'))
    
    # 删除该用户的答题详情
    records = QuizRecord.query.filter_by(user_id=user.id).all()
    record_ids = [r.id for r in records]
    if record_ids:
        QuizDetail.query.filter(QuizDetail.record_id.in_(record_ids)).delete(synchronize_session=False)
        QuizRecord.query.filter_by(user_id=user.id).delete(synchronize_session=False)
    
    # 删除该用户的学习进度
    UserProgress.query.filter_by(user_id=user.id).delete()
    
    db.session.commit()
    flash(f'已清除用户 {user.username} 的所有答题历史数据')
    return redirect(url_for('admin.admin_users'))
