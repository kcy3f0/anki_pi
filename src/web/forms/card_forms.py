from flask_wtf import FlaskForm
from wtforms import TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired

class ImportPasteForm(FlaskForm):
    csv_data = TextAreaField('CSV 內容 (格式: front,back)', validators=[DataRequired()])
    card_type = SelectField('卡片類型', choices=[('recognize', '認讀 (Recognize)'), ('spell', '拼寫 (Spell)')])
    deck_id = SelectField('選擇牌組', validators=[DataRequired()])
    submit = SubmitField('開始匯入')
