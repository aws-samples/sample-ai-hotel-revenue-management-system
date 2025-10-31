from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, FloatField, BooleanField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Optional, NumberRange

class NaturalLanguageForm(FlaskForm):
    """Form for natural language queries"""
    query = TextAreaField('Enter your query', validators=[DataRequired()], 
                         render_kw={"placeholder": "Example: Optimize pricing for a 4-star hotel in Miami during summer season", "rows": 3})
    submit = SubmitField('Submit Query')

class StructuredForm(FlaskForm):
    """Structured form for hotel revenue optimization"""
    hotel_name = StringField('Hotel Name', validators=[DataRequired()],
                           render_kw={"placeholder": "Enter hotel name"})
    
    hotel_type = SelectField('Hotel Type', 
                           choices=[
                               ('', 'Select hotel type...'),
                               ('luxury', 'Luxury Hotel'),
                               ('business', 'Business Hotel'),
                               ('resort', 'Resort'),
                               ('boutique', 'Boutique Hotel'),
                               ('budget', 'Budget Hotel')
                           ],
                           validators=[DataRequired()])
    
    location = StringField('Location', validators=[DataRequired()],
                         render_kw={"placeholder": "City, State or Region"})
    
    season = SelectField('Season',
                       choices=[
                           ('', 'Select season...'),
                           ('high', 'High Season'),
                           ('shoulder', 'Shoulder Season'),
                           ('low', 'Low Season')
                       ],
                       validators=[DataRequired()])
    
    star_rating = SelectField('Star Rating',
                            choices=[
                                ('', 'Select star rating...'),
                                ('3', '3 Stars'),
                                ('4', '4 Stars'),
                                ('5', '5 Stars')
                            ],
                            validators=[DataRequired()])
    
    occupancy_rate = FloatField('Current Occupancy Rate (%)', 
                              validators=[DataRequired(), NumberRange(min=0, max=100)],
                              render_kw={"placeholder": "e.g., 75.5"})
    
    competitor_analysis = BooleanField('Include Competitor Analysis', default=True)
    
    optimization_goal = SelectField('Optimization Goal',
                                  choices=[
                                      ('', 'Select optimization goal...'),
                                      ('maximize_revenue', 'Maximize Total Revenue'),
                                      ('maximize_occupancy', 'Maximize Occupancy Rate'),
                                      ('maximize_profit', 'Maximize Profit Margin'),
                                      ('balance', 'Balance Revenue and Occupancy')
                                  ],
                                  validators=[DataRequired()])
    
    submit = SubmitField('Generate Recommendations')
