#!/usr/bin/env python
# -*- coding: utf-8 -*-
from flask.ext.wtf import Form
from wtforms import validators, IntegerField, TextAreaField, BooleanField, SelectField
from flask_wtf.file import FileField, FileRequired, FileAllowed
from flask_user.translations import lazy_gettext as _
from models import MAX_TEXT_LENGTH, Question
import time
from helpers import SpreadSheetReader


class QuestionForm(Form):
    number = IntegerField(
        _('Question number'),
        [validators.NumberRange(min=1, message=_('Question number must be a positive integer'))]
    )
    body = TextAreaField(
        _('Question body'),
        [validators.Length(min=1, max=MAX_TEXT_LENGTH)]
    )
    justification = TextAreaField(
        _('Question justification (optional)'),
        [validators.Length(min=0, max=MAX_TEXT_LENGTH)]
    )
    context = TextAreaField(
        _('Question context (optional)'),
        [validators.Length(min=0, max=MAX_TEXT_LENGTH)]
    )

    def save_question(self, db_session):
        question = Question(
            number=self.number.data,
            body=self.body.data,
            justification=self.justification.data,
            context=self.context.data
        )
        db_session.add(question)
        db_session.commit()


class UploadForm(Form):
    spreadsheet = FileField(
        'spreadsheet',
        validators=[FileRequired(), FileAllowed(['xls', 'xlsx', 'csv'], 'Spreadsheets only (.xsl, .xslx, .csv)')]
    )

    def save_spreadsheet(self):
        original_filename = self.spreadsheet.data.filename
        new_filename = str(int(time.time())) + '.' + original_filename.split('.')[-1]
        self.spreadsheet.data.save('app/uploads/' + new_filename)
        return new_filename


class ProcessSpreadsheetForm(Form):
    discard_first_row = BooleanField(_('First row is header'), [validators.DataRequired()])
    number = SelectField('Question number', [validators.DataRequired()])
    body = SelectField('Question body', [validators.DataRequired()])
    justification = SelectField('Question justification')
    context = SelectField('Question context')
    answerer = SelectField('Question answerer')
    report = SelectField('Report number')
    author = SelectField('Question author')
    topic = SelectField('Question topic')
    subtopic = SelectField('Question subtopic')
    # keywords ?

    def update_choices(self, first_row):
        choices = [(str(i), first_row[i]) for i in range(len(first_row))]
        choices = [('', _('None'))] + choices
        self.number.choices = choices
        self.body.choices = choices
        self.justification.choices = choices
        self.context.choices = choices
        self.answerer.choices = choices
        self.report.choices = choices
        self.author.choices = choices
        self.topic.choices = choices
        self.subtopic.choices = choices

    def save_models(self, filename, db_session):
        columns = self.collect_columns()
        extension = filename.split('.')[-1]
        with open('app/uploads/' + filename, 'rb') as spreadsheet_file:

            if extension == 'csv':
                spreadsheet = SpreadSheetReader.read_csv(spreadsheet_file)

            for i, row in spreadsheet:
                if i == 0 and self.discard_first_row.data:
                    continue
                args = self.collect_args(row, columns)
                question = Question(**args)
                db_session.add(question)
            db_session.commit()
        return

    def collect_columns(self):
        columns = [
            (self.number.data, 'number'),
            (self.body.data, 'body'),
            (self.justification.data, 'justification'),
            (self.context.data, 'context'),
            (self.answerer.data, 'answerer'),
            (self.report.data, 'report'),
            (self.author.data, 'author'),
            (self.topic.data, 'topic'),
            (self.subtopic.data, 'subtopic')
        ]
        return [(int(tuple[0]), tuple[1]) for tuple in columns if len(tuple[0]) > 0]

    @staticmethod
    def collect_args(row, columns):
        d = {}
        for col in columns:
            position = col[0]
            if position < len(row):
                value = row[col[0]].strip()
            else:
                value = ''
            d[col[1]] = value
        return d


class FullTextQueryForm(Form):
    main_text = TextAreaField(
        _('Base text to query'),
        [validators.Length(min=1, max=MAX_TEXT_LENGTH)]
    )
