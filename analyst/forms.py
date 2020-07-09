from django import forms


class DcfForm(forms.Form):
    choices = (("AAPL", "AAPL"), ("MSFT", "MSFT"), ("NVDA", "NVDA"),)
    equity = forms.ChoiceField(choices=choices)
    discount_rate = forms.IntegerField(label='Discount Rate')
