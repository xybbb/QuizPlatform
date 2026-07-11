#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
答题路由：答题、提交、历史记录
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_required, current_user
from sqlalchemy.orm import joinedload
from datetime import datetime
import os
from models import db, Category, Group, Question, QuizRecord, QuizDetail, UserProgress, User
from utils import check_answer

quiz_bp = Blueprint('quiz', __name__)

TEMPLATES_DIR = 'templates'

@quiz_bp.route('/')
def index():
    categories = Category.query.all()
    # 为每个分类获取用户进度信息
    category_progress = {}
    if current_user.is_authenticated:
        for cat in categories:
            progress = UserProgress.query.filter_by(
                user_id=current_user.id,
                category_id=cat.id
            ).first()
            # 获取该分类下所有需要解锁的题组
            locked_groups = Group.query.filter(
                Group.category_id == cat.id,
                Group.unlock_order > 0
            ).order_by(Group.unlock_order).all()
            
            # 计算已解锁的题组
            if progress and progress.last_completed_group:
                unlocked_order = progress.last_completed_group.unlock_order
            else:
                unlocked_order = 0
            
            total_groups = Group.query.filter_by(category_id=cat.id).count()
            completed_groups = 0
            if progress and progress.last_completed_group:
                completed_groups = Group.query.filter(
                    Group.category_id == cat.id,
                    Group.unlock_order > 0,
                    Group.unlock_order <= progress.last_completed_group.unlock_order
                ).count()
            
            category_progress[cat.id] = {
                'unlocked_order': unlocked_order,
                'total_groups': total_groups,
                'completed_groups': completed_groups
            }
    
    return render_template('index.html', categories=categories, category_progress=category_progress)

@quiz_bp.route('/quiz/<int:category_id>')
@login_required
def start_quiz(category_id):
    category = db.get_or_404(Category, category_id)
    questions = Question.query.filter_by(category_id=category_id).order_by(db.func.random()).limit(10).all()
    if not questions:
        flash('该分类下暂无题目')
        return redirect(url_for('quiz.index'))
    record = QuizRecord(user_id=current_user.id, category_id=category_id, total_questions=len(questions))
    db.session.add(record)
    db.session.commit()
    session['quiz_record_id'] = record.id
    session['question_ids'] = [q.id for q in questions]
    session['current_index'] = 0
    session['answers'] = {}
    session['group_mode'] = False
    return redirect(url_for('quiz.do_quiz'))

@quiz_bp.route('/group_quiz/<int:category_id>')
@login_required
def group_quiz(category_id):
    category = db.get_or_404(Category, category_id)
    db_groups = Group.query.filter_by(category_id=category_id).order_by(Group.order).all()
    if not db_groups:
        flash('该分类下没有分组，请先创建分组')
        return redirect(url_for('quiz.index'))

    group_questions = []
    for g in db_groups:
        qs = Question.query.filter_by(group_id=g.id).all()
        if qs:
            group_questions.append({
                'group_id': g.id,
                'group_name': g.name,
                'category_id': g.category_id,
                'question_ids': [q.id for q in qs]
            })

    if not group_questions:
        flash('所有分组下均无题目')
        return redirect(url_for('quiz.index'))

    progress = UserProgress.query.filter_by(user_id=current_user.id, category_id=category_id).first()
    start_group_index = 0
    if progress and progress.last_completed_group_id:
        for idx, g in enumerate(group_questions):
            if g['group_id'] == progress.last_completed_group_id:
                if idx == len(group_questions) - 1:
                    db.session.delete(progress)
                    db.session.commit()
                    start_group_index = 0
                else:
                    start_group_index = idx + 1
                break
        else:
            db.session.delete(progress)
            db.session.commit()
            start_group_index = 0

    current_group_question_count = len(group_questions[start_group_index]['question_ids'])
    record = QuizRecord(user_id=current_user.id, category_id=category_id, total_questions=current_group_question_count)
    db.session.add(record)
    db.session.commit()

    session['quiz_record_id'] = record.id
    session['group_mode'] = True
    session['groups'] = group_questions
    session['current_group'] = start_group_index
    session['group_question_ids'] = group_questions[start_group_index]['question_ids']
    session['current_index'] = 0
    session['answers'] = {}
    session.modified = True

    if start_group_index > 0:
        flash(f'欢迎回来，您将从分组"{group_questions[start_group_index]["group_name"]}"开始答题。', 'info')

    return redirect(url_for('quiz.do_quiz'))

@quiz_bp.route('/do_quiz', methods=['GET', 'POST'])
@login_required
def do_quiz():
    if 'question_ids' not in session and 'group_question_ids' not in session:
        return redirect(url_for('quiz.index'))

    group_mode = session.get('group_mode', False)

    if group_mode:
        question_ids = session['group_question_ids']
        current_group = session['current_group']
        groups = session['groups']
        group_name = groups[current_group]['group_name']
        current_group_id = groups[current_group]['group_id']
        current_group_obj = db.session.get(Group, current_group_id)
        group_background_image = current_group_obj.background_image if current_group_obj else None
        group_category_id = groups[current_group]['category_id']
    else:
        question_ids = session['question_ids']
        group_name = None
        group_background_image = None
        group_category_id = None

    total = len(question_ids)
    current_index = session['current_index']

    if request.method == 'POST':
        qid = request.form['question_id']
        qtype = request.form['type']
        if qtype == 'multiple':
            answer = request.form.getlist('answer')
        else:
            answer = request.form.get('answer')
        session['answers'][qid] = answer
        session.modified = True

        action = request.form.get('action')

        if action == 'next' and current_index < total - 1:
            session['current_index'] += 1
        elif action == 'prev' and current_index > 0:
            session['current_index'] -= 1
        elif action == 'submit':
            if group_mode:
                return redirect(url_for('quiz.finish_group'))
            else:
                return redirect(url_for('quiz.submit_quiz'))

        return redirect(url_for('quiz.do_quiz'))

    current_qid = question_ids[current_index]
    question = db.session.get(Question, current_qid)
    saved_answer = session['answers'].get(str(current_qid))

    return render_template(
        'quiz.html',
        question=question,
        index=current_index,
        total=total,
        saved_answer=saved_answer,
        group_mode=group_mode,
        group_name=group_name if group_mode else None,
        group_background_image=group_background_image,
        group_category_id=group_category_id
    )

@quiz_bp.route('/finish_group')
@login_required
def finish_group():
    if not session.get('group_mode'):
        return redirect(url_for('quiz.index'))

    groups = session['groups']
    current_group = session['current_group']
    question_ids = groups[current_group]['question_ids']
    group_info = groups[current_group]

    # 判断本组是否全对
    all_correct = True
    for qid in question_ids:
        qid_str = str(qid)
        if qid_str not in session['answers']:
            all_correct = False
            break
        question = db.session.get(Question, qid)
        if not question:
            all_correct = False
            break
        user_answer = session['answers'][qid_str]
        if not check_answer(question, user_answer):
            all_correct = False
            break

    # 复用预创建的记录（由 group_quiz/start_group 创建），保留原始开始时间
    old_record_id = session.get('quiz_record_id')
    if old_record_id:
        record = db.session.get(QuizRecord, old_record_id)
        if record and record.end_time is None:
            # 复用此记录，更新必要字段
            record.category_id = group_info['category_id']
            record.total_questions = len(question_ids)
        else:
            # 如果记录不存在或已完成，创建新记录
            record = QuizRecord(
                user_id=current_user.id,
                category_id=group_info['category_id'],
                total_questions=len(question_ids)
            )
            db.session.add(record)
            db.session.commit()
    else:
        # 没有旧记录，创建新记录
        record = QuizRecord(
            user_id=current_user.id,
            category_id=group_info['category_id'],
            total_questions=len(question_ids)
        )
        db.session.add(record)
        db.session.commit()

    # 保存每道题的答题详情
    correct_count = 0
    for qid in question_ids:
        qid_str = str(qid)
        question = db.session.get(Question, qid)
        user_answer = session['answers'].get(qid_str)
        is_correct = check_answer(question, user_answer) if question and user_answer else False
        score_earned = 1 if is_correct else 0
        if is_correct:
            correct_count += 1
        detail = QuizDetail(
            record_id=record.id,
            question_id=qid,
            user_answer=user_answer,
            is_correct=is_correct,
            score_earned=score_earned
        )
        db.session.add(detail)

    record.end_time = datetime.utcnow()
    record.score = correct_count
    record.correct_count = correct_count
    db.session.commit()

    # 全对时解锁下一题组
    if all_correct:
        progress = UserProgress.query.filter_by(
            user_id=current_user.id,
            category_id=group_info['category_id']
        ).first()
        if not progress:
            progress = UserProgress(
                user_id=current_user.id,
                category_id=group_info['category_id']
            )
            db.session.add(progress)
        progress.last_completed_group_id = group_info['group_id']
        db.session.commit()

    # 存储题组结果信息，供结果页面展示
    session['group_result_all_correct'] = all_correct
    session['group_result_name'] = group_info['group_name']

    # 清理 session 中的答题数据
    session.pop('question_ids', None)
    session.pop('group_question_ids', None)
    session.pop('current_index', None)
    session.pop('answers', None)
    session.pop('quiz_record_id', None)
    session.pop('group_mode', None)
    session.pop('groups', None)
    session.pop('current_group', None)
    session.modified = True

    return redirect(url_for('quiz.result', record_id=record.id))

@quiz_bp.route('/submit_quiz')
@login_required
def submit_quiz():
    record_id = session.get('quiz_record_id')
    record = db.session.get(QuizRecord, record_id)
    if not record:
        return redirect(url_for('quiz.index'))

    total_score = 0
    correct_count = 0
    for qid, user_answer in session['answers'].items():
        question = db.session.get(Question, int(qid))
        correct = check_answer(question, user_answer)
        score_earned = 1 if correct else 0
        total_score += score_earned
        if correct:
            correct_count += 1
        detail = QuizDetail(record_id=record_id, question_id=qid,
                            user_answer=user_answer, is_correct=correct,
                            score_earned=score_earned)
        db.session.add(detail)

    record.end_time = datetime.utcnow()
    record.score = total_score
    record.correct_count = correct_count
    db.session.commit()

    session.pop('question_ids', None)
    session.pop('group_question_ids', None)
    session.pop('current_index', None)
    session.pop('answers', None)
    session.pop('quiz_record_id', None)
    session.pop('group_mode', None)
    session.pop('groups', None)
    session.pop('current_group', None)

    return redirect(url_for('quiz.result', record_id=record.id))

@quiz_bp.route('/result/<int:record_id>')
@login_required
def result(record_id):
    record = db.session.get(QuizRecord, record_id,
        options=[joinedload(QuizRecord.details).joinedload(QuizDetail.question),
                 joinedload(QuizRecord.category)])
    if record is None:
        from flask import abort
        abort(404)
    if record.user_id != current_user.id and current_user.role != 'admin':
        flash('无权查看')
        return redirect(url_for('quiz.index'))

    # 从 session 获取题组结果信息（题组模式才有）
    group_all_correct = session.pop('group_result_all_correct', None)
    group_name = session.pop('group_result_name', None)

    # 检查该分类是否有学习路线（题组）
    has_roadmap = False
    if record.category:
        group_count = Group.query.filter_by(category_id=record.category.id).count()
        has_roadmap = group_count > 0

    return render_template(
        'result.html',
        record=record,
        group_all_correct=group_all_correct,
        group_name=group_name,
        has_roadmap=has_roadmap
    )

@quiz_bp.route('/roadmap/<int:category_id>')
@login_required
def roadmap(category_id):
    """图形化题组路线图"""
    category = db.get_or_404(Category, category_id)
    groups = Group.query.filter_by(category_id=category_id).order_by(Group.unlock_order, Group.order).all()
    
    if not groups:
        flash('该分类下没有题组')
        return redirect(url_for('quiz.index'))
    
    progress = UserProgress.query.filter_by(user_id=current_user.id, category_id=category_id).first()
    if progress and progress.last_completed_group:
        unlocked_order = progress.last_completed_group.unlock_order
    else:
        unlocked_order = 0
    
    return render_template('roadmap.html', category=category, groups=groups, unlocked_order=unlocked_order)


@quiz_bp.route('/study/<int:group_id>')
@login_required
def study(group_id):
    """学习资料页面"""
    group = db.get_or_404(Group, group_id)
    category = db.get_or_404(Category, group.category_id)
    
    # 获取该分类的进度
    progress = UserProgress.query.filter_by(user_id=current_user.id, category_id=category.id).first()
    unlocked_order = progress.last_completed_group.unlock_order if (progress and progress.last_completed_group) else 0
    
    # 检查是否有学习内容，或该题组是否已解锁/无需解锁
    if group.unlock_order > 0 and group.unlock_order > unlocked_order + 1:
        flash('请先完成前面的题组')
        return redirect(url_for('quiz.roadmap', category_id=category.id))
    
    return render_template('study.html', group=group, category=category, unlocked_order=unlocked_order)


@quiz_bp.route('/start_group/<int:group_id>')
@login_required
def start_group(group_id):
    """从路线图启动特定题组的答题"""
    group = db.get_or_404(Group, group_id)
    category = db.get_or_404(Category, group.category_id)
    
    progress = UserProgress.query.filter_by(user_id=current_user.id, category_id=category.id).first()
    unlocked_order = progress.last_completed_group.unlock_order if (progress and progress.last_completed_group) else 0
    
    # 检查解锁
    if group.unlock_order > 0 and group.unlock_order > unlocked_order + 1:
        flash('该题组尚未解锁，请先完成前面的题组')
        return redirect(url_for('quiz.roadmap', category_id=category.id))
    
    # 获取该题组的题目
    questions = Question.query.filter_by(group_id=group_id).all()
    if not questions:
        flash('该题组暂无题目')
        return redirect(url_for('quiz.roadmap', category_id=category.id))
    
    # 获取该分类下所有题组，构建完整的 groups session
    all_groups = Group.query.filter_by(category_id=category.id).order_by(Group.unlock_order, Group.order).all()
    
    group_questions = []
    for g in all_groups:
        qs = Question.query.filter_by(group_id=g.id).all()
        if qs:
            group_questions.append({
                'group_id': g.id,
                'group_name': g.name,
                'category_id': g.category_id,
                'question_ids': [q.id for q in qs]
            })
    
    if not group_questions:
        flash('所有分组下均无题目')
        return redirect(url_for('quiz.index'))
    
    # 找到当前 group 在 group_questions 中的索引
    start_group_index = 0
    for idx, gq in enumerate(group_questions):
        if gq['group_id'] == group_id:
            start_group_index = idx
            break
    
    current_group_question_count = len(group_questions[start_group_index]['question_ids'])
    record = QuizRecord(user_id=current_user.id, category_id=category.id, total_questions=current_group_question_count)
    db.session.add(record)
    db.session.commit()
    
    session['quiz_record_id'] = record.id
    session['group_mode'] = True
    session['groups'] = group_questions
    session['current_group'] = start_group_index
    session['group_question_ids'] = group_questions[start_group_index]['question_ids']
    session['current_index'] = 0
    session['answers'] = {}
    session.modified = True
    
    return redirect(url_for('quiz.do_quiz'))


@quiz_bp.route('/history')
@login_required
def history():
    records = QuizRecord.query.filter_by(user_id=current_user.id).order_by(QuizRecord.start_time.desc()).all()
    return render_template('history.html', records=records)


@quiz_bp.route('/leaderboard')
def leaderboard():
    """排行榜：按总分和正确率排名"""
    from sqlalchemy import func
    
    # 获取所有用户的答题统计
    # 按用户汇总：总得分数、总题目数、总正确数
    stats = db.session.query(
        User.id,
        User.username,
        func.count(QuizRecord.id).label('total_records'),
        func.coalesce(func.sum(QuizRecord.score), 0).label('total_score'),
        func.coalesce(func.sum(QuizRecord.total_questions), 0).label('total_questions'),
        func.coalesce(func.sum(QuizRecord.correct_count), 0).label('total_correct')
    ).join(QuizRecord, User.id == QuizRecord.user_id, isouter=True
    ).filter((QuizRecord.id == None) | (QuizRecord.end_time != None)
    ).group_by(User.id).order_by(func.sum(QuizRecord.score).desc()).all()
    
    # 计算排名数据
    ranked_users = []
    for idx, row in enumerate(stats):
        if row.total_questions > 0:
            accuracy = round(row.total_correct / row.total_questions * 100, 1)
        else:
            accuracy = 0.0
        
        ranked_users.append({
            'rank': idx + 1,
            'user_id': row.id,
            'username': row.username,
            'total_records': row.total_records,
            'total_score': int(row.total_score),
            'total_questions': int(row.total_questions),
            'total_correct': int(row.total_correct),
            'accuracy': accuracy
        })
    
    return render_template('leaderboard.html', ranked_users=ranked_users)
